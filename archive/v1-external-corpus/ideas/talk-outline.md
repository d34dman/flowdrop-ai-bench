# A 45-minute plan

Seven decisions in 45 minutes is ~5 minutes each, which is not enough to also present a
benchmark. **So don't present the benchmark.** Thread its numbers through the decisions,
and reuse one chart three times rather than showing seven.

## Shape

```
00:00  Cold open — the failure that scored best          4 min
04:00  Why this is hard to see: the harness              4 min
08:00  Decisions 1–7, evidence-backed                   28 min
36:00  What I'd do differently / what's still broken     5 min
41:00  Q&A                                               4 min
```

---

## 00:00 — Cold open (4 min)

Put the B4/Sonnet 5 medium output on screen with no preamble:

```
▌▌▌▌ versus ▌▌▌▌

▌▌▌▌ and ▌▌▌▌ are among the most popular content management system…
```

Ask the room what went wrong. Then reveal: the page is *"Drupal versus WordPress"*, and
the agent put a mark on **"Drupal" 37 times** — the one thing it was told to keep. Not one
mention survived. Then reveal the second half: **the v1 metrics scored this run as a success.**
Zero leaks, highest redaction count in the table. Under rubric v2 it is the worst graded run
in the dataset: subject preservation 0.26, precision 0.41.

> *"This is what hallucination actually looks like in production. Not a made-up API. A
> correct rule, applied confidently to the wrong entity, passing every check I had
> written."*

That is the title, the thesis, and the stakes, in four minutes, with a real artifact.

## 04:00 — The harness (4 min)

Briefly: one task, eight architectures, four models, three page sizes, metered costs, a
deterministic control document to grade against. Two slides maximum.

The number that buys credibility and pre-empts the framework objection:
**FlowDrop's own orchestration overhead is 24 ms median.** Everything after this is the
model, not the framework.

Then the honesty slide — put it early, not in the footnotes:
- mostly n=1
- the first rubric counted bytes and marks, and both were fooled by the same run; the report
  was re-graded against gold documents (v2) and one of the four named failures was withdrawn
- three early draws of one arm ran with an erased prompt and I didn't notice for hours

## 08:00 — The seven decisions (28 min, ~4 min each)

| Decision | Evidence to show | The number |
|---|---|---|
| **1. Output format / token economy** | B5 vs B7 tool shape — **the anchor chart** | 18.5× tokens, 6× cost, 0 quality cost |
| **2. Reduce context** | B3 pre-conversion; B7 input flat vs page size | 73,380 → 4,924 input tokens |
| **3. Injection & gates** | The seven silent failures; the heading blind spot | 7 of 116 graded runs said `completed` and were wrong; a two-second deterministic check against a gold document catches every one |
| **4. Predictable IDs** | Call count | B7 = 2 calls on every page, both models |
| **5. Atomic & reversible** | Memory cliff; Haiku's loud deaths | answer completed, then lost |
| **6. Failure patterns in prompts** | The shadowed prompt | 338 tokens = 64 points |
| **7. Dogfooding** | B7 built in the UI, beat the hand-built one | $2.91 vs $0.55 |

**Reuse the anchor chart.** The B5/B7 three-draw dot plot appears at decision 1
(variance), gets called back at decision 4 (call count), and again at decision 6 (prompt
present vs absent). The audience learns to read one chart instead of seven.

### Decision 3 needs care

You have gates, not injection. Either run the injection probe first
([open-questions.md](open-questions.md) #1) or reframe the slide honestly as *"the gate is
the part I have data for"* — and state the untested prediction explicitly: **server-side
fetching is not an injection defense, because the hostile text still arrives.**

## 36:00 — What's still broken (5 min)

Strongest possible ending for a Drupal audience — three real issues, filed, with numbers:

1. **[flowdrop#3592438](https://git.drupalcode.org/project/flowdrop/-/work_items/3592438)** —
   exposed-but-unconnected port shadows config. A `array_key_exists` vs `!== NULL` bug that
   presents as "the AI is unreliable."
2. **[flowdrop#3592437](https://git.drupalcode.org/project/flowdrop/-/work_items/3592437)** —
   ReAct loop re-sends the transcript uncached.
3. **[ai_provider_anthropic#3607961](https://git.drupalcode.org/project/ai_provider_anthropic/-/work_items/3607961)** —
   prompt caching is *unreachable*, not unused: the module speaks the OpenAI-compatible
   endpoint, which silently drops `cache_control`. Worth 13% here; no module-level patch
   is possible.

Close on the honest hierarchy: **structure (83%) → caching (13%) → model choice**, in that
order.

---

## Alternative cold open, if you prefer the quieter one

The B5/Haiku medium run: clean Markdown, normal cost, normal latency, `completed`,
68% retention — and **zero redactions with all 29 competitor mentions intact.** Ask the
room which dashboard would have caught it. Answer: none of them.

Use this one if the audience skews ops; use the Drupal-redaction one if it skews
developers. The Drupal one is funnier and lands harder.

## Things to cut if you're over time

- The full model matrix — one table, referenced, not walked through
- Pricing tables — put them in the repo, not on a slide
- Cross-model B7 verification — one sentence, not a chart

## Demo risk

If you demo live, demo **B3**, not an agent — it is one call and 41 seconds on the medium
page. Agentic runs took 30–580 seconds and one in six failed. Better: pre-record, and
show the recording while narrating the cost meter.
