# FlowDrop AI Benchmark (flowdrop_ai_bench)

Drush 13 harness for the FlowDrop pipeline-vs-agent benchmark, plus the
supporting AI plugins the benchmarked graphs and agents need (an HTTP fetch
function-call tool, and an event subscriber that stamps every AI call made
during a run with that run's id so `ai_metering` can attribute its tokens).

Corpus pages and the prompt are fetched over HTTP from
`https://d34dman.github.io/flowdrop-ai-bench/` (override with `--base` or the
`BENCH_BASE` env var) at corpus version `v1` (override with `--corpus` or
`BENCH_CORPUS`). The ledger records the exact corpus version and prompt hash
each run used, so a run is reproducible from those alone.

## Paths

- Drupal root: `runner/web`.
- Ledger: `runner/var/runs.jsonl` (override with `--var`).
- Fetch cache: `runner/var/cache/`.
- Per-run output, at the repo root two levels above `runner/web`:
  `<repo>/runs/<run_id>.json` (pretty JSON) and
  `<repo>/outputs/<run_id>.md` (override the repo root with `--out`).

## Commands

### `bench:set-prompt [--prompt] [--critic] [--base] [--var]`

Writes the one benchmark prompt (and, for reflexion cells, the critic
template) into every model-calling cell: `config.systemPrompt` on
`ai_provider_chat`/`processor_reason` nodes (un-exposing that input port so it
cannot shadow the value), `config.system_prompt`/`config.critic_prompt` on
react/reflexion engine nodes, and `system_prompt` on the two benchmark
`ai_agent` entities.

```
drush bench:set-prompt
drush bench:set-prompt --prompt=prompt/redact.v2.md
```

### `bench:set-model <model> [--provider=anthropic]`

Points every model call at one model: `config.model` on
`ai_provider_chat`/`processor_reason` nodes, `config.llm_model` (as
`provider__model`) on `ai_agents_executor` nodes.

```
drush bench:set-model claude-sonnet-5
```

### `bench:launch <cells> [--pages=small,medium,large] [--reps=1] [--tag] [--model] [--base] [--corpus] [--var]`

Launches one or more cells (`B0`..`B9`, or raw workflow ids, comma-separated)
against the given manifest pages, appending one ledger line per run to
`runs.jsonl`. `--tag` is required — it is how `bench:list` and the summary
table find these runs afterwards. `--model` defaults to whatever is
configured on the `bench_3_markdown_llm` chat node.

```
drush bench:launch B5,B8 --tag=b5-b8-sonnet5
```

### `bench:collect [--var] [--out]`

Derives metrics for every ledger line from stored pipelines/jobs and the
`ai_metering_usage` table, rewriting `<repo>/runs/<run_id>.json` and
`<repo>/outputs/<run_id>.md`. Idempotent: safe to re-run at any time, in any
order, without spending anything. A ledger line whose pipeline no longer
exists is skipped with a warning.

```
drush bench:collect
```

### `bench:run <cells> <model> [--pages] [--reps] [--tag] [--provider] [--base] [--corpus] [--var] [--out]`

The one-command path: `bench:set-prompt`, `bench:set-model`, `bench:launch`,
then `bench:collect`, aborting on the first failure. Prints a cost/time table
for the runs it just launched. `--tag` defaults to `<cells>-<model>`.

```
drush bench:run B5,B8 claude-sonnet-5
```

### `bench:list [cell] [page] [model-substring] [--out]`

Lists collected runs from `<repo>/runs/*.json`, optionally filtered by cell
(or raw workflow id), manifest page key, and a model substring, newest last.

```
drush bench:list B5 small
drush bench:list
```

## Environment variables

- `BENCH_BASE` — overrides the default bench site base URL.
- `BENCH_CORPUS` — overrides the default corpus version (`v1`).

## Output

By default every command prints one line per phase and one line per run, opened when the
run starts and closed when it finishes. Add `-v` to see which node and entity each prompt
and model write touched.
