> **Archived 2026-09-06. Not comparable with current results.** Every figure in this folder
> came from runs against three live third-party web pages (drupal.org, ibm.com, Wikipedia)
> that we had no consent to fetch or republish. The fetched text, the 163 output documents
> and the hand-cleaned gold bodies were removed on that date; the run
> ledgers (`data/runs.csv`, `data/runs_v2.csv`), the scoring code and the research prose are
> kept as a record of the method. The benchmark continues on a corpus we own, with the
> figures reset, at <https://github.com/d34dman/flowdrop-ai-bench>
> (results: <https://d34dman.github.io/flowdrop-ai-bench/>). Scripts here that read
> `outputs/` or `gold/*.md` no longer run.

# DrupalCon Rotterdam 2026 — talk research

Working material for:

> **Why Your AI Agent Hallucinates: Engineering Lessons From a Production Workflow
> Builder in Drupal**
> Shibin Devadas Kakanat (D34dman) · Development, AI & Agentic Architecture
> Tuesday 29 September 2026, 13:30–14:15 CEST · Mees Room I · 45 min · Intermediate
> <https://events.drupal.org/rotterdam2026/session/why-your-ai-agent-hallucinates-engineering-lessons-production-workflow>

The abstract promises seven architectural decisions that make LLM features reliable,
motivated by four named failure patterns: *hallucinated field names, half-applied state
changes, prompt-injection through user content, runaway token costs.*

This folder holds the **evidence** gathered on 2026-08-30/31 from a controlled benchmark
of eight FlowDrop workflow variants, extended on 2026-09-05 with two more (B8, B9),
plus the ideas for turning it into 45 minutes.

## What's here

| File | What it is |
|---|---|
| [research/01-method.md](research/01-method.md) | Benchmark design, the ten variants, what the metrics can and cannot say |
| [research/02-results-matrix.md](research/02-results-matrix.md) | The full numbers — every variant × model × page |
| [research/03-failure-gallery.md](research/03-failure-gallery.md) | **Four named failure modes with exact evidence.** The heart of the talk |
| [research/04-tool-shape.md](research/04-tool-shape.md) | B5 vs B7: what changes when a tool takes a URL instead of the content |
| [research/05-cost-and-caching.md](research/05-cost-and-caching.md) | Token economy, why prompt caching is unreachable, what this cost |
| [research/06-flowdrop-findings.md](research/06-flowdrop-findings.md) | Bugs found in FlowDrop itself, and the three issues filed upstream |
| [ideas/objective-mapping.md](ideas/objective-mapping.md) | The seven learning objectives ↔ the evidence, **including the gaps** |
| [ideas/talk-outline.md](ideas/talk-outline.md) | A 45-minute slide-by-slide plan |
| [ideas/open-questions.md](ideas/open-questions.md) | What to run before the talk, with cost estimates |
| [data/](data/) | **Frozen CSV snapshot of all 203 runs** — the durable copy. The harness and its raw ledgers are committed under `scratchpad/bench/`; runs enter this folder only through `fold_runs.py` |
| [v2/](v2/) | **Report v2** — the same runs re-graded against gold documents into Correct / Degraded / Silent / Format / Loud. Start with [v2/README.md](v2/README.md) |

## Published artifacts (interactive, for reference or live demo)

Public copies of every page, plus the tech all-hands slides, are served from GitHub Pages:
<https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/> (source in `site/redaction-benchmark/`).

Full index of everything (published pages + repo files): [ARTIFACTS.md](ARTIFACTS.md),
also as a shareable page — <https://claude.ai/code/artifact/47c9cb5c-16cf-43a4-96e9-cb05836a2dd0>


- **Benchmark overview, all variants, global filters** — <https://claude.ai/code/artifact/33ba2dce-38f5-4f19-b3a1-eff81053bc93>
- **Threshold explorer** (parallel coordinates, drag to set acceptable cost/time/quality) — see `bench-explorer.html`
- **ReAct Redactor Deep Dive** (B5 across four models) — <https://claude.ai/code/artifact/e2a1cb1f-59b2-4cf8-a383-8394b394facd>
- **URL-Shaped Tool Deep Dive** (B5 vs B7) — <https://claude.ai/code/artifact/9360ca71-6e39-4526-b1c8-a9ada5f39017>

## The one-sentence finding

> Across eight architectures and four models running one identical task, **the variant
> with the least agency was the only one that never failed silently** — and every failure
> that mattered was silent.

Report v2 sharpens this: of 116 graded runs, 7 failed silently, 6 of them in variants that
let the model decide what to do with the page. See [v2/README.md](v2/README.md).

## Status

Research is complete and reproducible; report v2 is drafted in `v2/`; the narrative is drafted but not slide-built.
Known gaps are listed in [ideas/open-questions.md](ideas/open-questions.md) — the biggest
is that **prompt injection (learning objective 3) has no experimental data at all.**
