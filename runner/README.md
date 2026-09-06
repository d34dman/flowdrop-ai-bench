# Runner

A minimal Drupal 11 site that runs the benchmark cells. The DDEV project root is the
repository root (so the harness can write straight into `runs/` and `outputs/`); the
Drupal docroot is `runner/web` and composer runs in `runner/`.

## Set up once

```sh
git clone git@github.com:d34dman/flowdrop-ai-bench.git && cd flowdrop-ai-bench
echo 'ANTHROPIC_KEY=sk-ant-...' >> .ddev/.env
ddev start
sh runner/bin/setup.sh          # composer install, site install from runner/config/sync
```

## Run

```sh
ddev drush bench:run B3 claude-haiku-4-5-20251001 --pages=small --tag=yourname-first
ddev drush bench:run B2,B3,B5 claude-sonnet-5 --pages=small,medium,large --tag=yourname-sonnet5-sweep
ddev drush bench:list B5 small sonnet-5
```

`bench:run` sets the prompt in every cell (fetched from this repo's published site, hash
recorded), sets the model, launches the cells against the corpus pages, and collects
one `runs/<run_id>.json` and one `outputs/<run_id>.md` per run. The ledger is
`runner/var/runs.jsonl` (not committed). Then `git add runs outputs` and open a PR.

Each step is also its own command: `bench:set-prompt`, `bench:set-model`, `bench:launch`,
`bench:collect`. Details and options: `runner/web/modules/custom/flowdrop_ai_bench/README.md`
or `ddev drush help bench:run`.

## What is in here

| Path | What |
|---|---|
| `composer.json`, `composer.lock`, `patches.lock.json` | The site's dependencies, pinned. `drupal/flowdrop` and `drupal/flowdrop_ai_provider` are `2.x-dev` at the commits in the lock. |
| `patches/` | Two composer patches: FlowDrop memory's max value size made configurable (#3592436), and the 4000 `maxTokens` cap removed from the Chat nodes so a whole document can come back in one call. Both are part of the experiment and recorded in every run's `flowdrop_version`. |
| `config/sync/` | The site's whole configuration: the nine cell workflows, six sub-workflows and their node types, two AI Agents entities, key, metering, and the FlowDrop settings the runs were made with (including `default_orchestrator`). |
| `web/modules/custom/flowdrop_ai_bench/` | The module: `http_fetch` tool for the autonomous agent, the metering context tag that attributes tokens to one run, and the `bench:*` Drush commands. GPL-2.0-or-later. |
| `bin/setup.sh`, `bin/run_cell.sh` | Bootstrap, and a positional wrapper around `bench:run`. |
| `var/` | Ledger and fetch cache, gitignored. |

## Adding a variant

Build the workflow in the site (`/admin/structure/flowdrop-workflow`, the FlowDrop UI is
installed), give it the id `bench_<n>_<name>`, export config (`ddev drush cex -y`), add the
cell letter to the map in `Harness.php`, and describe the architecture in your PR.
