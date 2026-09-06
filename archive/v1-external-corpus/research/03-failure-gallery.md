# The failure gallery

Four failure modes, all observed on the **same task**, most on the **same page**. This is
the spine of the talk: the abstract names four failure patterns, and the benchmark
produced four — but they are not quite the ones you would guess, and **every one of them
is silent.**

---

## Failure 1 — It did nothing, and every signal said it worked

**B5 ReAct agent · Haiku 4.5 · medium page**

| Signal | Reading | Verdict |
|---|---|---|
| Pipeline status | `completed` | ✅ |
| Output format | clean Markdown | ✅ |
| Retention | 68.1% | ✅ normal |
| Wall clock | 61.1s | ✅ normal |
| Cost | $0.1610 | ✅ normal |
| **Redactions placed** | **0** | ❌ |
| **Competitor mentions left readable** | **29** | ❌ |

The run converted the document perfectly and **did not redact anything**. Every health
check short of reading the output says it succeeded. In production this ships a document
that was never redacted, to whoever asked for a redacted document.

> **The lesson:** "the pipeline completed" is not a quality signal. The only signal that
> caught this was an assertion about the *content* — a validation gate.

Compare with the same model, same page, one architecture down (B3): 29 redactions,
0 leaks, $0.0140.

---

## Failure 2 — It redacted the subject of the document

**B4 Drupal AI Agent + tool · Sonnet 5 · medium page**

The medium page is IBM's *"Drupal versus WordPress"*. The control contains **46 mentions
of "Drupal"** and 36 of "WordPress". The output begins:

```
▌▌▌▌ versus ▌▌▌▌# ▌▌▌▌ versus ▌▌▌▌

## ▌▌▌▌ versus ▌▌▌▌

▌▌▌▌ and ▌▌▌▌ are among the most popular content management system (CMS) platforms…
```

**Mentions of "Drupal" surviving in the output: 0.** It placed 70 redaction marks against
36 actual competitor mentions, having decided that the thing it was told to protect was
also a thing to hide.

Every other cell on that page kept 37–41 Drupal mentions:

| Variant | Model | Drupal kept | WordPress leaked | Glyphs |
|---|---|---|---|---|
| B3 markdown → LLM | sonnet-5 | 41 | 0 | 33 |
| B3 markdown → LLM | opus-5 | 39 | 0 | 31 |
| B5 ReAct | opus-5 | 38 | 0 | 30 |
| B6 autonomous | sonnet-5 | 38 | 0 | 30 |
| **B4 agent + tool** | **sonnet-5** | **0** | 0 | **70** |

> **The lesson:** this is the closest thing in the dataset to the abstract's *"hallucinated
> field names"* — the agent applied a correct rule to the wrong entity, confidently and
> consistently, across the whole document. And **the metrics scored it as a success**:
> zero leaks, highest redaction count in the table. An eval that only counts what should
> be absent will rank this run first.

**This is the slide that earns the talk title.**

---

## Failure 3 — It ignored the output format and handed back the input

**B2 raw HTML → LLM · all models · small and medium pages**

The small-page output opens:

````
```html

<html xml:lang="en" version="XHTML+RDFa 1.0" dir="ltr" …
````

27,896 bytes, **832 HTML tags**, 0 redactions. The model echoed its input back, wrapped in
a fenced code block. Retention scored **408%** — because the metric divides by a Markdown
control, and raw HTML is four times the size.

On the medium page Sonnet 5 did something subtler and worse: it returned **HTML, but
correctly redacted** — 518 tags, 40 glyphs, 567% retention. It did the hard half of the
job and silently refused the easy half.

> **The lesson:** a metric with no format assertion will report your worst runs as your
> best. Any retention figure over ~110% in this dataset is a format failure, not quality.
> The detector is one line: HTML tag density > 5 per 1,000 characters.

---

## Failure 4 — It rewrote the document instead of reproducing it

**B5 ReAct agent · Sonnet 5 · small page · three identical draws**

Same model, same prompt, same page, three runs:

| Draw | Chars | Retention | Cost | Calls |
|---|---|---|---|---|
| 1 | 5,818 | 70.5% | $0.1925 | 3 |
| 2 | 8,318 | 95.1% | $0.2712 | 3 |
| 3 | 3,721 | 50.6% | $0.1345 | 3 |

Half the document silently disappeared, or didn't, depending on the draw. There is no
error, no warning, and no way to tell from outside which draw you got.

The cause is architectural, not statistical — see [04-tool-shape.md](04-tool-shape.md).
B5's tool takes the page *content* as an argument, so the model must **regenerate the
entire document as output tokens** to call it. That is reconstruction, not copying.

The same three draws through B7, whose tool takes a **URL**:

| Draw | Chars | Retention | Cost | Calls |
|---|---|---|---|---|
| 1 | 8,715 | 94.6% | $0.0820 | 2 |
| 2 | 8,715 | 94.6% | $0.0824 | 2 |
| 3 | 8,716 | 94.6% | $0.0826 | 2 |

> **The lesson:** if the document has to travel through the model's output channel, how
> much of it survives is a coin flip. Take it out of the output channel and the variance
> disappears. **This is the same insight as "DSL over JSON" from learning objective 1**,
> measured on a different payload.

---

## The pattern behind all four

| # | What happened | What the metrics said | What caught it |
|---|---|---|---|
| 1 | Redacted nothing | completed, 68% retention | leak count |
| 2 | Redacted the subject | completed, **best** redaction score | "Drupal" count — a check nobody wrote in advance |
| 3 | Returned HTML | completed, 408% retention | format assertion |
| 4 | Dropped half the text | completed, 51% retention | a control document |

**Nothing failed loudly.** Four different architectures, four different silent wrong
answers, and in three of the four cases the metric that was supposed to catch problems
reported success. The engineering lesson is not "pick a better model" — it is that
**agentic correctness is only observable against a control**, and you have to decide in
advance what "wrong" looks like.
