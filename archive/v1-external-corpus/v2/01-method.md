# Method

The task, the pages, the variants and the environment are unchanged from v1
([`../research/01-method.md`](../research/01-method.md)); they are restated briefly so this
folder reads on its own. What is new is section 3 onward: the gold documents and the rubric.

## 1. The task

> Fetch a URL, convert the content to Markdown, and redact every competitor of Drupal CMS
> by replacing the name with `▌▌▌▌`.

## 2. Pages, variants, models

| Key | URL | Role |
|---|---|---|
| `small` | drupal.org/about | **False-positive control**: no competitor is named |
| `medium` | ibm.com/think/topics/drupal-wordpress | The only page with targets **and** a protected subject |
| `large` | en.wikipedia.org/wiki/Drupal | Fidelity and cost at 20 KB of body; one neutral mention (Backdrop) |

| ID | Architecture | Agency |
|---|---|---|
| B2 | raw HTML → one LLM call | low |
| B3 | deterministic HTML→Markdown → one LLM call | low |
| B4 | Drupal `ai_agents` agent with a tool | medium |
| B5 | FlowDrop ReAct agent, `html_to_markdown(content)` tool | high |
| B6 | autonomous agent | high |
| B7 | FlowDrop ReAct agent, `url_to_markdown(url)` tool, rewritten prompt | high |
| B8 | B5's prompt and shape, parent agent given `url_to_markdown` | high |
| B9 | As B8 on a Reflexion engine: critic, up to 3 revisions | high |

B0 (empty pipeline) and B1 (deterministic fetch + convert) are the floor and the source of
the gold documents; they are not graded. B5a shared B5's sub-workflow and was dropped from
the report on 2026-09-05; its rows stay in the ledger.

Models: Haiku 4.5, Sonnet 4.6, Sonnet 5, Opus 5, via `ai_provider_anthropic`. B7 ran on
the two Sonnets only. B8/B9 on Opus 5 were run on 2026-09-05 and folded into this report.

Environment: FlowDrop 2.4.2 · Drupal 11.4.5 · PHP 8.3 · DDEV. Cost is metered per run
from `ai_metering_usage`, not estimated.

## 3. Gold documents

Per page, committed under [`../data/gold/`](../data/gold/) and rebuilt by `build_gold.py`
from the B1 conversion:

- `<page>.md`: the article body. Navigation, cookie banners, footers, sidebars, promo
  blocks, the Wikipedia infobox and References are removed as **explicit line ranges with
  a stated reason**, so every cut is reviewable. Link targets, images, citation markers and
  `[edit]` links are dropped; whitespace is collapsed.
- `<page>.targets.json`: every competitor mention in the body. A mention is
  `\bName[\w.-]*`, case-sensitive, so `WordPress.com` counts once and `drupal-wordpress`
  inside a URL does not.
- `<page>.protected.json`: every mention that must survive: `Drupal`, and the other proper
  nouns in the body (IBM, PHP, MySQL, Linux, Apache on medium; PHP, Twig, Symfony,
  Microsoft on large).

| Page | Gold bytes | Control bytes | Headings | Targets | Drupal | Other protected |
|---|---|---|---|---|---|---|
| small | 3,212 | 16,240 | 7 | **0** | 25 | — |
| medium | 8,715 | 14,497 | 9 | **30** | 38 | 7 |
| large | 20,583 | 101,790 | 19 | **0** (+1 neutral) | 154 | 16 |

Backdrop CMS, the one competitor-ish name in the large body, is `AMBIGUOUS`: a mark on it
is neither correct nor wrong, and the name left readable is not a leak.

Not yet done: a by-eye read of the three gold bodies against the live pages. The cuts were
checked line by line against the control, not against the browser rendering.

## 4. Rubric v2

All deterministic. The output is unfenced, canonicalised like the gold, split into
sentences and headings; `▌+` is one redaction mark and a wildcard token in matching.

### Gates, in order

| Gate | Test |
|---|---|
| G0 Delivered | status `completed` and ≥ 500 chars of output |
| G1 Format | HTML tag density ≤ 5 per 1,000 chars, and at least one Markdown heading |
| G2 In scope | ≥ 50 % of the gold headings present |

### Graded axes, 0–1

| Axis | Definition | Catches |
|---|---|---|
| **recall** | correct marks ÷ (correct marks + leaks). A leak is a target name still readable in gold or invented text; names left in retained chrome are counted separately and do not count | redacting nothing |
| **precision** | correct marks ÷ marks placed on gold or invented text. Marks on retained chrome (e.g. Wikipedia citations) are excluded | redacting the subject; marks on invented text |
| **subject** | protected names kept ÷ (kept + marks placed on protected names) | redacting "Drupal" |
| **fidelity** | gold sentences (≥ 4 words) found in the output at ≥ 0.90 similarity, redaction-tolerant ÷ gold sentences | truncation, dropped sections |
| **fabrication** | output sentences found neither in the gold nor anywhere in the full page ÷ output sentences. **The hallucination metric** | invented prose, the agent's reasoning in the document |
| **structure** | gold headings found ÷ gold headings (feeds G2) | flattened or reordered documents |

### Outcome class

| Class | Rule |
|---|---|
| **correct** | all gates pass; recall ≥ 0.95, precision ≥ 0.95, subject ≥ 0.95, fidelity ≥ 0.95, fabrication ≤ 0.05 |
| **degraded** | all gates pass; every axis ≥ 0.75, not correct. Visible on inspection, usable with a fix |
| **silent** | all gates pass, or G2 fails, and some axis < 0.75. The pipeline said success; the document is wrong |
| **format** | G0 passes, G1 fails: HTML came back |
| **loud** | G0 fails: nothing delivered |

A run with status `paused` (stalled on a confirmation gate or a pending job) has no answer
to grade. It stays in the ledger with its cost and is excluded from class counts, listed.

No composite score. Class first, then axes, then cost.

### What is reported alongside, never blended

Cost, wall, calls, tokens, as metered. **Cost per correct run** = cell spend ÷ correct
draws, undefined when zero. Stability only where n ≥ 3, as min–max.

### What the scorer cannot do

Sentence matching is fuzzy. A heavily paraphrased sentence counts as missing (fidelity)
or invented (fabrication). Runs that keep chrome carry a fabrication floor around 1 %
(reformatted promo lines, the release table the converter flattens), well inside the
0.05 threshold. Spot-check with `--explain` before quoting a single cell. An LLM judge was
considered and deliberately not used: a judge grading a talk about hallucination is a
joke the audience makes first.

## 5. Honesty constraints

1. **Mostly n = 1.** The class matrix shows draws, not rates. Five cells have n ≥ 3.
2. **The first three B7 draws ran with an empty system prompt** (flowdrop#3592438) and
   are excluded. B5 was wrongly given the same mark until 2026-09-05; its parent forwarded
   the prompt and its rows are in.
3. **Thresholds are the rubric proposal, with fidelity tightened from 0.90 to 0.95 on
   2026-09-05.** No graded run changed class; the lowest fidelity among correct runs is 0.965. `degraded` on the medium page is
   almost always recall 0.90–0.93: two or three of 30 WordPress mentions left readable.
4. **Total spend is $61.39 over 203 runs.** Nothing was rerun for this report.
