"""List what files a ModelScope repo actually contains.

The direct downloader guessed filenames and got a 404, which is a signal to ask
the API rather than guess again. ModelScope exposes a file listing endpoint; this
prints it so the download list can be built from reality.
"""
import json
import urllib.request

REPOS = [
    'LLM-Research/Mistral-7B-Instruct-v0.3',
    'LLM-Research/Phi-3.5-mini-instruct',
]
ENDPOINTS = [
    'https://modelscope.cn/api/v1/models/%s/repo/files?Revision=master&Recursive=true',
    'https://modelscope.cn/api/v1/models/%s/repo/tree?Revision=master&Recursive=true',
]

for repo in REPOS:
    print('=== %s ===' % repo)
    for tpl in ENDPOINTS:
        url = tpl % repo
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as exc:
            print('   %-58s %s' % (tpl.split('/')[-1][:56],
                                   type(exc).__name__))
            continue
        files = (data.get('Data') or {}).get('Files') or []
        if not files:
            print('   %-58s no Files key (keys=%s)'
                  % (tpl.split('/')[-1][:56], list(data.keys())[:6]))
            continue
        print('   endpoint: %s' % tpl.split('/')[-1].split('?')[0])
        for f in files:
            sz = f.get('Size') or 0
            print('     %-46s %10s' % (f.get('Path'),
                                       '%.1f MB' % (sz / 1e6) if sz else '-'))
        break
    print()
