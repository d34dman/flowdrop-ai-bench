# The failure gallery, re-graded

v1 named four failures and found them by reading. v2 asks, for each, which axis catches it
without a reader, and then adds the two that only the new axes could see. All six are
`silent` or would have been: the pipeline reported `completed`.

| # | Failure | Cell | v1 metric that flagged it | v2 axis that catches it |
|---|---|---|---|---|
| 1 | Redacted nothing | B5 · Haiku · medium | leak count (29) | **recall 0.0** |
| 2 | Redacted the subject | B4 · Sonnet 5 · medium | none; scored best | **subject 0.26**, precision 0.41 |
| 3 | Returned HTML | B2 · small, all models; B2 · Sonnet 5 · medium | retention > 100 % (a smell, not a rule) | **G1 format gate** |
| 4 | Rewrote the document | B5 · Sonnet 5 · small, 3 draws | retention 51 / 71 / 95 % | **nothing: it was not a failure.** fidelity 1.0 on all three |
| 5 | Reasoning inside the document | B4 · Sonnet 4.6 · small; B2 · Sonnet 4.6 · large | none | **fabrication**, and recall 0 / precision 0 on the invented text |
| 6 | Heading blind spot | B7 · medium, both Sonnets; B8 · medium, three models; B9 · Sonnet 4.6 · medium | none; "56 marks, also redacts variant spellings" | **recall 0.90–0.93**, every leak in the title |

---

## 1. It did nothing, and every signal said it worked

**B5 ReAct · Haiku 4.5 · medium.** Status `completed`, clean Markdown, fidelity 1.0,
fabrication 0.0, $0.16, 61 s. Marks placed: 0. Target mentions left readable: 29.
**recall 0.0 → silent.** Same model, one architecture down (B3): recall 1.0 for $0.014.

## 2. It redacted the subject of the document

**B4 `ai_agents` + tool · Sonnet 5 · medium.** 70 marks on a page with 30 targets. v2
places every one: 29 on WordPress, **37 on "Drupal"**, 4 on invented text.

| Axis | Score |
|---|---|
| recall | 1.0 |
| precision | **0.414** |
| subject | **0.26** |
| fidelity | 1.0 |
| fabrication | 0.014 |

v1 ranked this run first on its redaction column. In v2 it is the worst graded run in the
dataset, on two axes. This is the slide that justified rebuilding the rubric.

## 3. It handed back the input

**B2 raw HTML → LLM · small · all four models.** The output opens with a fenced ` ```html `
block and the page's own `<html>` tag. Tag density around 30 per 1,000 chars; G1 fails; class
`format`. On the medium page Sonnet 5 did the harder half of the job inside the HTML:
underneath the format failure, recall 0.75 and precision 0.45. v1's 408 % and 567 %
retention figures are gone; there is no number to misread as "better than the control".

## 4. It rewrote the document: withdrawn

**B5 ReAct · Sonnet 5 · small · three draws** at 51, 71 and 95 % retention were failure #4
in v1. Against the gold body all three score **fidelity 1.0 and fabrication 0.0**. They
differ in how many Drupal.org menu sentences they reproduced: 0, 11 and 25. The variance was
real, and it was variance in chrome. Eleven draws of this cell now exist; ten are `correct`
and one failed loudly. The B5 vs B7 finding stands on **calls and cost**
([`../research/04-tool-shape.md`](../research/04-tool-shape.md)), not on retention.

## 5. The agent's reasoning ended up inside the document

Two runs, both Sonnet 4.6, neither visible to any v1 metric.

**B4 · small.** The small page names no competitor. The output contains, between the
converted sections:

> Now I'll apply the competitor replacement rule. Drupal CMS competitors include platforms
> like WordPress, Joomla, Wix, Squarespace, Sitecore, Adobe Experience Manager, Contentful,
> Webflow etc. Reviewing the converted markdown, none of those competitor names appear in
> the content. … Here is the final output:

Six competitor names, written into a document that had none, by the step whose job was to
remove them. fabrication 0.087, six leaks, **recall 0.0 → silent**. v1's leak column did
record 6; nothing in the tables surfaced a leak on the control page.

**B2 · large.** The output ends with a note about the article's references that names
WordPress and Joomla and places four marks in it. Every mark the run placed sits in text
the model wrote. **precision 0.0, recall 0.0 → silent.** fidelity 0.97: the article itself
was fine.

> **Lesson:** the output channel carries whatever the model was thinking. Fabrication is the
> only axis that sees it, and it needs a gold document to see against.

## 6. The heading blind spot

**B7 · medium · Sonnet 4.6 and Sonnet 5; B8 · medium · Sonnet 4.6, Sonnet 5, Opus 5; B9 ·
medium · Sonnet 4.6.** Six draws, three variants, three models. The body is redacted, 28
marks, precision 1.0. The document starts:

```
# Drupal versus WordPress

## Drupal versus WordPress
```

Two or three target mentions left readable per draw, every one in a heading. recall
0.90–0.93 → `degraded` on all six draws. Every variant whose tool returns Markdown from a
URL does this, on every model tried, with either prompt. B9's critic accepted the Sonnet 4.6
draft as-is; on Sonnet 5, Opus 5 and Haiku the critic loop redacted the title and those
cells are `correct`. B3, which hands the model the Markdown directly, redacts the title on
every model.

v1 reported this row as "56 marks on 36 mentions, also redacts variant spellings". The 56
was a counting artefact (nine-bar marks counted twice), and the leaks were in the CSV.

> **Lesson:** a deterministic rule ("every mention") is applied by the model to the part of
> the document it treats as prose. Headings are not prose to it. A regex post-pass over the
> output would have made all six draws `correct` for nothing.

---

## The pattern behind all six

| # | What happened | What `status` said | What catches it |
|---|---|---|---|
| 1 | Redacted nothing | completed | recall |
| 2 | Redacted the subject | completed | subject, precision |
| 3 | Returned HTML | completed | format gate |
| 4 | Kept less chrome | completed | nothing: correct |
| 5 | Wrote its reasoning into the output | completed | fabrication |
| 6 | Skipped the headings | completed | recall, at the sentence level |

Nothing failed loudly. Every check above is deterministic and runs in two seconds over the
whole dataset. All of them need one thing the v1 harness did not have: **a gold document,
decided in advance**, so that "wrong" has a definition before the run starts.
