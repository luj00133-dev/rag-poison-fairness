Correction: the machine has a GPU, and the balanced-and-partial regime does not survive scaling

TWO CORRECTIONS, ONE OF THEM MINE

The machine has an NVIDIA RTX 5060 (8 GB, compute capability 12.0, driver 595.71, CUDA 13.2).
An earlier conclusion in this project stated that local generation is impossible here because
the environment is CPU-only. That was wrong, and the error is worth naming precisely: I checked
`torch.cuda.is_available()`, got False, and reported "no CUDA" as though it were a fact about the
hardware. It was a fact about the torch build -- 2.14.0+cpu, with `torch.version.cuda = None`.
The hardware was there the whole time. That mistake sent the work down the paid-API route and,
worse, it was used to justify stopping the scaled run as infeasible.

Fixed by installing the CUDA build, bypassing two obstacles worth recording: the pip config
carries `extra-index-url = mirrors.aliyun.com`, which overrode `--index-url` and silently served
a 124 MB CPU wheel when a 2.7 GB CUDA wheel was requested; and PyTorch's own index had to be
queried directly to discover which builds exist. Now:

    torch 2.9.1+cu128   cuda 12.8   available True
    device NVIDIA GeForce RTX 5060   capability (12, 0)   sm_120 present in the arch list
    4000x4000 matmul on CUDA: 0.20 s (confirms sm_120 kernels actually execute)
    gte-base encodes 256 texts in 0.41 s on CUDA

THE SCALED RUN, NOW FEASIBLE, AND WHAT IT SHOWED

With CUDA the 1,536-query retrieval that had been stopped at 18,117 s CPU and unfinished
completed in 474 s -- roughly a 38x speedup. The label regime at that scale:

    share=0.0   n=768   drift mean=0.0000   BALANCED
    share=1.0   n=768   drift mean=0.1250
    attacked=1536   partial=0   BALANCED+PARTIAL=0

So the balanced-and-partial regime does NOT survive scaling: it went from 36 queries in the
192-query run to zero in the 1,536-query run.

WHY, AND WHY THIS IS A RESULT RATHER THAN A FAILURE

The corpus supplies exactly four query templates per stratum. Raising the query count therefore
does not add independent queries -- it repeats the same four texts more times, and each repeat
sees the identical retrieval outcome. The 36 balanced-and-partial queries in the 192-query run
were those four templates happening to land on the retrieval boundary at low replication. That
landing is not a stable property of the construction; it was a small-sample coincidence.

This is the honest bottom line of the whole line of work: the prospective validation cannot be
powered on this corpus, and the obstacle is the corpus, not the attack construction, not the
statistics, and not the hardware. Four fixed query texts per stratum cannot supply the
independent batches that a batch-level statistic needs, however many times they are repeated.

WHAT THE GPU DOES CHANGE

Two things, and they are real:

  * retrieval is no longer a constraint, so any future design can be evaluated at full scale
    instead of on a 192-query sample -- which is exactly how the coincidence above was exposed;
  * local generation is now possible. LocalGenerator._ensure requires CUDA, which is now
    satisfied, so the Mistral-7B panel can run locally and the paid API is no longer the only
    route. That reverses the earlier claim and makes repeated generation sampling cheap.

Neither fixes the corpus limit, which is the one that actually binds.
