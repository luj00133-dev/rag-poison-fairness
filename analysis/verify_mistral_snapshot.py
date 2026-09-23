"""Verify the Mistral snapshot file by file against the index.

The download left four large blobs totalling ~11 GB but the snapshot has none of
the safetensors linked, and `snapshot_download(local_files_only=True)` reports
four missing files. Downloading blind again risks the same outcome, so this checks
what the model index actually requires, what size each shard should be, and which
blobs on disk match -- which distinguishes "still downloading" from "corrupt cache
that must be removed".
"""
import json
import os
import glob

HF = os.environ.get('HF_HOME', r'D:\HaizeiwangPingshu\models\huggingface')
HUB = os.path.join(HF, 'hub', 'models--mistralai--Mistral-7B-Instruct-v0.3')

print('cache root:', HUB)
print('exists    :', os.path.isdir(HUB))
if not os.path.isdir(HUB):
    raise SystemExit(0)

snaps = glob.glob(os.path.join(HUB, 'snapshots', '*'))
print('snapshot(s):', [os.path.basename(s) for s in snaps])
if not snaps:
    raise SystemExit(0)

snap = snaps[0]
idx_path = os.path.join(snap, 'model.safetensors.index.json')
if not os.path.isfile(idx_path):
    print('index json missing')
    raise SystemExit(0)

idx = json.load(open(idx_path, encoding='utf-8'))
weight_map = idx.get('weight_map', {})
want = sorted(set(weight_map.values()))
total = idx.get('metadata', {}).get('total_size')
print('index requires %d shard(s), total_size=%s (%.2f GB)'
      % (len(want), total, (total or 0) / 1e9))
for w in want:
    p = os.path.join(snap, w)
    ok = os.path.isfile(p)
    print('   %-34s present=%s%s' % (w, ok,
          '' if not ok else '  %.2f GB' % (os.path.getsize(p) / 1e9)))

print()
blobs = os.path.join(HUB, 'blobs')
print('blobs on disk:')
for f in sorted(glob.glob(os.path.join(blobs, '*'))):
    sz = os.path.getsize(f)
    if sz > 1_000_000:
        print('   %-62s %8.2f GB%s'
              % (os.path.basename(f)[:62], sz / 1e9,
                 '  INCOMPLETE' if f.endswith('.incomplete') else ''))
