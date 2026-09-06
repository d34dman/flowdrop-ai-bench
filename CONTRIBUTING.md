# Contributing runs

The dataset is built from one JSON file per run in `runs/` and one Markdown output per run
in `outputs/`. Everything else, the CSVs in `data/` and the published page, is regenerated
by CI from those two folders on every merge. You never edit a CSV.

The dataset is append-only. A pull request adds run files and never modifies, renames or
deletes an existing one; CI rejects it otherwise. Run ids carry a random suffix, so two
contributors can never produce the same filename and PRs never conflict. `traces/` is
covered by the same append-only check, and CI also rejects a trace over 3 MB.

## The path

1. **Set up the runner** (once). Clone this repo, put `ANTHROPIC_KEY=sk-ant-...` in
   `.ddev/.env`, `ddev start`, `sh bin/setup.sh`. Needs [DDEV](https://ddev.readthedocs.io/).
2. **Run a cell.** The first time, let the wizard ask:
   ```sh
   ddev drush bench:wizard
   ```
   It lists the models your provider key can use, the cells B0–B9 with a line each, the
   pages, and shows the equivalent `bench:run` before it runs anything. Afterwards:
   ```sh
   ddev drush bench:models      # model ids the provider offers; bench:run refuses others
   ddev drush bench:run B3 claude-sonnet-5 --pages=small --tag=yourname-first-run
   ```
   Cells B0–B9, pages `small,medium,large`, `--reps`, and a tag that says who and why.
   The runner fetches the corpus pages and the prompt from this repo's published site, so
   the same corpus version and prompt hash are recorded in every run.
3. **Look at it.** `ddev drush bench:list B3 small sonnet-5` and open `outputs/<run_id>.md`.
   To see the score CI will give it: `python3 scoring/score.py` (needs only Python 3).
4. **Commit and open a PR.** The runner has already written `runs/<run_id>.json` and
   `outputs/<run_id>.md` into the checkout, and, if the harness collected one,
   `traces/<run_id>.json.gz`.
   ```sh
   git checkout -b runs/yourname && git add runs outputs traces && git commit -m "runs: B3 on Sonnet 5, small" && git push -u origin HEAD
   ```
   CI scores your runs on the PR. Merge publishes them.

## What we are glad to receive

- New models, including from other providers: any Drupal AI `ai_provider_*` module works,
  see [Adding a provider](runner/README.md#adding-a-provider) in the runner README. Prefer
  the dated id when the provider lists one (`claude-haiku-4-5-20251001`, not
  `claude-haiku-4-5`): an undated alias can be repointed to a newer snapshot and the run
  records only the id that was requested. The scorer groups both forms under one
  `model_family` for the published tables, so the study reads per model either way.
- Repetitions of existing cells; most cells are a single draw today.
- Failures, when the failure is the finding. Commit the failed run's JSON and say why in the PR.
- A new variant: build it in the runner site, export config, add its cell letter to the
  map in the module, and describe the architecture in the PR (see `runner/README.md`).

## What changes the experiment

The prompt, the glyph, the competitor list and the corpus pages are fixed per version.
Until the benchmark's 1.0 tag, `v1` may still be edited in place; the scorer marks any run
whose recorded page hash no longer matches the manifest as `stale` and leaves it ungraded.
From 1.0 on, a change to any of them is a new `prompt/redact.v2.md` or `corpus/v2/`, never
an edit in place, so old runs stay comparable with each other. Propose such a change in an
issue first.

## Scoring

`python3 scoring/score.py` grades every run; `--explain <run_id-prefix>` shows why one run
scored as it did, sentence by sentence. It is deterministic and uses only the standard
library, so a disagreement with a score is a bug report against the scorer, and welcome.

## Add a visual

The site is a homepage that indexes independent pages ("visuals"), each built by its own CI
job from the same scored data (`data/scores.csv` from `scoring/score.py`). A visual is a
folder `site/visuals/<id>/`:

- `visual.json`: `title`, `blurb`, `filters` (ids from `site/filters.json` the page honours),
  optional `focus` (a filter id the page needs exactly one value of; it becomes a select).
- `build.py`: `def build(ctx)` writes `ctx.out/index.html`, normally
  `ctx.write('index.html', ctx.page(title, body_html, sub=..., scripts=(...)))`. `ctx` carries
  the scored rows, facets, registry, corpus manifests and the set of traced run ids
  (`site/lib/framework.py`). Use build-time rendering only for things the browser cannot do
  (one page per trace); everything that should react to filters is rendered by `page.js`.
- `page.js` (optional): `Bench.ready(({rows, all, facets, state, focus}) => ...)` runs once the
  data is loaded and again after every filter change, with `rows` already filtered. Helpers:
  `Bench.esc`, `Bench.pill`, `Bench.cell`, `Bench.label`, `Bench.graded`, `Bench.href`,
  `Bench.query` (the current query string, to build links that keep the selection).
  `Compare.render` (`site/lib/compare.js`, include via `scripts=('lib/compare.js',)`) draws the
  correctness and axes tables the two focus pages use.

Then add the id to `site/registry.json`; the homepage, the nav and the CI matrix are all
generated from it. Ids are `[a-z0-9-]` and may not be `corpus`, `prompt`, `outputs`, `runs`,
`data` or `lib`, which the data stage publishes at the site root. Check it with
`python3 site/build.py visual <id>` and a full `python3 site/build.py`.

Adding a **filter** is one line in `site/filters.json` (`id`, `label`, `column` of
`scores.csv`, optional `labels` map, `order`, or `split` for multi-valued columns); a visual
opts in by listing the id. Adding a **column** the filters or visuals need belongs in
`scoring/score.py` (`flat()` for ledger-derived fields, `score()` for graded axes), never in
the site: the CSVs stay the single source every visual reads.
