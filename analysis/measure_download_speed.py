"""Measure raw download throughput from each model host before choosing one.

Three attempts to fetch a 14.5 GB checkpoint stalled at zero bytes, from two
different hosts (hf-mirror.com and modelscope.cn). Retrying blind is the wrong
move; this measures what each host actually delivers by streaming a bounded
number of bytes from a real model file and reporting the rate.

If every host crawls, the conclusion is that a 7B checkpoint is not obtainable
from this network, and the right response is a smaller model rather than a fourth
retry.
"""
import time
import urllib.error
import urllib.request

#: real large files, with a Range request for the first chunk only
TARGETS = [
    ('hf-mirror  mistral shard1',
     'https://hf-mirror.com/mistralai/Mistral-7B-Instruct-v0.3/resolve/main/model-00001-of-00003.safetensors'),
    ('hf-mirror  phi3.5 mini',
     'https://hf-mirror.com/microsoft/Phi-3.5-mini-instruct/resolve/main/model-00001-of-00002.safetensors'),
    ('modelscope  mistral shard1',
     'https://modelscope.cn/api/v1/models/LLM-Research/Mistral-7B-Instruct-v0.3/repo?Revision=master&FilePath=model-00001-of-00003.safetensors'),
    ('modelscope  phi3.5 mini',
     'https://modelscope.cn/api/v1/models/LLM-Research/Phi-3.5-mini-instruct/repo?Revision=master&FilePath=model-00001-of-00002.safetensors'),
    ('hf-mirror  tiny sanity',
     'https://hf-mirror.com/Qwen/Qwen2.5-0.5B-Instruct/resolve/main/model.safetensors'),
]

CHUNK = 8 * 1024 * 1024   # 8 MB is plenty to estimate a rate
SECONDS = 25


def measure(label, url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0', 'Range': 'bytes=0-%d' % (CHUNK - 1)})
    t0 = time.time()
    got = 0
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            while got < CHUNK:
                buf = r.read(65536)
                if not buf:
                    break
                got += len(buf)
                if time.time() - t0 > SECONDS:
                    break
    except urllib.error.HTTPError as exc:
        print('%-28s HTTP %s' % (label, exc.code))
        return None
    except Exception as exc:
        print('%-28s %s: %s' % (label, type(exc).__name__, str(exc)[:60]))
        return None
    dt = max(time.time() - t0, 1e-6)
    rate = got / dt / 1e6
    print('%-28s %7.2f MB in %5.1fs  = %6.2f MB/s' % (label, got / 1e6, dt, rate))
    return rate


if __name__ == '__main__':
    rates = []
    for label, url in TARGETS:
        r = measure(label, url)
        if r:
            rates.append((label, r))
    print()
    if not rates:
        print('no host delivered data at all')
    else:
        best = max(rates, key=lambda kv: kv[1])
        print('best host: %s at %.2f MB/s' % best)
        for gb, what in ((14.5, 'Mistral-7B'), (7.7, 'Phi-3.5-mini')):
            print('   %-14s %.1f GB would take %.1f min at that rate'
                  % (what, gb, gb * 1000 / best[1] / 60))
