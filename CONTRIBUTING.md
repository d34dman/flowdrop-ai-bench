# Contributing runs

The dataset is built from one JSON file per run in `runs/` and one Markdown output per run
in `outputs/`. Everything else, the CSVs in `data/` and the published page, is regenerated
by CI from those two folders on every merge. You never edit a CSV.

## The path

1. **Get a runner.** Today that is the FlowDrop Drupal demo: clone
   <https://github.com/d34dman/flowdrop-drupal-demo>, `ddev start`, `ddev composer install`,
   `ddev drush si --existing-config`, put `ANTHROPIC_KEY=sk-ant-...` in `.ddev/.env`, `ddev restart`.
2. **Run a cell.** Inside the demo checkout:
   ```sh
   ddev exec sh scratchpad/bench/run_cell.sh B3 claude-sonnet-5 small 1 yourname-first-run
   ```
   Cells B0–B9, pages `small,medium,large`, repetitions, and a tag that says who and why.
   The runner fetches the corpus pages and the prompt from this repo's site, so the same
   corpus version and prompt hash are recorded in every run.
3. **Look at it.** `python3 scratchpad/bench/summarize.py B3 small sonnet-5` and open
   `scratchpad/bench/results/outputs/<run_id>.md`.
4. **Export and open a PR.**
   ```sh
   python3 scratchpad/bench/export.py /path/to/flowdrop-ai-bench yourname-
   cd /path/to/flowdrop-ai-bench && git checkout -b runs/yourname && git add runs outputs && git commit -m "runs: B3 on Sonnet 5, small" && git push -u origin HEAD
   ```
   CI scores your runs on the PR. Merge publishes them.

## What we are glad to receive

- New models, including non-Anthropic ones once the runner supports the provider.
- Repetitions of existing cells; most cells are a single draw today.
- Failures, when the failure is the finding. Include them with `--include-failed` and say why.
- A new variant: copy one of the `bench_*` workflows in the runner, give it the next number,
  add it to `run_cell.sh`, and describe the architecture in the PR.

## What changes the experiment

The prompt, the glyph, the competitor list and the corpus pages are fixed per version.
A change to any of them is a new `prompt/redact.v2.md` or `corpus/v2/`, never an edit in
place, so old runs stay comparable with each other. Propose such a change in an issue first.

## Scoring

`python3 scoring/score.py` grades every run; `--explain <run_id-prefix>` shows why one run
scored as it did, sentence by sentence. It is deterministic and uses only the standard
library, so a disagreement with a score is a bug report against the scorer, and welcome.
