# Cost, token economy, and the caching that isn't there

Covers the abstract's fourth failure pattern — **runaway token costs**.

## What this research cost

**$53.94** metered across **192 harness runs** — $47.94 over the original two days, plus
$4.91 for the B8/B9 sweeps and $1.08 for the B9 reruns after the FlowDrop fix, both on
2026-09-05.

| Tag | Spend |
|---|---|
| `matrix-claude-opus-5` | $15.89 |
| `matrix-claude-sonnet-5` | $9.30 |
| `fill-large` | $6.13 |
| `final-sonnet5` (B5 vs B7 head-to-head) | $3.46 |
| untagged / exploratory | $2.71 |
| `bench6-fill` | $2.23 |
| `verify-sonnet-5` (the rerun that caught a bad draw) | $2.02 |
| `post-patch-10mb` | $1.90 |
| `bench89-claude-sonnet-5` (B8/B9) | $2.22 |
| `bench89-claude-sonnet-4-6` (B8/B9) | $1.89 |
| `matrix-claude-haiku-4-5` | $1.20 |
| `bench89-claude-haiku-4-5` (B8/B9) | $0.80 |
| `b9fix-*` (B9 cells rerun on the fixed module) | $1.08 |
| everything else (13 tags) | $3.10 |

By model:

| Model | Spend | Runs |
|---|---|---|
| Sonnet 5 | $19.29 | 52 |
| Opus 5 | $15.89 | 18 |
| Sonnet 4.6 | $15.87 | 29 |
| Haiku 4.5 | $2.88 | 27 |

> Opus ran 18 times and cost nearly as much as Sonnet 5's 52. **Model choice is a 12× lever on
> this workload** — but see below, because architecture is a bigger one.

The Anthropic billing export for 30 August showed a higher total (~$69) than the metered
figure for that day. The gap is runs made outside the harness — smoke tests, discarded
runs, and interactive work — not a metering error: the Opus 5 and Sonnet 5 rows
reconciled to the token against the export.

## The single most useful cost number

| | Cost |
|---|---|
| Head-to-head sweep, 6 runs | **$3.46** |
| — of which **B5** (content-argument tool) | **$2.91** |
| — of which **B7** (URL-argument tool) | **$0.55** |

The benchmark that discovered the finding is itself an instance of the finding: 84% of
the money went to the architecture that was wrong.

## Architecture beats model choice

Cheapest *correct* run on the medium page, by variant, Sonnet 5:

| Variant | Cost | Retention | Leaks |
|---|---|---|---|
| **B3** deterministic Markdown → 1 call | **$0.0593** | 98.0% | 0 |
| B7 ReAct + URL tool | $0.0603 | 93.2% | 2 |
| B6 autonomous | $0.2454 | 97.6% | 0 |
| B5 ReAct + content tool | $0.3077 | 93.4% | 1 |
| B4 agent + tool | $0.3735 | 76.0% | 0 (but redacted "Drupal") |
| B2 raw HTML → 1 call | $0.9356 | format failure | 3 |

**16× spread on the same task and the same model.** Switching Sonnet 5 → Haiku on B3
saves another 4× ($0.0140). Switching architecture saves more than switching model,
and unlike model choice it does not trade away correctness.

## Where the tokens actually go

The ReAct loop re-sends the entire conversation on every iteration. On the large page:

| | Calls | Input tokens |
|---|---|---|
| B5 + Sonnet 5 | 4 | **1,055,106** |
| B5 + Sonnet 4.6 | 3 | 503,345 |
| B5 + Opus 5 | 2 | 337,512 |
| B9 + Sonnet 5 (critic, 3 revisions) | 7 | 265,477 |
| **B7 + Sonnet 5** | **2** | **56,955** |
| **B8 + Sonnet 5** | **2** | **56,968** |

B9 is the new cautionary row: a critic loop re-sends the transcript on every revision, so
it lands at a quarter of B5's tokens for the same page and roughly four times B8's cost.
It would be the biggest beneficiary of caching if caching were reachable.

Two things are compounding: the page is re-sent per iteration, *and* B5's document also
travels as output tokens. Fewer, more decisive iterations are a real cost lever — and in
B5 it is the **model** that decides how many. In B7 it is the architecture, and the answer
is always 2.

## Prompt caching: unreachable, not merely unused

Every row in this benchmark shows **zero cached tokens**. This is not a configuration
mistake.

`ai_provider_anthropic` talks to Anthropic through the **OpenAI-compatible endpoint**
(`openai-php/client` against `https://api.anthropic.com/v1`). That endpoint accepts the
request and **silently ignores `cache_control`**. Verified empirically against a live key:

| Endpoint | Call 1 | Call 2 |
|---|---|---|
| native `/v1/messages` | writes 11,704 cache tokens | **reads 11,704** |
| compat `/v1/chat/completions` | — | identical `prompt_tokens`, no cache fields |

**No patch is possible** at the module level — it requires rewriting the provider against
the native Messages API. Filed as
[ai_provider_anthropic#3607961](https://git.drupalcode.org/project/ai_provider_anthropic/-/work_items/3607961).

### What it would have been worth

Measured from real per-call token sequences (`scratchpad/bench/cache_saving.php`), across
the 31 multi-call runs in the dataset:

- **1,477,418 of 4,874,158 input tokens (30%) were verbatim repeats** of an earlier call
  in the same run.
- Billed: **$17.83**. Recoverable with caching: **$2.31 — 13%.**

The gap between 30% of tokens and 13% of dollars is the cache-write premium (125% of
input) partly eating the read discount (10%).

> **The honest framing for the stage:** caching is worth 13% here. Fixing the tool shape
> was worth **83%** on the same runs. Structural fixes first, caching after — and know
> which of the two your provider even permits.

## Pricing reference (per MTok)

| Model | Input | Output | Cache write | Cache read |
|---|---|---|---|---|
| Haiku 4.5 | $1 | $5 | $1.25 | $0.10 |
| Sonnet 4.6 | $3 | $15 | $3.75 | $0.30 |
| Sonnet 5 | $2 | $10 | $2.50 | $0.20 |
| Opus 5 | $5 | $25 | $6.25 | $0.50 |
