"""Verify 4-bit quantisation works on the RTX 5060 before downloading a 7B model.

8 GB of VRAM runs a 7B model only in 4-bit (~4.5 GB of weights). bitsandbytes
kernel support for Blackwell (sm_120) is the open question, and it is worth
answering with a small model first: a failed 4-bit path after a 15 GB download is
a worse afternoon than a failed one after a 0.5 GB download.

Checks, in order:
  1. can transformers load a model in 4-bit at all on this device;
  2. does a forward pass produce finite logits;
  3. how much VRAM does it actually take.

Falls back to reporting float16 feasibility if 4-bit is unavailable.
"""
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

SMALL = 'Qwen/Qwen2.5-0.5B-Instruct'


def vram():
    return torch.cuda.max_memory_allocated() / 1e9


def try_4bit():
    from transformers import BitsAndBytesConfig
    qc = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    tok = AutoTokenizer.from_pretrained(SMALL)
    model = AutoModelForCausalLM.from_pretrained(
        SMALL, quantization_config=qc, device_map='cuda')
    ids = tok('Say OK.', return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = model(**ids)
    logits = out.logits
    finite = bool(torch.isfinite(logits).all())
    print('4-bit load        : OK')
    print('forward pass      : %s, finite=%s' % (tuple(logits.shape), finite))
    print('VRAM after forward: %.2f GB' % vram())
    with torch.no_grad():
        gen = model.generate(**ids, max_new_tokens=8, do_sample=False)
    text = tok.decode(gen[0][ids['input_ids'].shape[1]:],
                      skip_special_tokens=True)
    print('greedy generation : %r' % text[:60])
    return True


def try_fp16():
    tok = AutoTokenizer.from_pretrained(SMALL)
    model = AutoModelForCausalLM.from_pretrained(
        SMALL, torch_dtype=torch.float16, device_map='cuda')
    ids = tok('Say OK.', return_tensors='pt').to('cuda')
    with torch.no_grad():
        out = model(**ids)
    print('fp16 load         : OK, finite=%s'
          % bool(torch.isfinite(out.logits).all()))
    print('VRAM              : %.2f GB' % vram())
    return True


if __name__ == '__main__':
    print('device: %s  capability %s  VRAM %.1f GB'
          % (torch.cuda.get_device_name(0),
             torch.cuda.get_device_capability(0),
             torch.cuda.get_device_properties(0).total_memory / 1e9))
    print()
    try:
        try_4bit()
        print('\nRESULT: 4-bit path works -- a 7B model is feasible here')
    except Exception as exc:
        print('4-bit FAILED: %s: %s' % (type(exc).__name__, str(exc)[:200]))
        print()
        try:
            try_fp16()
            print('\nRESULT: fp16 works but 4-bit does not')
        except Exception as exc2:
            print('fp16 also FAILED: %s: %s'
                  % (type(exc2).__name__, str(exc2)[:200]))
            print('\nRESULT: GPU unusable for generation')
