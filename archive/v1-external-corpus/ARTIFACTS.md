# Benchmark & analysis — artifact index

Everything produced for the DrupalCon Rotterdam 2026 talk research
(2026-08-30 → 09-01). Interactive index of the same list:
<https://claude.ai/code/artifact/47c9cb5c-16cf-43a4-96e9-cb05836a2dd0>

## Interactive artifacts (published)

The claude.ai links are private to the author. The **Public copy** column is the same
page exported into this repo and served from GitHub Pages. On 2026-09-05 the nine v1 pages
moved to `site/redaction-benchmark/archive/v1/` (old URLs redirect); the two v2 pages under
`artifacts/` are generated from `data/runs_v2.csv`: <https://d34dman.github.io/flowdrop-drupal-demo/>

| Artifact | What it shows | Updated | Public copy |
|---|---|---|---|
| Redaction Benchmark Plots v2 (repo-generated, no claude.ai original) | One model at a time (single-select, Sonnet 4.6 by default): eight variants across three pages on the v2 axes, five plots plus the run table | 2026-09-05 | [redaction-benchmark-plots-v2](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/artifacts/redaction-benchmark-plots-v2.html) |
| Redactor Model Matrix v2 (repo-generated, no claude.ai original) | Variant × model × page on the v2 axes: fidelity against cost, what was redacted on the medium page, fidelity as the page grows, cost per cell | 2026-09-05 | [redactor-model-matrix-v2](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/artifacts/redactor-model-matrix-v2.html) |
| Rubric v2 Scorecard (repo-generated, no claude.ai original) | Every run re-graded against a gold document: outcome-class matrix, six axes, cost per correct run. **Supersedes the Explorer, Plots and Model Matrix numbers** | 2026-09-05 | [rubric-v2-scorecard](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/artifacts/rubric-v2-scorecard.html) |
| [Why Your AI Agent Hallucinates](https://claude.ai/code/artifact/4d0184e1-547a-4dad-9060-bd81cedc913c) | Talk-companion page — failure modes and lessons, matching the session abstract | 2026-09-01 | [why-your-ai-agent-hallucinates](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/why-your-ai-agent-hallucinates.html) |
| [Caching the Agent Route](https://claude.ai/code/artifact/b2fa38fe-d50f-4d1a-ad2f-c90562ec2565) | Token economy; why prompt caching is unreachable for the agentic variants | 2026-09-01 | [caching-the-agent-route](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/caching-the-agent-route.html) |
| [Redaction Tradeoff Explorer](https://claude.ai/code/artifact/1fdd6f40-a31b-43f8-83a1-39a3d0a4c7e4) | Threshold explorer — parallel coordinates over all nine variants, drag to set acceptable cost/time/quality | 2026-09-05 | [redaction-tradeoff-explorer](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/redaction-tradeoff-explorer.html) |
| [Redaction Benchmark Plots](https://claude.ai/code/artifact/33ba2dce-38f5-4f19-b3a1-eff81053bc93) | Benchmark overview — all nine variants on one model (B8/B9 added), global filters | 2026-09-05 | [redaction-benchmark-plots](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/redaction-benchmark-plots.html) |
| [URL-Shaped Tool Deep Dive](https://claude.ai/code/artifact/9360ca71-6e39-4526-b1c8-a9ada5f39017) | B5 vs B7 — what changes when a tool takes a URL instead of the content | 2026-08-31 | [url-shaped-tool-deep-dive](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/url-shaped-tool-deep-dive.html) |
| [How the Redaction Benchmark Works](https://claude.ai/code/artifact/418dbee8-3e92-4635-b928-454260443158) | Method explainer — the task, the variants, metric caveats | 2026-08-30 | [how-the-redaction-benchmark-works](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/how-the-redaction-benchmark-works.html) |
| [Seven Ways to Redact a Page](https://claude.ai/code/artifact/ba617bdd-e7ce-4fff-af54-2b4a481f2627) | The workflow architectures compared side by side | 2026-08-30 | [seven-ways-to-redact-a-page](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/seven-ways-to-redact-a-page.html) |
| [Redactor Model Matrix](https://claude.ai/code/artifact/f0cec580-bfd2-443f-85be-c8627940d9b8) | Variant × model results grid — B3/B5/B6 on four models, B8/B9 on three | 2026-09-05 | [redactor-model-matrix](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/redactor-model-matrix.html) |
| [ReAct Redactor Deep Dive](https://claude.ai/code/artifact/e2a1cb1f-59b2-4cf8-a383-8394b394facd) | B5 (the ReAct agent variant) across four models | 2026-08-30 | [react-redactor-deep-dive](https://d34dman.github.io/flowdrop-drupal-demo/redaction-benchmark/archive/v1/react-redactor-deep-dive.html) |

## In this repo

### Research (`docs/drupalcon/research/`, commit 81c349b)

- [01-method.md](research/01-method.md) — benchmark design, the ten variants, metric caveats
- [02-results-matrix.md](research/02-results-matrix.md) — the full numbers, every variant × model × page
- [03-failure-gallery.md](research/03-failure-gallery.md) — four named failure modes with exact evidence
- [04-tool-shape.md](research/04-tool-shape.md) — B5 vs B7: URL-shaped vs content-shaped tools
- [05-cost-and-caching.md](research/05-cost-and-caching.md) — token economy, caching, what this cost
- [06-flowdrop-findings.md](research/06-flowdrop-findings.md) — FlowDrop bugs found; four issues filed upstream

### Report v2 (`docs/drupalcon/v2/`, 2026-09-05)

The same runs re-graded against hand-cleaned gold documents; supersedes the conclusions in
`research/02` and `research/03`, which stay frozen as the record of what was published first.

- [v2/README.md](v2/README.md) — index and the one-sentence finding
- [v2/00-what-changed.md](v2/00-what-changed.md) — why v1's metrics were replaced; the v1 → v2 autopsy
- [v2/01-method.md](v2/01-method.md) — gold documents, gates, axes, outcome classes
- [v2/02-scorecard.md](v2/02-scorecard.md) — outcome-class matrix and per-axis tables
- [v2/03-failure-gallery.md](v2/03-failure-gallery.md) — six failures, and the axis that catches each
- [v2/04-cost-per-correct.md](v2/04-cost-per-correct.md) — cost conditioned on class
- [v2/05-flowdrop-findings.md](v2/05-flowdrop-findings.md) — carried forward, plus the confirmation-gate pauses

### Talk preparation (`docs/drupalcon/ideas/`)

- [talk-outline.md](ideas/talk-outline.md) — 45-minute slide-by-slide plan
- [objective-mapping.md](ideas/objective-mapping.md) — learning objectives ↔ evidence, gaps included
- [open-questions.md](ideas/open-questions.md) — experiments still to run, with cost estimates
- [report-v2-rubric.md](ideas/report-v2-rubric.md) — the rubric v2 proposal and re-report plan

### Published site (`docs/drupalcon/site/`)

- [site/redaction-benchmark/index.html](site/redaction-benchmark/index.html) — this study's landing page linking every HTML page below (the root `site/index.html` lists all studies); deployed to
  GitHub Pages by `.github/workflows/pages.yml`: <https://d34dman.github.io/flowdrop-drupal-demo/>
- [site/redaction-benchmark/slides/tech-all-hands-2026-09-04.html](site/redaction-benchmark/slides/tech-all-hands-2026-09-04.html) — 20-minute internal
  tech all-hands deck, 15 slides with speaker notes and time budget
- [site/redaction-benchmark/archive/v1/](site/redaction-benchmark/archive/v1/) — the nine interactive pages above, exported as standalone HTML

### Data (`docs/drupalcon/data/`)

- [runs.csv](data/runs.csv) — frozen snapshot of all 203 benchmark runs (the durable copy)
- [runs_v2.csv](data/runs_v2.csv), [RUNS_V2.md](data/RUNS_V2.md) — the same runs under rubric v2, and how to read them
- [gold/](data/gold/) — the hand-cleaned gold documents v2 grades against
- [outputs/](data/outputs/) — the verbatim output of every run
- [controls.csv](data/controls.csv) — control-run baselines

### Harness (`scratchpad/bench/`, commit a86dfa8)

- Harness: `harness.php`, `launch.php`, `collect.php`, `run_one.php`, `build*.php`
- Analysis: `analyse.py`, `overhead.py`, `report_final.py`
- Raw logs: `matrix.log`, `matrix2.log`, `b5*.log`, `b6.log`, `large.log`, `rep1.log`
- Supporting config: benchmark workflows/agents/node types in commits 6fa6184 and 2f4f216; `fd_bench` module in a86dfa8

## Status

Report v2 (rubric with gold documents, outcome classes) is drafted in `v2/` and published as the
Rubric v2 Scorecard page (generated by `data/build_site_v2.py`); the three v1 data pages carry a
superseded banner and keep their URLs.
Research complete and reproducible; the 20-minute internal deck is built (see Slides), the 45-minute DrupalCon deck is not.
B8 and B9 (2026-09-05) are in the data, the three data-driven pages and the research docs, including the B9 cells rerun after the FlowDrop fix; the narrative pages
(Seven Ways, URL-Shaped Tool Deep Dive, the deck) still describe eight variants. Biggest gap:
prompt injection (learning objective 3) has no experimental data —
see [ideas/open-questions.md](ideas/open-questions.md).
