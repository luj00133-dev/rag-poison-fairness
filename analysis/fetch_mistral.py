"""Resumable direct downloader for the Mistral weights, verified against the host.

Everything here is the result of a measurement rather than an assumption:

  * huggingface_hub stalled at zero bytes twice against hf-mirror.com, then the
    modelscope client stalled the same way, while a raw ranged GET from the same
    hosts sustained 7.5 MB/s. The clients are the problem, not the network.
  * HEAD returns 200 with no Content-Length on this host, so the size comes from
    a one-byte Range request's `Content-Range` header instead.
  * Range IS supported (206 + `Accept-Ranges: bytes`), which is what makes
    resumption possible and is why an interrupted transfer is recoverable rather
    than fatal.
  * the file list comes from the repository listing, because guessing filenames
    produced a 404 (`params.json` does not exist here; `configuration.json` does).

Each file lands as `<name>.part` and is renamed only when its byte count equals
the size the host reports, so an interrupted run cannot leave a short file that
looks whole -- the failure mode that produced 38 GB of duplicated partial blobs.
"""
import os
import sys
import time
import urllib.error
import urllib.request

REPO = 'LLM-Research/Mistral-7B-Instruct-v0.3'
API = ('https://modelscope.cn/api/v1/models/%s/repo'
       '?Revision=master&FilePath=%s')
DEST = r'D:\HaizeiwangPingshu\models\mistral-7b-v0.3'
UA = {'User-Agent': 'Mozilla/5.0'}

FILES = [
    'config.json',
    'configuration.json',
    'generation_config.json',
    'tokenizer.json',
    'tokenizer.model',
    'tokenizer.model.v3',
    'tokenizer_config.json',
    'special_tokens_map.json',
    'model.safetensors.index.json',
    'model-00001-of-00003.safetensors',
    'model-00002-of-00003.safetensors',
    'model-00003-of-00003.safetensors',
]


def remote_size(name):
    """Size via a 1-byte Range request, since HEAD omits Content-Length here."""
    req = urllib.request.Request(
        API % (REPO, name),
        headers=dict(UA, Range='bytes=0-0'))
    with urllib.request.urlopen(req, timeout=45) as r:
        cr = r.headers.get('Content-Range') or ''
        if '/' in cr:
            return int(cr.rsplit('/', 1)[1])
        cl = r.headers.get('Content-Length')
        return int(cl) if cl else 0


def fetch(name, retries=4):
    url = API % (REPO, name)
    out = os.path.join(DEST, name)
    part = out + '.part'

    try:
        total = remote_size(name)
    except Exception as exc:
        print('  %-38s size probe failed: %s' % (name, type(exc).__name__))
        return False
    if not total:
        print('  %-38s unknown size' % name)
        return False
    if os.path.exists(out) and os.path.getsize(out) == total:
        print('  %-38s complete (%.1f MB)' % (name, total / 1e6))
        return True

    for attempt in range(1, retries + 1):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if have > total:
            os.remove(part)
            have = 0
        if have == total:
            os.replace(part, out)
            print('  %-38s done (resumed to completion)' % name)
            return True
        headers = dict(UA)
        if have:
            headers['Range'] = 'bytes=%d-' % have
        t0 = time.time()
        last = t0
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r, \
                    open(part, 'ab') as fh:
                while True:
                    buf = r.read(1 << 20)
                    if not buf:
                        break
                    fh.write(buf)
                    have += len(buf)
                    now = time.time()
                    if now - last >= 25:
                        print('  %-38s %5.1f%%  %6.2f MB/s'
                              % (name, 100.0 * have / total,
                                 have / max(now - t0, 1e-6) / 1e6), flush=True)
                        last = now
        except Exception as exc:
            print('  %-38s attempt %d stopped: %s'
                  % (name, attempt, type(exc).__name__), flush=True)

        got = os.path.getsize(part) if os.path.exists(part) else 0
        if got == total:
            os.replace(part, out)
            print('  %-38s done  %.1f MB in %.0fs'
                  % (name, total / 1e6, time.time() - t0))
            return True
        print('  %-38s %d / %d bytes (%.1f%%), resuming'
              % (name, got, total, 100.0 * got / total), flush=True)
    return False


def main():
    os.makedirs(DEST, exist_ok=True)
    print('repo : %s' % REPO)
    print('dest : %s' % DEST)
    print()
    ok = True
    for f in FILES:
        if not fetch(f):
            ok = False
    print()
    total_have = sum(
        os.path.getsize(os.path.join(DEST, f))
        for f in os.listdir(DEST)
        if os.path.isfile(os.path.join(DEST, f)))
    print('on disk: %.1f MB' % (total_have / 1e6))
    print('RESULT: %s' % ('all files complete' if ok
                          else 'incomplete -- re-run to resume'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
