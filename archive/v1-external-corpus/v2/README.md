# Report v2 — the redaction benchmark, re-graded

Drafted 2026-09-05. The same 203 runs as the v1 report in [`../research/`](../research/),
re-graded against hand-cleaned gold documents with the rubric in
[`../ideas/report-v2-rubric.md`](../ideas/report-v2-rubric.md). No run was added for this
report; the six Opus 5 B8/B9 cells and two B5 reruns from the last sweep were folded in.

> v1 scored redaction by counting marks and fidelity by counting bytes. Both were fooled
> by the same run. v2 grades recall, precision, subject preservation, fidelity and
> fabrication against a hand-cleaned gold document, and classifies every run as Correct,
> Degraded, Silent failure, Loud failure or Format failure. The raw runs are the same;
> the conclusions are re-derived.

| File | Content |
|---|---|
| [00-what-changed.md](00-what-changed.md) | Why v1's metrics were replaced; the v1 → v2 autopsy, cell by cell |
| [01-method.md](01-method.md) | Task, pages, variants (unchanged), the gold documents, rubric v2 |
| [02-scorecard.md](02-scorecard.md) | The outcome-class matrix, then per-axis tables |
| [03-failure-gallery.md](03-failure-gallery.md) | The four v1 failures with the axis that catches each, and two v1 could not see |
| [04-cost-per-correct.md](04-cost-per-correct.md) | Cost, wall and calls conditioned on class |
| [05-flowdrop-findings.md](05-flowdrop-findings.md) | Carried forward from v1, plus what the v2 sweep added |
| [`../data/runs_v2.csv`](../data/runs_v2.csv), [`../data/gold/`](../data/gold/) | The frozen dataset and the gold documents |

Regenerate the numbers: `python3 docs/drupalcon/data/score_v2.py` (about two seconds, no LLM),
tables with `python3 docs/drupalcon/data/tables_v2.py`, a single run's reasoning with
`--explain <run_id-prefix>`.

## The one-sentence finding, restated

> Of 116 graded runs, 86 were correct, 9 degraded and **7 were silent failures: the pipeline
> reported success and the document was wrong.** Six of the seven came from variants that let the
> model decide what to do with the page; the seventh is the deterministic-conversion variant
> B3 truncating on the cheapest model.

## Status

Phase A (rescore) and the fold are done. This folder is Phase C, first draft. The site has three
generated pages, the [Rubric v2 Scorecard](../site/redaction-benchmark/artifacts/rubric-v2-scorecard.html)
(`data/build_site_v2.py`), the [Redactor Model Matrix v2](../site/redaction-benchmark/artifacts/redactor-model-matrix-v2.html)
(`data/build_matrix_v2.py`) and the [Redaction Benchmark Plots v2](../site/redaction-benchmark/artifacts/redaction-benchmark-plots-v2.html)
(`data/build_plots_v2.py`, one model at a time); the nine v1 pages moved to `site/redaction-benchmark/archive/v1/`
with redirects at their old URLs. Not done:
the by-eye read of the gold bodies against the live pages; the talk outline and decks still cite
v1 numbers; most cells are one draw.
