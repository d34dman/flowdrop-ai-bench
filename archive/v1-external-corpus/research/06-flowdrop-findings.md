# What broke in FlowDrop itself

Four bugs found while running the benchmark, all filed upstream. These are the most
*Drupal-specific* material in the research and the best fit for a DrupalCon audience —
they are ordinary Drupal plugin/config bugs whose symptom is "the AI is unreliable."

---

## 1. An exposed-but-unconnected port silently erases your system prompt

**[flowdrop#3592438](https://git.drupalcode.org/project/flowdrop/-/work_items/3592438)**

### Symptom

The first three B7 draws ran with **no system prompt at all**. Nothing errored. The runs
completed, produced clean Markdown, cost normal money, and returned ~30% of the document
instead of ~95%. It looked exactly like "the model isn't good enough at this task."

### Cause

A FlowDrop node port can be `exposed` (connectable from another node). `ParameterResolver`
resolves precedence as:

```
runtime input (connectable + exposed)  →  workflow config  →  schema default
```

…gated on **`array_key_exists`** — presence, not emptiness. An exposed port with **no
incoming connection** resolves to an empty value, which is *present*, so it wins over the
node's configured `systemPrompt` and shadows it.

The node type does declare `system_prompt` under `parameters` — so this is a genuine
resolution bug, not a wiring mistake by the user.

### Fix

Both steps are required — setting the config alone does nothing:

```php
$n['data']['config']['systemPrompt'] = $prompt;
foreach ($n['data']['config']['ports']['inputs'] as &$p) {
  if (($p['id'] ?? '') === 'systemPrompt') { $p['exposed'] = FALSE; }
}
```

Suggested upstream fix at `WorkflowNode.php:523` — test `$params->get($name) !== NULL`
rather than `has()`.

### Measured impact

Identical workflow, same model, same page:

| | Input tokens | Retention |
|---|---|---|
| Prompt shadowed | 9,061 | **30.6 / 30.0 / 28.0%** |
| Prompt applied | 9,399 | **94.6 / 94.6 / 94.6%** |

**338 tokens of system prompt were worth 64 points of fidelity.** The 338-token delta is
also the only externally visible sign that anything was wrong.

### Correction (2026-09-05): B5 was not affected

B5 was marked as shadowed alongside B7 because it used the same exposed port. It was not.
B5's parent workflow sets `system_prompt` on the sub-workflow node, the sub-workflow
declares that as an input port wired to the Reason node's `systemPrompt`, and the runtime
merges that node-keyed initial data into the node's runtime inputs. The exposed port was
therefore *non-empty*: it carried the parent's prompt, and there was nothing to shadow.
B7's parent forwarded only `message`, which is why the bug bit B7 and not B5.

Verified from the local database: every B5 (and B5a) sub-pipeline's initial data holds
the 489-character prompt, and the first LLM call's input tokens are identical with the
port exposed and with it closed (Sonnet 5: 754 / 766 / 763 for small / medium / large).
The `prompt_shadowed` flag in `data/runs.csv` is now 0 for B5 and B5a. The lesson in the
next section holds with extra force: the marker test would have caught this too, had it
been run on B5 rather than assumed from B7.

### Why this belongs in the talk

It is a perfect worked example for **learning objective 6** (encode failure patterns) and
a cautionary tale for the whole thesis: *the research nearly concluded that an
architecture didn't work, when in fact the config layer had eaten the instructions.*
When an agent underperforms, verify the prompt physically arrived before you tune it.

**Diagnostic technique worth showing:** inject a nonsense marker (`QQZZX9`, `BANANA`)
into the system prompt and assert it appears in the model's behaviour. A prompt you cannot
prove arrived is a prompt you are not testing. An earlier conclusion in this research —
"setting `systemPrompt` fixed it, 51% → 93%" — was **wrong**, and only the marker test
exposed it; the 93% was ordinary variance.

---

## 2. The ReAct loop re-sends its transcript uncached

**[flowdrop#3592437](https://git.drupalcode.org/project/flowdrop/-/work_items/3592437)**

Each iteration re-sends the whole conversation. 30% of all input tokens in the dataset are
verbatim repeats. Combined with finding #3 in
[05-cost-and-caching.md](05-cost-and-caching.md), those repeats cannot be cached at all
through the current provider.

---

## 3. Pipeline memory ceiling — a non-atomic failure

**Patch: `flowdrop-memory-configurable-max-value-bytes.patch` (1 MB → 10 MB)**

On the large page, a model that produces a long faithful answer overflows FlowDrop's
pipeline-memory buffer **after the answer is complete**. The run then delivers nothing.

This is the abstract's *"half-applied state changes"* pattern, in the wild: the expensive
work succeeded, and the result was lost at the storage boundary. It is also an argument
for **learning objective 5** (atomic and reversible) that costs $1.90 to demonstrate —
Sonnet 4.6's large-page cell simply does not exist without the patch.

Any model pushing a long answer through this loop sits near the same cliff. **The fix is
the patch, not the model choice.**

---

## 4. A skipped tool branch fails a re-entered loop instead of skipping downstream

**[flowdrop#3592443](https://git.drupalcode.org/project/flowdrop/-/work_items/3592443)** · found 2026-09-05 · **fixed upstream the same day** (`872ca8d9`, in `a1095dba`)

### Symptom

B9's Reflexion engine failed on 3 of 9 cells (Haiku small + medium, Sonnet 4.6 small) on
module `41779a34`:

```
Job 4862 failed: port 'value' cannot be satisfied in round 2 — its only in-loop source
'flowdrop_node_processor_tool_invoke.1' can no longer produce a value for this round
```

The agent had already written its revised answer. Nothing was emitted.

### Cause

When the critic sends the answer back, the loop re-enters and the agent usually revises
*without* calling a tool — it already has the page. The has-tool-calls gateway routes away
from `tool_invoke`, so the gateway that reads its `executed_any` output has an idle
round-2 job whose only source completed in round 1. Clause 2 of the per-iteration
staleness barrier (`JobGenerationService::getUnsatisfiableJobs()`) reads that as "value
exists but from the wrong round" and fails the job. It has no error edge, so the
sub-workflow fails, then the parent.

The method's own docblock says a source that a gateway routed away from means the
consumer "was not meant to run" and must terminate through the BR-7 skip sweep, not a
failure. The restriction meant to keep Clause 2 narrow looks at the source's *newest
completed* job — the round-1 one — so it cannot tell "skipped this round" from
"round-behind". A secondary bug: the message fell back to the degraded wording instead
of naming the gateway that routed away.

### Why it matters

Whether a run succeeds is decided by whether the model happens to call a tool on the
revision round. Sonnet 5 always did, so it completed 9/9; Haiku and Sonnet 4.6 did not.
A plain ReAct engine (B8) never hits it because the loop exits on the first no-tool
round. Any critic / reflexion / retry pattern built on FlowDrop loops does.

### After the fix

All three cells were rerun on `a1095dba` (tags `b9fix-*`) and completed: Sonnet 4.6 small
in 170s, Haiku medium in 221s, Haiku small in 281s. One wrinkle: the **first** Haiku small
attempt on the fixed module ended `paused`, not `completed`. Its Reflexion sub-pipeline
ran seven reason rounds and three critic rounds, then stopped scheduling while
`Max revisions reached? #3` was already `pending`, and logged
`paused on unknown budget with ready jobs remaining` — neither the 100-iteration cap (67
used) nor a time budget had fired, and no job failed. The parent marked the sub-workflow
node `interrupted` and paused too. The identical cell completed on the next attempt, so it
looks intermittent and is not yet understood or filed.

### Two harness-side traps found the same day, not bugs

- The new workflows declared the **asynchronous orchestrator**; `launch.php` cannot
  `wait` on that and every cell errored in 0.1s. Pin `flowdrop_runtime:synchronous`.
- B8 ended in both a `chat_output` and a `text_output` capped at **1,000 characters**;
  the collector took the last output node and silently kept the truncated copy. Five of
  six B8 cells read as 2–11% retention until `collect.php` was changed to keep the
  longest output. Same class of error as the failure gallery: a plausible number, no
  error attached.

---

## Also worth a mention

- **`url_to_markdown` raises a `schema_form` interrupt** unless the node sets
  `requiresConfirmation: 'waive'`, which pauses headless runs indefinitely
  (`scratchpad/bench/waive_utm.php`). A human-in-the-loop default that becomes a hang in
  automation.
- **Bench workflows are now in `config/sync`** (commits 7e51e62, 9c8b9f6) — the
  reproducibility risk flagged in [ideas/open-questions.md](../ideas/open-questions.md)
  is closed.
