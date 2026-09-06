# Runner

A minimal Drupal 11 site that runs the benchmark cells. The DDEV project root is the
repository root (so the harness can write straight into `runs/` and `outputs/`); the
Drupal docroot is `runner/web` and composer runs in `runner/`.

## Set up once

```sh
git clone git@github.com:d34dman/flowdrop-ai-bench.git && cd flowdrop-ai-bench
echo 'ANTHROPIC_KEY=sk-ant-...' >> .ddev/.env
ddev start
sh bin/setup.sh          # composer install, site install from runner/config/sync
```

## Run

```sh
ddev drush bench:wizard                      # first time: pick model, cells, pages, confirm
ddev drush bench:models                      # model ids the provider offers
ddev drush bench:run B3 claude-haiku-4-5-20251001 --pages=small --tag=yourname-first
ddev drush bench:run B2,B3,B5 claude-sonnet-5 --pages=small,medium,large --tag=yourname-sonnet5-sweep
ddev drush bench:list B5 small sonnet-5
```

`bench:run` sets the prompt in every cell (fetched from this repo's published site, hash
recorded), sets the model, launches the cells against the corpus pages, and collects
one `runs/<run_id>.json` and one `outputs/<run_id>.md` per run. The ledger is
`runner/var/runs.jsonl` (not committed). Then `git add runs outputs` and open a PR.

A run id is `<workflow>__<page>__r<rep>__<unix seconds>[__<tag>]__<6 hex>`. The random
suffix is what makes ids unique across contributors; the tag segment is only there for a
human reading the directory, and is left out when `--tag` was not given.

Each step is also its own command: `bench:set-prompt`, `bench:set-model`, `bench:launch`,
`bench:collect`. Details and options: `runner/web/modules/custom/flowdrop_ai_bench/README.md`
or `ddev drush help bench:run`.

## Adding a provider

The runner talks to models through the [Drupal AI](https://www.drupal.org/project/ai)
module, so any provider with an `ai_provider_*` module works, and the benchmark treats it
like Anthropic: `bench:models` lists what the key can use, `bench:run` records the model
id and the metering rows it produced. Anthropic is the only provider shipped today. To add
one, OpenAI as the example:

1. **Install the provider module** in the runner (the DDEV composer root is `runner/`):
   ```sh
   ddev composer require drupal/ai_provider_openai
   ddev drush en ai_provider_openai -y
   ```
2. **Give it a key through the environment.** Keys are never config: the site holds a
   [Key](https://www.drupal.org/project/key) entity that points at an environment variable,
   and the value lives in `.ddev/.env`, which is gitignored and loaded into the web
   container on start.
   ```sh
   echo 'OPENAI_KEY=sk-...' >> .ddev/.env && ddev restart
   ddev exec 'echo OPENAI_KEY ${OPENAI_KEY:+is set}'
   ddev drush php:eval "\Drupal::entityTypeManager()->getStorage('key')->create(['id' => 'openai_key', 'label' => 'OPENAI_KEY', 'key_type' => 'authentication', 'key_provider' => 'env', 'key_provider_settings' => ['env_variable' => 'OPENAI_KEY', 'base64_encoded' => FALSE, 'strip_line_breaks' => FALSE], 'key_input' => 'none'])->save();"
   ```
   The same thing can be done in the UI at `/admin/config/system/keys/add` (provider
   "Environment").
3. **Point the provider at the key** at `/admin/config/ai/providers/openai`, then check:
   ```sh
   ddev drush bench:models --provider=openai
   ```
4. **Ship it with the runner** so the next contributor does not repeat steps 1 and 3.
   Export config and open a pull request with the module and the config:
   ```sh
   ddev drush cex -y          # adds key.key.openai_key.yml, ai_provider_openai.settings.yml, core.extension.yml
   git add runner/composer.json runner/composer.lock runner/config/sync
   git commit -m "runner: OpenAI provider"
   ```
   `bin/setup.sh` installs from that config, so on a fresh clone the provider exists and
   only the `OPENAI_KEY=` line in `.ddev/.env` is personal. A missing key leaves the provider
   unusable and everything else working.
5. **Run.** Model ids are bare; the chat and reason nodes find the provider from the id
   through the ai module, so `--provider` matters only for the two cells built on the AI
   Agents module (B4, B6), whose config stores `provider__model`:
   ```sh
   ddev drush bench:run B3 gpt-5 --pages=small --tag=yourname-openai-first
   ddev drush bench:run B4,B6 gpt-5 --provider=openai --pages=small --tag=yourname-openai-agents
   ```
   Prefer a dated model id when the provider lists one (see CONTRIBUTING). If two installed
   providers list the same bare id, the ai module's resolution decides which answers; avoid
   that by not installing overlapping providers on one runner.

## What is in here

| Path | What |
|---|---|
| `composer.json`, `composer.lock`, `patches.lock.json` | The site's dependencies, pinned. `drupal/flowdrop` and `drupal/flowdrop_ai_provider` are `2.x-dev` at the commits in the lock. |
| `patches/` | Two composer patches: FlowDrop memory's max value size made configurable (#3592436), and the 4000 `maxTokens` cap removed from the Chat nodes so a whole document can come back in one call. Both are part of the experiment and recorded in every run's `flowdrop_version`. |
| `config/sync/` | The site's whole configuration: the nine cell workflows, six sub-workflows and their node types, two AI Agents entities, key, metering, and the FlowDrop settings the runs were made with (including `default_orchestrator`). |
| `web/modules/custom/flowdrop_ai_bench/` | The module: `http_fetch` tool for the autonomous agent, the metering context tag that attributes tokens to one run, and the `bench:*` Drush commands. GPL-2.0-or-later. |
| `var/` | Ledger and fetch cache, gitignored. |

## Adding a variant

Build the workflow in the site (`/admin/structure/flowdrop-workflow`, the FlowDrop UI is
installed), give it the id `bench_<n>_<name>`, export config (`ddev drush cex -y`), add the
cell letter to the map in `Harness.php`, and describe the architecture in your PR.
