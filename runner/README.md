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
   Also give ai_metering a price for each model you will run, at
   `/admin/config/ai/ai-metering` (manual entry keyed `provider:model`, per token) so the
   `cost_usd` the runner records is not zero; `ddev drush cex -y` exports it into
   `ai_metering.settings.yml` with the rest. Two limits of that module, both hit by
   OpenRouter: a model id with a dot in it (`qwen/qwen3.8-27b`) cannot be a config key,
   Drupal nests it at the dot and the lookup misses, and the LiteLLM sync stores OpenRouter
   rows as `openrouter:openrouter/<model>`, which the lookup never matches either. Such a
   model records `cost_usd: 0`. That is fine for the study: the site prices every run from
   its tokens against `scoring/pricing.json` and treats the runner's figure as advisory
   (`cost_usd_runner`); the row there is the one that must exist.
5. **Run.** Pass `--provider=openai` on every run. `bench:run` checks the model id against
   the named provider's catalogue before it starts (default `anthropic`), and the two cells
   built on the AI Agents module (B4, B6) store `provider__model` in their config. The chat
   and reason nodes themselves take the bare id and find the provider through the ai module.
   ```sh
   ddev drush bench:run B3 gpt-5 --provider=openai --pages=small --tag=yourname-openai-first
   ddev drush bench:run B4,B6 gpt-5 --provider=openai --pages=small --tag=yourname-openai-agents
   ```
   Prefer a dated model id when the provider lists one (see CONTRIBUTING). If two installed
   providers list the same bare id, the ai module's resolution decides which answers; avoid
   that by not installing overlapping providers on one runner.

## What is in here

| Path | What |
|---|---|
| `composer.json`, `composer.lock`, `patches.lock.json` | The site's dependencies, pinned. `drupal/flowdrop` and `drupal/flowdrop_ai_provider` are `2.x-dev` at the commits in the lock. |
| `patches/` | Two composer patches, both part of the experiment: FlowDrop memory's max value size made configurable (#3592436), and the 4000 `maxTokens` cap removed from the Chat nodes so a whole document can come back in one call. Both are recorded in every run's `flowdrop_version`. Two fixes the bench found on 2026-09-06 (a tool with one text answer replies in plain text, fddo 1834221c; a loop-free workflow no longer warns about an unrestorable loop extent, fddo 5f451c49) were carried as patches for the rerun and are now in the pinned FlowDrop 2.x commit. |
| `config/sync/` | The site's whole configuration: the nine cell workflows, six sub-workflows and their node types, two AI Agents entities, key, metering, and the FlowDrop settings the runs were made with (including `default_orchestrator`). |
| `web/modules/custom/flowdrop_ai_bench/` | The module: `http_fetch` tool for the autonomous agent, the metering context tag that attributes tokens to one run, and the `bench:*` Drush commands. GPL-2.0-or-later. |
| `var/` | Ledger and fetch cache, gitignored. |

## Adding a variant

Build the workflow in the site (`/admin/structure/flowdrop-workflow`, the FlowDrop UI is
installed), give it the id `bench_<n>_<name>`, export config (`ddev drush cex -y`), add the
cell letter to the map in `Harness.php`, and describe the architecture in your PR.

## Warnings a run prints, and what they mean

`bench:run` and `bench:launch` do not print the first three rows below. FlowDrop logs them at
warning level because in a workflow under construction they can point at a mistake; in the
benchmark cells they are the documented, intended shape of the workflow, and at several per
loop iteration they buried the one line worth reading. The harness drops exactly these
message templates while a command runs (the list, with the reason for each entry, is
`src/Logger/KnownWarnings.php` in the module) and ends with one `quiet` line giving the
counts, so nothing disappears silently. Everything else still prints: an unlisted warning,
the sync/async orchestrators' `on job` variant of the fan-in message, or any of these texts
at error level. `--all-warnings` turns the filter off.

| Warning | Cells | Meaning |
|---|---|---|
| `Removed disallowed Markdown link with URL: https://github.com/...` / `Removed disallowed AI output URL` | every model cell | The AI module's hostname filter strips links to hosts outside `ai.settings:allowed_hosts` from model output. It only ever hit the footer link to this repo, which is page chrome and not scored; `github.com` is now allowed so the model cells keep the link like B1 does. |
| `Cross-iteration data read on pipeline N ... (BR-6); logged for observability only` | B5, B7, B8, B9 | The loop-staleness barrier noting that a consumer in iteration n read a producer's value from iteration 0. Expected for the conversation buffers feeding message assembly; nothing is gated. |
| `ToolBox flowdrop_node_processor_toolbox.1 has no tools wired into it` | B8, B9 | By design: in the "tools in the parent" cells the engine's own ToolBox is empty and the tools arrive from the parent workflow as an execution argument. |
| `Multiple sources target port 'loop_back' on node 'conversation_buffer.1'; keeping value from latest executor` | B9 | The Reflexion engine has two legitimate re-entry paths into the actor loop, tool results and critiques, both wired to the same trigger port. Whichever fired last wins, which is the intended semantics; neither edge can be removed. |
| `Pipeline N has a loop-extent snapshot that could not be restored` | B7, B8, B9 (before the patch) | Was a false positive on the loop-free `url_to_markdown` tool sub-pipeline, whose well-formed empty snapshot restored to the same empty map a malformed one does; fixed in FlowDrop 2.x (fddo 5f451c49). |
