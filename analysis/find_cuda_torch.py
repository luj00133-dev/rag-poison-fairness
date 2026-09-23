"""Find which torch builds with CUDA 12.8 support this machine can install.

The RTX 5060 is Blackwell (compute capability 12.0 / sm_120), which needs a
CUDA 12.8 build of torch. The configured pip mirrors (Tsinghua, Aliyun PyPI) carry
only CPU wheels, so a CUDA build has to come from one of the PyTorch wheel indexes
or their mirrors. This checks what each actually offers for cp312 on Windows
rather than assuming a version exists.

Prints the newest few candidates per index so the install command can be pinned to
something that is really there.
"""
import re
import urllib.error
import urllib.request

INDEXES = [
    ('aliyun', 'https://mirrors.aliyun.com/pytorch-wheels/cu128/'),
    ('sjtu', 'https://mirror.sjtu.edu.cn/pytorch-wheels/cu128/'),
    ('official', 'https://download.pytorch.org/whl/cu128/torch/'),
]

PAT = re.compile(r'torch-(2\.\d+\.\d+)(?:\+cu128)?-cp312-cp312-win_amd64\.whl')

for name, url in INDEXES:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'pip/24'})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        print('%-9s HTTP %s' % (name, exc.code))
        continue
    except Exception as exc:
        print('%-9s %s' % (name, type(exc).__name__))
        continue
    vers = sorted(set(PAT.findall(body)), key=lambda v: [int(x) for x in v.split('.')])
    print('%-9s %d build(s): %s' % (name, len(vers), ' '.join(vers[-6:]) or 'none'))
