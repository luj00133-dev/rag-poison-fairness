Retrieval cost scales super-linearly with query count, which changes the plan

The scaled run was meant to reach ~1,500 attacked queries by raising n_queries_per_stratum from
48 to 384. It was stopped after 18,117 seconds of CPU with no output written.

WHY IT WAS STOPPED

The st retriever does a full query-by-document similarity computation, so the cost grows with
the number of queries times the number of documents, and the per-stratum work grows with the
query count in more than one place. The observed evidence:

    run            queries   conditions   wall time
    pv_validate        192            2    1,096 s
    pv_scale         1,536            2   stopped at 18,117 s CPU, unfinished

Eight times the queries, and after sixteen times the wall time of the smaller run it had not
finished. Extrapolating from that ratio is unreliable in the exact figure but unambiguous in
direction: the full run was not going to complete on a useful timescale on this CPU, and waiting
without a bound was the wrong call. Stopped rather than left running.

This is a correction to the estimate given before it was launched, which assumed roughly linear
scaling and predicted about an hour.

WHAT THIS DOES NOT INVALIDATE

Nothing already established. The balanced-and-partial regime was measured at 192 queries:
graded injection, align_strength 0.25, st retriever, lexical attack, giving 36
balanced-and-partial queries at drift exactly 0.0000. That measurement stands, as does the sweep
showing the window is narrow (0.10 and 0.05 collapse, projection cannot be graded at all), and
the replica-level validation showing the aggregate gap moving significantly while both group
rates carry bootstrap intervals that include zero.

WHAT THE POWER LIMIT ACTUALLY IS, AND THE CHEAPER WAY TO ATTACK IT

The limiting factor is not the number of attacked queries but the number of INDEPENDENT units
entering a batch average. Two things were being conflated:

  * raising n_queries_per_stratum repeats the three query templates per stratum, so most added
    queries are repeat trials of the same query text. They sharpen the estimate of the
    retrieval probability for that text, but they add little independent information about
    how a group's favourable rate responds.

  * the group favourable rate is an average over a batch, so its standard error falls with the
    number of independent batches, and the corpus supplies four strata.

Because the queries are cheap to answer from a FIXED retrieved context, whereas retrieval is
expensive, the efficient move is not more retrieval. It is more independent generation samples
per existing balanced-and-partial query: the context is already materialised for those 36
queries, and repeated answers to the same context with temperature above zero give independent
draws of the generator's behaviour, which is the quantity the batch average estimates. That
raises the precision of each cell's rate without any retrieval at all.

The remaining honest caveat, which must travel with any result from that route: repeated answers
to one context are independent draws of the GENERATOR, not of the retrieval event, so they
sharpen the answer-level estimate while leaving the retrieval-level uncertainty untouched. A
claim that needs both would still need either more strata or repeated audits over time, which
this corpus cannot supply.
