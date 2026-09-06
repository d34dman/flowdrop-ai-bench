# What changed, and why

## The three holes in v1

The v1 metrics were built to make the numbers visible, not right. Each axis had a hole
the failure gallery already documented from the inside:

| v1 metric | What it measured | What it could not see |
|---|---|---|
| retention (`kept`) | output bytes ÷ **B1 conversion** bytes | The B1 control is the whole page: 40 % Drupal.org menu on the small page, IBM's header and promos on the medium one, an infobox and 380 lines of references on the large one. Dropping chrome was penalised. Invented prose of the same length scored 100 %. |
| redactions (`red`) | `▌▌▌▌` substrings | Counts marks, not correctness. The run that redacted "Drupal" 37 times scored **highest**. Nine-bar marks were counted twice. |
| leaks | 15 names still readable, case-insensitive | Zero on the small page is trivially true (0 competitors). Zero is also what over-redaction produces. Counted the browser title and share-link URLs as prose. |
| `drupal_mentions` | Drupal mentions kept | Added as a patch after failure #2; lived in the CSV, not in the tables. |
| `status` | scheduler status | The talk's thesis is "completed is not a quality signal", and there was **no metric for silent failure**. |

Consequences: "cheapest correct run" had no definition of correct, rankings were single
draws, and the title metric, hallucination, had no column.

## What v2 does instead

Per page, a **gold document**: the B1 conversion with the chrome removed by explicit,
reviewable line ranges ([`../data/gold/`](../data/gold/)), plus a list of every competitor
mention in the body and every protected name. Then three gates, five graded axes and an
**outcome class** per run. The full rubric is in [01-method.md](01-method.md).

Two facts the gold documents corrected before any run was graded:

- **Medium has 30 targets, not 36.** The other six were the browser title and share-link
  URLs. A run with 30 marks and no leaks was already complete; 33 to 36 was redacting URLs.
- **Large has 1 target, not 5,** and it is Backdrop CMS, a 2013 Drupal fork. Two of v1's
  five hits were one link counted twice; three sat in the References. The models split
  evenly on whether a fork is a competitor, so Backdrop is **neutral** in v2. The large
  page grades fidelity, format and cost only. It never tested redaction.

## The autopsy: v1 verdict → v2 class

| Cell | What v1 said | What v2 says | Why |
|---|---|---|---|
| B4 · Sonnet 5 · medium | 70 marks, 0 leaks: **top of the redaction column** | **silent** | precision 0.41, subject 0.26: 37 marks on "Drupal", 4 on invented text |
| B5 · Haiku · medium | 0 marks, 29 leaks | **silent** | recall 0.0: stands, correctly |
| B2 · small · all four models | 408 % retention | **format** | G1: HTML in a code fence |
| B2 · Sonnet 5 · medium | 567 %, "redacted correctly but as HTML" | **format** | G1; recall 0.75, precision 0.45 underneath |
| B3 · Haiku · large | 4.3 %, "fails visibly" | **silent** | fidelity 0.08, structure 0.0: it completed. Visible only if someone checks length |
| B5 · Sonnet 5 · small · 3 draws | 51 / 71 / 95 % retention, failure #4 | **correct, correct, correct** | fidelity 1.0 on all three; they differ by 0, 11 or 25 Drupal.org menu sentences |
| B2/B3/B4 · Haiku, Sonnet 4.6 · medium | 67–69 %, bottom of the retention column | **correct** | they dropped IBM's header and promos and kept the article |
| B8 · medium · all models | 56 marks on 36 mentions, "also redacts variant spellings" | **degraded** | 28 marks (nine-bar glyphs were double-counted); 2–3 leaks, all in the title heading |
| B4 · Sonnet 4.6 · small | `leaks = 6` in the CSV on a page with 0 competitors; never surfaced | **silent** | the agent's reasoning is inside the document, naming six competitors |
| B2 · Sonnet 4.6 · large | 43.5 %, 4 marks, 2 leaks | **silent** | the 4 marks sit in a note the model appended about the references; recall 0, precision 0 |
| B9 · Haiku · small · first fixed-module attempt | loud failure | **excluded** | `paused` with a job pending: no answer exists to grade. Five such rows across the ledger |

The expected result held: v1's best cell by redaction count is last in v2, B3 on Sonnet 5
is correct on every page, and the B2 small row moved from "better than the control" to a
format failure. Two things v1 could not see at all surfaced: **agent reasoning written
into the document** (twice), and a **heading blind spot** in the URL-tool variants (four
draws, three models). Both are in [03-failure-gallery.md](03-failure-gallery.md).

## Counting artefacts, for the record

- v1 counted `▌▌▌▌` substrings. Sonnet 4.6, Sonnet 5 and Opus 5 on B8/B9 emit nine-bar
  marks, so every one counted twice. B8 medium placed 28 marks, not 56; B9 Sonnet 5 placed
  35, not 70.
- v1 retention variance on B5 small (failure #4) was chrome, not content. B7's stability in
  call count stands; its stability in retention was measuring the same chrome.
- v1's `drupal_mentions` control value of 46 counted the title and URLs. The gold body has 38.
