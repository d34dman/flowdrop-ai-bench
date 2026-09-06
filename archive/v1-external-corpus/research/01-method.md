# Benchmark method

## The task

Every variant performs the identical job:

> Fetch a URL, convert the content to Markdown, and redact every competitor of Drupal CMS
> by replacing the name with `▌▌▌▌`.

It was chosen because it has three properties a talk needs: the correct answer is
*checkable* (did the competitor names disappear?), the failure is *gradable* (how much of
the document survived?), and it is boring enough that nobody argues about prompt quality.

## The three input pages

| Key | URL | Raw HTML | Control, de-noised | Competitor mentions | "Drupal" mentions |
|---|---|---|---|---|---|
| `small` | <https://www.drupal.org/about> | ~38 KB | 6,648 B | **0** | — |
| `medium` | <https://www.ibm.com/think/topics/drupal-wordpress> | ~164 KB | 12,550 B | **36** | 46 |
| `large` | <https://en.wikipedia.org/wiki/Drupal> | ~535 KB | 50,082 B | **5** | — |

The small page has nothing to redact. That is deliberate — it is the **false-positive
control**, and it is the page on which the worst failure in the whole dataset shows up.

## The ten variants

| ID | Workflow | Architecture | Agency |
|---|---|---|---|
| **B0** | `bench_0_floor` | Empty pipeline, no LLM | none — measures FlowDrop overhead |
| **B1** | `bench_1_reference` | Deterministic fetch + convert, no LLM | none — **produces the control document** |
| **B2** | `bench_2_raw_html_llm` | Raw HTML → one LLM call | low |
| **B3** | `bench_3_markdown_llm` | Deterministic HTML→Markdown → one LLM call | low |
| **B4** | `bench_4_ai_agent_tool` | Drupal `ai_agents` agent with a tool | medium |
| **B5** | `bench_5_react_agent` | FlowDrop ReAct agent, `html_to_markdown` tool | high |
| **B6** | `bench_6_agent_autonomous` | Autonomous agent | high |
| **B7** | `bench_7_react_optimized` | FlowDrop ReAct agent, **`url_to_markdown` tool** | high |
| **B8** | `bench_8_react_with_tools_in_parent` | B5's shape and prompt; the **parent** agent is handed `url_to_markdown` | high |
| **B9** | `bench_9_reflexion_with_tools_in_parent` | As B8, on a **Reflexion** engine: a critic reviews the answer, up to 3 revisions | high |

B7 was built during the research, in the FlowDrop UI, after B5's failure mode was
understood — workflow `react_agent_with_optimized_tools`.

B8 and B9 were added on 2026-09-05 on the new `react_agent_engine` and
`reflexion_agent_engine` sub-workflows. B8 isolates the tool-shape fix from B7's prompt
change; B9 asks whether a critic loop buys anything a single pass does not. They ran on
Haiku 4.5, Sonnet 4.6 and Sonnet 5 in this report; the Opus 5 cells were run later on
2026-09-05 and appear only in [report v2](../v2/README.md). B9 failed on three of nine cells
inside FlowDrop's loop runtime; FlowDrop fixed it the same day and the three cells were
rerun on the fixed module (see [06-flowdrop-findings.md](06-flowdrop-findings.md), #4).

## Models

`claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-sonnet-5`, `claude-opus-5`, through
Drupal's `ai_provider_anthropic`.

## Environment

FlowDrop 2.4.2 · Drupal 11.4.5 · PHP 8.3 · orchestrator `flowdrop_runtime:synchronous`
· DDEV. Costs are **metered, not estimated**: each run is tagged `aim_context:<uuid>`
and the spend is read back from `ai_metering_usage.context_id`.

## The metrics, and what they can't tell you

**Retention (`kept`)** — output bytes ÷ control bytes, after identical de-noising of both
sides: `](…)` link targets stripped, `![…]` alt blocks removed, whitespace collapsed.
The de-noising matters enormously: before it, the control on the medium page was 59%
link markup, so a model that produced clean prose scored as if it had lost half the
document. B3-large moved from 46% to 84% on this correction alone.

> **What it cannot do:** distinguish a faithful reproduction from fluent invented prose of
> the same length. A model that rewrites the document in its own words scores ~100%.
> Retention is a *floor* on damage, not a measure of fidelity.

**Redactions (`red`)** — count of `▌▌▌▌` in the output.
**Leaks (`leak`)** — competitor names still readable, matched word-boundary
case-insensitively against a fixed list (WordPress, Joomla, TYPO3, Sitecore, Contentful,
Wix, Squarespace, Magento, Umbraco, Mambo, Backdrop, Optimizely, Episerver, Kentico,
Plone).

> **What it cannot do:** notice *over*-redaction. A run that redacts the word "Drupal"
> scores zero leaks and a high redaction count. This is exactly what happened in the
> worst run in the dataset, and the metric called it a success. See
> [03-failure-gallery.md](03-failure-gallery.md), failure #2.

**Calls** — LLM round-trips the loop used. **Cost / wall** — metered and measured.

## Honesty constraints to state on stage

1. **Mostly n=1.** Only the small page has n=3, and only for B5/B7. A single B5 draw of
   one cell landed at 51%, 71% and 95% on three attempts — so treat every single-draw
   number as one sample from a distribution whose width is unknown.
2. **The first three B7 runs executed with an empty system prompt** because of a
   FlowDrop bug found mid-research (see
   [06-flowdrop-findings.md](06-flowdrop-findings.md)). They are marked, not deleted.
   **B5 was wrongly given the same marking until 2026-09-05.** Its parent workflow
   forwards the system prompt into the sub-workflow's `system_prompt` input port, which
   lands on the Reason node as a non-empty runtime input — so the exposed port carried the
   full prompt rather than shadowing it. Every B5 sub-pipeline's stored initial data holds
   the 489-character prompt, and the first-call input token count is identical before and
   after the port fix (754 / 766 / 763 on Sonnet 5 for small / medium / large). B5's
   fidelity numbers are valid.
   *Assumed but not exhaustively verified:* B2/B3/B4/B6 use different node types and were
   not affected.
3. **Retention above 100% means the run did not produce Markdown at all** — see failure
   #3. Do not present those cells as "better than the control".
