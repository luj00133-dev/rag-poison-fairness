# Data

## BBQ (used in §5.4 of Paper A, §5 of Paper B)

Source: the official repository of *BBQ: A Hand-Built Bias Benchmark for Question
Answering* (Parrish et al., Findings of ACL 2022).

https://github.com/nyu-mll/BBQ/tree/main/data

Download the four categories used here (about 15 MB total):

```bash
mkdir -p data/bbq
base=https://raw.githubusercontent.com/nyu-mll/BBQ/main/data
for f in Gender_identity Disability_status Age Race_ethnicity; do
  curl -sSL "$base/$f.jsonl" -o "data/bbq/$f.jsonl"
done
```

On Windows PowerShell:

```powershell
$dir = 'data\bbq'; New-Item -ItemType Directory -Force -Path $dir | Out-Null
$base = 'https://raw.githubusercontent.com/nyu-mll/BBQ/main/data'
foreach ($f in 'Gender_identity','Disability_status','Age','Race_ethnicity') {
  Invoke-WebRequest -Uri "$base/$f.jsonl" -OutFile "$dir\$f.jsonl" -UseBasicParsing
}
```

Then build and inspect the corpus:

```bash
python -m src.data.bbq_loader
```

Expected: 17,792 passages, 144 group-neutral queries, four strata. Stance
labels are **derived from BBQ's own annotations** (`stereotyped_groups` +
`question_polarity`), so no new annotation is introduced — see the module
docstring in `src/data/bbq_loader.py` for the exact rule.

### Two properties of BBQ worth knowing

1. **Group imbalance in the race category.** Our build yields 960 passages about
   the protected group versus 88 about the non-protected group. This is a
   property of the benchmark, not of the loader, and it affects any per-group
   metric computed on that stratum.
2. **Pre-existing stance imbalance.** On BBQ the *clean* retrieval already has a
   cross-group stance gap of 0.9326 (dense) / 1.0000 (BM25), because BBQ's
   contexts express stereotyped views by construction. The absolute value of
   `stance_gap` is therefore uninformative on this corpus; use the **change**
   from the clean baseline, as the papers do.

## Controlled corpus (used in §5.1–§5.3 of Paper A)

No download. Generated deterministically from a fixed seed by
`src/data/corpus.py`, using stereotype/anti-stereotype template inventories in
the style of BBQ/StereoSet. Its purpose is to provide an **exactly known clean
reference** for both R1 and R2, which no public benchmark provides. Its passages
are template-instantiated, which is the threat to external validity that §5.4
addresses.

## Not used, and why

NQ and MS MARCO are the standard neutral retrieval corpora, but neither carries
group labels (needed for R1) or stance labels (needed for R2), and stance toward
a social group is not a property a neutral passage expresses. Substituting one
would require annotating it — and any defense in this family faces the same
requirement, since an R1-constraining defense needs the same group labels. See
Limitations §1 of Paper A.
