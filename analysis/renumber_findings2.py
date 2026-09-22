"""Final renumber: the encoder-scale finding takes 11, leaving the
generation-stage findings at 8/9/10 in document order."""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

old = '**Finding 10. Text-attack susceptibility is a per-checkpoint property'
new = '**Finding 11. Text-attack susceptibility is a per-checkpoint property'
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# the contributions list points at the scale finding by number
old_c = ('contribution 6 and is itself the sharper result (\u00a75.6)')
if old_c in s:
    print('contributions text does not cite the number; no change needed')

io.open(P, 'w', encoding='utf-8').write(s)

print('Finding labels in document order:',
      re.findall(r'\*\*Finding (\d+[a-z]?)\.', s))
print()
print('duplicate check:', end=' ')
nums = re.findall(r'\*\*Finding (\d+[a-z]?)\.', s)
dupes = [n for n in set(nums) if nums.count(n) > 1]
print(dupes if dupes else 'none')
