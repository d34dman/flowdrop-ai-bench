# Contributing runs

The dataset is built from one JSON file per run in `runs/` and one Markdown output per run
in `outputs/`. Everything else, the CSVs in `data/` and the published page, is regenerated
by CI from those two folders on every merge. You never edit a CSV.

## The path

1. **Set up the runner** (once). Clone this repo, put `ANTHROPIC_KEY=sk-ant-...` in
   `.ddev/.env`, `ddev start`, `sh runner/bin/setup.sh`. Needs [DDEV](https://ddev.readthedocs.io/).
2. **Run a cell.**
   ```sh
   ddev drush bench:run B3 claude-sonnet-5 --pages=small --tag=yourname-first-run
   ```
   Cells B0–B9, pages `small,medium,large`, `--reps`, and a tag that says who and why.
   The runner fetches the corpus pages and the prompt from this repo's published site, so
   the same corpus version and prompt hash are recorded in every run.
3. **Look at it.** `ddev drush bench:list B3 small sonnet-5` and open `outputs/<run_id>.md`.
   To see the score CI will give it: `python3 scoring/score.py` (needs only Python 3).
4. **Commit and open a PR.** The runner has already written `runs/<run_id>.json` and
   `outputs/<run_id>.md` into the checkout.
   ```sh
   git checkout -b runs/yourname && git add runs outputs && git commit -m "runs: B3 on Sonnet 5, small" && git push -u origin HEAD
   ```
   CI scores your runs on the PR. Merge publishes them.

## What we are glad to receive

- New models, including non-Anthropic ones once the runner supports the provider.
- Repetitions of existing cells; most cells are a single draw today.
- Failures, when the failure is the finding. Commit the failed run's JSON and say why in the PR.
- A new variant: build it in the runner site, export config, add its cell letter to the
  map in the module, and describe the architecture in the PR (see `runner/README.md`).

## What changes the experiment

The prompt, the glyph, the competitor list and the corpus pages are fixed per version.
A change to any of them is a new `prompt/redact.v2.md` or `corpus/v2/`, never an edit in
place, so old runs stay comparable with each other. Propose such a change in an issue first.

## Scoring

`python3 scoring/score.py` grades every run; `--explain <run_id-prefix>` shows why one run
scored as it did, sentence by sentence. It is deterministic and uses only the standard
library, so a disagreement with a score is a bug report against the scorer, and welcome.
