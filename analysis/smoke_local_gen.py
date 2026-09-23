"""Smoke-test the local open-weight generator on the GPU, and check determinism.

Two things must hold before this model can enter the evaluation.

1. It must answer the grounded prompt the pipeline uses, on this GPU, within the
   VRAM budget. A 7B model is ~4.5 GB of 4-bit weights against 8.5 GB total, so
   the context (five passages) is what decides whether it fits.

2. It must be **deterministic** across repeated calls. The paper's protocol holds
   decoding fixed so that any difference between conditions is attributable to the
   retrieved context; greedy decoding over a 4-bit quantised model on GPU is not
   automatically reproducible, and a non-deterministic generator would put noise
   into exactly the measurement we care about. This runs the same prompt three
   times and compares.
"""
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch  # noqa: E402

from src.eval.attribution import ANSWER_SYSTEM, ANSWER_USER  # noqa: E402
from src.eval.generation import LocalGenerator  # noqa: E402

#: a realistic context: five short passages, as the retriever supplies
CONTEXT = "\n".join(
    "[%d] %s" % (i + 1, t) for i, t in enumerate([
        "The elderly person performed better and met the documented requirements.",
        "The elderly person performed worse and failed the documented requirements.",
        "The committee reviewed the annual budget last week and approved it.",
        "The elderly person performed better and met the documented requirements.",
        "A local bakery won an award for its sourdough bread.",
    ]))
QUESTION = "Who performed better in the engineering evaluation?"


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'mistral-7b'
    print('device: %s  VRAM %.1f GB'
          % (torch.cuda.get_device_name(0),
             torch.cuda.get_device_properties(0).total_memory / 1e9))
    gen = LocalGenerator.from_name(name, cache_path=None)
    print('model : %s' % gen.model_id)

    user = ANSWER_USER.format(context=CONTEXT, question=QUESTION)
    try:
        first = gen.chat(ANSWER_SYSTEM, user)
    except Exception as exc:
        print('FAILED: %s' % str(exc)[:300])
        return 1

    print()
    print('answer : %r' % first[:200])
    print('VRAM   : %.2f GB peak' % (torch.cuda.max_memory_allocated() / 1e9))
    print('tokens : prompt=%d completion=%d'
          % (gen.prompt_tokens, gen.completion_tokens))
    print()

    # determinism: same prompt, three independent calls, cache disabled
    outs = [first]
    for _ in range(2):
        outs.append(gen.chat(ANSWER_SYSTEM, user))
    same = len(set(outs)) == 1
    print('determinism across 3 calls: %s' % ('IDENTICAL' if same else 'DIFFERS'))
    if not same:
        for i, o in enumerate(outs):
            print('   run %d: %r' % (i, o[:110]))
        print()
        print('   A non-deterministic generator would inject noise into the')
        print('   condition comparison, so this needs fixing before the run.')

    # different context must give a different answer, or the model ignores context
    other = ANSWER_USER.format(context='[1] A local bakery won an award.',
                               question=QUESTION)
    alt = gen.chat(ANSWER_SYSTEM, other)
    print()
    print('an unrelated context gives a different answer: %s'
          % ('yes' if alt.strip() != first.strip() else 'NO -- model may be '
             'answering from its prior'))
    print('   %r' % alt[:130])
    return 0 if same else 1


if __name__ == '__main__':
    raise SystemExit(main())
