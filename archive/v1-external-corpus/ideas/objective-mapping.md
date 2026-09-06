# The seven learning objectives ↔ the evidence

Your abstract commits to seven decisions. Here is what today's data can actually back,
what it can't, and the honest strength of each claim.

| # | Objective | Evidence | Strength |
|---|---|---|---|
| 1 | Output format (DSL vs JSON), token economy, atomicity | B5 vs B7 tool shape | **Strong** |
| 2 | Reduce context; separate LLM needs from system storage | B7 input flat vs page size; B3 pre-conversion | **Strong** |
| 3 | Prompt-injection defenses (XML wrapping, validation gates) | *gates only, no injection data* | **Half** |
| 4 | Predictable identifiers, multi-step planning without round-trips | Call count pinned at 2 | **Strong** |
| 5 | Atomic and reversible actions | Memory-ceiling cliff | Partial |
| 6 | Encode failure patterns into system prompts | Prompt-shadowing bug, measured | **Strong** |
| 7 | Dogfood agents through the platform | B7 built in the FlowDrop UI; 3 issues filed | Good |

---

## 1 — Output format and token economy · **Strong**

The B5/B7 comparison is the same argument as DSL-over-JSON, on a different payload: every
token the model must *emit* is a token it can get wrong, and is billed at 5×.

- 18.5× input tokens, 6.0× cost, large page
- Retention spread across three identical draws: **44.5 points (B5) vs 0.0 (B7)**
- Atomicity: B7 is 2 calls always; B5's count is model-dependent

**Line for the slide:** *"A tool that takes content makes the model your transport layer.
A tool that takes a handle makes it your planner. Only one of those is what you're paying
for."*

## 2 — Reduce context · **Strong**

B7's input tokens barely track page size: 9,399 / 7,468 / 56,955 across 38 KB / 164 KB /
535 KB. B3 makes the same point one layer down — deterministic HTML→Markdown *before* the
model cuts medium-page input from 73,380 (B2) to 4,924, and it is the cheapest correct
run on the small and medium pages (on Haiku, $0.014 for medium under rubric v2).

**Line for the slide:** *"The cheapest token is the one you converted before the model saw
it."*

## 3 — Prompt injection · **HALF. Do not overclaim.**

**There is no injection experiment in this dataset.** Say so, or run one
([open-questions.md](open-questions.md) #1, ~$0.20).

The *validation gate* half is very well covered, and it is the stronger half anyway —
[failure gallery](../research/03-failure-gallery.md) #1 and #2 are exactly "the model
reported success and the output was wrong." Three of four failure modes were caught only
by an assertion about content.

**Line for the slide:** *"'Completed' is a scheduler status, not a quality signal."*

⚠️ A prediction worth stating and then testing rather than asserting: B7's server-side
fetch does **not** protect against injection — the hostile text still lands in context.
Tool shape is not an injection defense.

## 4 — Predictable identifiers, no round-trips · **Strong**

Call count is the metric. B7: **2 on every page, on both Sonnet 5 and Sonnet 4.6.**
B5: 3, 2, 4 — and its count moves with the model. A plan that can name its targets in
advance doesn't need a lookup turn; the benchmark measures the same property from outside.

## 5 — Atomic and reversible · Partial

One good anecdote: the pipeline-memory cliff, where the answer completes and *then* the
buffer overflows, delivering nothing. Textbook half-applied state — and it cost $1.90 to
hit.

Also usable: Haiku failing outright on the large page in four of six agentic variants,
at 2.0–5.8s having consumed almost nothing. **Loud failure is cheap; silent failure is
expensive.** That contrast is worth a slide on its own.

## 6 — Encode failure patterns into prompts · **Strong**

The inverse proof is better than the direct one: when the prompt was silently erased, the
runs still *looked* fine and returned 30% of the document. Prompt present → 94.6%.
**338 tokens = 64 points of fidelity.**

Also here: the marker-injection technique (`BANANA` test) for proving a prompt physically
arrived — and the fact that this research reached a **wrong conclusion** without it. That
admission will land better than any assertion.

## 7 — Dogfooding · Good

B7 was built in the FlowDrop UI as an ordinary user would, then benchmarked against the
hand-built variant, and won on every axis. Three issues filed upstream from findings the
benchmark produced. The benchmark harness is itself FlowDrop workflows.

---

## The three claims to lead with

1. **The variant with the least agency almost never failed silently.** B3 — deterministic
   conversion plus one LLM call — is correct in 15 of 16 graded runs and the cheapest correct
   run on the small and medium pages. Its one failure (Haiku, large page) is a truncation to
   8 % of the document that the pipeline still reported as `completed`; rubric v2 classes it
   silent, because nothing but a length check would have caught it. Six of the seven silent
   failures came from a *more* agentic design.
2. **Every failure that mattered was silent**, and in three of four cases the metric
   reported success.
3. **Architecture is a bigger lever than model choice**: 16× cost spread across variants
   on one page and one model, versus 12× across models — and the architecture lever
   doesn't trade away correctness.

## The one to be careful with

B5a (the "naive prompt" arm) was dropped from the report on 2026-09-05: it shared a
sub-workflow with B5, so it was never a clean prompt-quality contrast. The prompt-quality
evidence you *do* have is the shadowing bug in objective 6, which is stronger anyway.
