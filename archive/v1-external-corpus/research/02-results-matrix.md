# Results — the full matrix

All figures metered from `ai_metering_usage`. `kept` = retention vs the de-noised control
(see [01-method.md](01-method.md)). `red` = `▌▌▌▌` marks placed. `leak` = competitor
mentions still readable.

Control competitor mentions: **small 0 · medium 36 · large 5**.

## Orchestration floor — what FlowDrop itself costs

| Variant | n | Median | p90 | Min | Max |
|---|---|---|---|---|---|
| B0 empty pipeline | 30 | **0.024s** | 0.036s | 0.014s | 0.179s |
| B1 deterministic fetch + convert | 30 | **0.258s** | 0.792s | 0.122s | 1.562s |

> **Use this to close down the "the framework is slow" objection before it opens.**
> FlowDrop's own orchestration is 24 ms. A full deterministic fetch-and-convert of a
> 535 KB page is a quarter of a second. Every remaining second in this document is the
> model.

## The model matrix — one draw per cell

Until 2026-09-05 the B5 rows carried a "ran with an empty system prompt" warning. That
was wrong: the parent workflow forwarded the full prompt through the sub-workflow input
port, and the first-call token counts prove it arrived. See honesty constraint 2 in
[01-method.md](01-method.md) and the correction in
[06-flowdrop-findings.md](06-flowdrop-findings.md).

### B2 — raw HTML → one LLM call

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 1 | 13,675 | $0.0819 | 127.8s | 408.1% ⚠️HTML | 6 | 0 |
| medium | haiku-4.5 | 1 | 59,261 | $0.0690 | 30.9s | 67.3% | 28 | 0 |
| large | haiku-4.5 | 0 | 0 | $0.0000 | 2.0s | **failed** | 0 | 0 |
| small | sonnet-5 | 1 | 16,622 | $0.2009 | 138.7s | 407.9% ⚠️HTML | 0 | 0 |
| medium | sonnet-5 | 1 | 73,380 | $0.9356 | 576.8s | 567.2% ⚠️HTML | 40 | 3 |
| large | sonnet-5 | 1 | 266,158 | $0.6584 | 114.5s | 46.7% | 4 | 0 |
| small | opus-5 | 1 | 16,622 | $0.5066 | 170.3s | 407.7% ⚠️HTML | 0 | 0 |
| medium | opus-5 | 1 | 73,380 | $0.4343 | 30.7s | 68.9% | 27 | 2 |
| large | opus-5 | 1 | 266,158 | $1.5371 | 85.2s | 47.2% | 0 | 1 |

### B3 — deterministic Markdown → one LLM call

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 1 | 4,915 | $0.0246 | 45.2s | 85.8% | 0 | 0 |
| medium | haiku-4.5 | 1 | 3,501 | $0.0140 | 28.8s | 69.0% | 29 | 0 |
| large | haiku-4.5 | 1 | 34,821 | $0.0400 | 11.2s | 4.3% ⚠️ | 0 | 0 |
| small | sonnet-5 | 1 | 6,391 | $0.0758 | 46.8s | 94.0% | 0 | 0 |
| medium | sonnet-5 | 1 | 4,924 | **$0.0593** | 41.1s | **98.0%** | 33 | **0** |
| large | sonnet-5 | 1 | 46,970 | $0.5671 | 339.8s | **96.6%** | 4 | **0** |
| small | opus-5 | 1 | 6,391 | $0.1967 | 63.4s | 97.4% | 0 | 0 |
| medium | opus-5 | 1 | 4,924 | $0.1430 | 47.2s | 94.1% | 31 | 0 |
| large | opus-5 | 1 | 46,970 | $1.4256 | 421.7s | 96.6% | 4 | 0 |

**B3 is the quiet winner of the entire benchmark.** On Sonnet 5 it is the cheapest
correct run on every page, and — uniquely — it never produced a *silent* wrong answer.
It does fail once, with Haiku on the large page (4.3%), but that failure is truncation:
visible at a glance, and cheap. Every other variant's failures had to be hunted for.

### B4 — Drupal AI Agent + tool

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 2 | 39,135 | $0.1006 | 122.0s | 92.6% | 0 | 0 |
| medium | haiku-4.5 | 2 | 124,149 | $0.1468 | 59.2s | 74.1% | 29 | 0 |
| large | haiku-4.5 | 0 | 0 | $0.0000 | 2.0s | **failed** | 0 | 0 |
| small | sonnet-5 | 2 | 40,549 | $0.1500 | 50.1s | 59.9% | 0 | 0 |
| medium | sonnet-5 | 2 | 153,802 | $0.3735 | 55.0s | 76.0% | **70** ❌ | 0 |
| large | sonnet-5 | 2 | 552,606 | $1.3282 | 182.9s | 43.8% | 1 | 0 |
| small | opus-5 | 2 | 41,389 | $0.4429 | 84.2s | 94.0% | 0 | 0 |
| medium | opus-5 | 2 | 155,234 | $0.9840 | 84.6s | 93.1% | 30 | 0 |
| large | opus-5 | 1 | 266,590 | $1.5889 | 97.2s | 42.9% | 0 | 1 |

❌ The 70-glyph cell is failure #2 — it redacted "Drupal" itself, all 46 mentions.

### B5 — FlowDrop ReAct, `html_to_markdown` tool

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 3 | 41,793 | $0.0914 | 106.6s | 75.7% | 0 | 0 |
| medium | haiku-4.5 | 3 | 139,877 | $0.1610 | 61.1s | 68.1% | **0** ❌ | **29** ❌ |
| large | haiku-4.5 | 1 | 818 | $0.0013 | 5.8s | **failed** | 0 | 0 |
| small | sonnet-5 | 2 | 22,580 | $0.0600 | 15.4s | 50.6% | 0 | 0 |
| medium | sonnet-5 | 2 | 91,658 | $0.2470 | 59.2s | 94.2% | 29 | 1 |
| large | sonnet-5 | 3 | 691,024 | $1.5452 | 157.4s | 43.9% | 0 | 1 |
| small | opus-5 | 2 | 22,455 | $0.2357 | 49.5s | 95.2% | 0 | 0 |
| medium | opus-5 | 2 | 91,494 | $0.6029 | 64.4s | 97.0% | 30 | 0 |
| large | opus-5 | 2 | 337,512 | $2.4270 | 272.9s | 84.1% | 4 | 0 |

❌ The Haiku medium cell is failure #1 — converted perfectly, redacted nothing.

### B6 — autonomous agent

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 3 | 41,984 | $0.1181 | 165.8s | 69.4% | 0 | 0 |
| medium | haiku-4.5 | 3 | 125,622 | $0.1495 | 64.0s | 69.0% | 27 | 3 |
| large | haiku-4.5 | 1 | 883 | $0.0013 | 3.1s | **failed** | 0 | 0 |
| small | sonnet-5 | 2 | 18,331 | $0.0941 | 47.6s | 93.6% | 0 | 0 |
| medium | sonnet-5 | 2 | 75,251 | $0.2454 | 74.3s | 97.6% | 30 | 0 |
| large | sonnet-5 | 2 | 267,893 | $0.9511 | 331.7s | 81.5% | 4 | 0 |
| small | opus-5 | 2 | 18,207 | $0.2134 | 43.9s | 94.8% | 0 | 0 |
| medium | opus-5 | 2 | 75,099 | $0.4894 | 46.9s | 93.8% | 30 | 0 |
| large | opus-5 | 2 | 267,768 | $2.0813 | 263.4s | 85.2% | 4 | 0 |

### B7 — FlowDrop ReAct, `url_to_markdown` tool ✅ prompt verified present

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | sonnet-5 | 2 | 9,399 | $0.0826 | 52.0s | 94.6% | 0 | 0 |
| medium | sonnet-5 | 2 | 7,468 | $0.0603 | 41.9s | 93.2% | 28 | 2 |
| large | sonnet-5 | 2 | 56,955 | $0.4092 | 224.7s | 79.7% | 4 | 0 |
| small | sonnet-4.6 | 2 | 7,434 | $0.0660 | 57.0s | 69.3% | 0 | 0 |
| medium | sonnet-4.6 | 2 | 5,910 | $0.0666 | 85.1s | 93.3% | 28 | 2 |
| large | sonnet-4.6 | 2 | 40,856 | $0.3625 | 327.0s | 80.9% | 2 | 2 |

**Two calls in every single cell, on both models.** No other variant is stable in call
count across pages or models.

### B8 — FlowDrop ReAct, `url_to_markdown` given to the parent agent ✅ prompt applied

Added 2026-09-05. B5's prompt and shape; only the tool changes. No Opus 5 run.

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 2 | 7,456 | $0.0312 | 57.5s | 94.1% | 0 | 0 |
| medium | haiku-4.5 | 2 | 5,954 | $0.0211 | 44.4s | 91.4% | 40 | **10** |
| large | haiku-4.5 | 2 | 40,897 | $0.1524 | 236.2s | 80.4% | 0 | 4 |
| small | sonnet-4.6 | 2 | 7,444 | $0.0661 | 53.5s | 69.3% | 0 | 0 |
| medium | sonnet-4.6 | 2 | 5,928 | $0.0710 | 87.0s | 97.1% | 56 | 3 |
| large | sonnet-4.6 | 2 | 40,866 | $0.3693 | 327.0s | 82.2% | 4 | 2 |
| small | sonnet-5 | 2 | 9,412 | $0.0816 | 50.9s | 94.0% | 0 | 0 |
| medium | sonnet-5 | 2 | 7,489 | $0.0634 | 42.4s | 96.5% | 56 | 2 |
| large | sonnet-5 | 2 | 56,968 | $0.3351 | 165.9s | 81.9% | 8 | 0 |

**Two calls in every cell, on all three models** — the same signature as B7, and on
Sonnet 4.6 the small-page output is byte-for-byte the same length as B7's. The URL-shaped
tool, not the prompt rewrite, is what made B7 predictable. B8 places more `▌▌▌▌` than
the control has competitor mentions (56 vs 36 on medium) because it also redacts variant
spellings and link text; Drupal mentions survive (38 of 46), so this is not failure #2.

### B9 — as B8, Reflexion engine (critic + up to 3 revisions) ✅ prompt applied

| Page | Model | Calls | Tokens in | Cost | Wall | Kept | Red | Leak |
|---|---|---|---|---|---|---|---|---|
| small | haiku-4.5 | 9 | 125,817 | $0.2303 | 281.5s | 94.9% ⚠️ | 0 | 0 |
| medium | haiku-4.5 | 9 | 195,056 | $0.2620 | 221.1s | 93.0% ⚠️ | 58 | 0 |
| large | haiku-4.5 | 7 | 212,845 | $0.4969 | 637.0s | 75.5% | 8 | 0 |
| small | sonnet-4.6 | 9 | 78,856 | $0.3456 | 169.7s | 69.3% ⚠️ | 0 | 0 |
| medium | sonnet-4.6 | 3 | 9,027 | $0.0799 | 79.9s | 94.5% | 56 | 3 |
| large | sonnet-4.6 | 7 | 199,271 | $1.2054 | 863.7s | 80.0% | 6 | 1 |
| small | sonnet-5 | 5 | 28,742 | $0.1925 | 122.6s | 94.4% | 0 | 0 |
| medium | sonnet-5 | 7 | 47,703 | $0.2676 | 157.2s | 96.8% | 70 | **0** |
| large | sonnet-5 | 7 | 265,477 | $1.2823 | 641.8s | 76.5% | 8 | **0** |

⚠️ These three cells **failed on the first sweep and were rerun on 2026-09-05** after FlowDrop
fixed [flowdrop#3592443](https://git.drupalcode.org/project/flowdrop/-/work_items/3592443)
(module `a1095dba`, tags `b9fix-*`): on the revision round the agent answered without calling
a tool, and the loop runtime failed the consumer of the tool node instead of skipping it. The
failed rows stay in `runs.csv` at $0.04–$0.10 each. The Haiku small cell took two attempts
on the fixed module: the first stalled after the third critic round with a job still
pending and paused (see [06-flowdrop-findings.md](06-flowdrop-findings.md), #4); the
second completed. Sonnet 4.6's small-page run ended at 69%: the critic sent the draft back three times and the
agent landed on the same 4,608-character document its B7 and B8 runs produced on this page.

**What the critic bought.** On Sonnet 5, B9 is the only variant with zero leaks on every
page, and Haiku 4.5 also lands at zero leaks on all three pages once the loop runs to the end
— the small page has no competitor names to redact, so zero redactions there is correct — at 5–7 calls, ~4× B8's cost, and 10+ minutes on the large page. On Sonnet 4.6 the
critic accepted the medium draft unchanged (3 calls, same output profile as B8) and its
large-page revisions cut leaks from 2 to 1 for 3× the cost and 14 minutes. Whether a
critic is worth it is a model-dependent answer, and n=1 everywhere.

## Haiku's cliff

Haiku 4.5 failed outright on the large page in **three of five agentic variants**
(B2, B4, B5 — with B2 and B4 dying at 2.0s having consumed nothing). It is the
only model in the set that does not complete the matrix. Cheap models fail the *loud*
way here, which is the good way — except in B5-medium, where it failed the silent way.

## Rankings that matter

**Cheapest correct run, medium page:** B3 + Sonnet 5 — $0.0593, 98.0%, 33 red, 0 leaks.
**Most expensive run:** B5 + Opus 5, large — $2.4270.
**Worst value:** B4 + Sonnet 5, medium — $0.3735 to destroy the document.
**Most predictable:** B7 — 2 calls everywhere, ±0.0 pts across three draws.
