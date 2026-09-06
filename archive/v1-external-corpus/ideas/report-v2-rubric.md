# Report v2 — a real rubric, and how to re-report

Drafted 2026-09-05. Proposes replacing the v1 metrics (`kept` / `red` / `leak`) with a
scorecard that grades what the talk actually claims, and releasing the result as a
**new report** rather than patching the existing pages. The v1 pages and `data/runs.csv`
stay frozen as the record of what was published first.

---

## 1. What v1 measures, and where it lies

The v1 rubric was built to make the numbers *visible*, not *right*. Each axis has a hole
that the failure gallery already documents from the inside:

| v1 metric | What it actually measures | Where it fails |
|---|---|---|
| `kept` (retention %) | output bytes ÷ **B1 conversion** bytes, after stripping link targets and images | The B1 control is not a gold document. The medium control opens with an IBM nav bar and a cookie banner; the small control is 40 % Drupal.org menu. A model that drops chrome and keeps the article is *penalised*. Cannot see invented prose (failure #4), cannot see the run that returned HTML (failure #3, 408 %). |
| `red` (glyph count) | number of `▌▌▌▌` placed | Counts marks, not correctness. Failure #2 (70 glyphs, all 46 "Drupal" gone) scores **highest** on this column. B8's 56 on medium is presented as "also redacts variant spellings" — unverified. |
| `leak` | competitor names from a fixed list of 15, still readable | Zero leaks on the small page is trivially true (0 competitors). Zero leaks is also what over-redaction produces. Misses "WP", possessives, "WordPress.com". |
| `drupal_mentions` | Drupal mentions kept | Added after failure #2 as a patch. Lives in the CSV, not in the tables or the rankings. |
| `html_tag_density` | tags per 1 000 chars | A flag, not a score. Rows it flags still show a retention number that reads as quality. |
| `status` | scheduler status | The talk's whole thesis is "completed is not a quality signal", yet **there is no metric for silent failure**. It is found by reading. |

Three consequences for the current tables:

1. **"Cheapest correct run" has no definition of correct.** It was picked by eye.
2. **Rankings are per-cell, single draw.** 93 model×variant×page cells; 5 have n≥3.
   Every ranking sentence in 02-results-matrix.md is one sample.
3. **The title metric is absent.** The talk is "Why your AI agent hallucinates". No v1
   column can distinguish a faithfully copied sentence from an invented one.

---

## 2. Rubric v2 — the scorecard

One scorecard per run. Gates first, then graded axes, then an **outcome class**, which is
the headline unit of the new report.

### 2.1 Gold documents (replace the B1 control)

Per page, build once and commit under `data/gold/`:

- `gold/<page>.md` — the B1 conversion with nav, cookie, footer and sidebar chrome
  removed by hand. Article body, headings, lists and tables only. **This is the
  denominator for fidelity.**
- `gold/<page>.targets.json` — every competitor mention in the gold body with its
  sentence index and surface form (`WordPress`, `WordPress.com`, `Joomla`, `Mambo`,
  `Backdrop`…). Counted, not assumed. Small is expected to have 0; that stays the
  false-positive control.
- `gold/<page>.protected.json` — mentions that must **not** be redacted: `Drupal`, and a
  handful of other proper nouns present in the body (Acquia, IBM, Linux, PHP…). This is
  what catches failure #2 and its milder cousins.

### 2.2 Gates (pass/fail, evaluated in order)

| Gate | Test | Fails today |
|---|---|---|
| G0 Delivered | `status == completed` and output ≥ 500 chars | Haiku large cliffs, the memory-cap run |
| G1 Format | tag density ≤ 5/1 000, not wrapped in a code fence, ≥ 1 Markdown heading | Failure #3 — every B2 small/medium row |
| G2 In scope | output is about the same document: ≥ 50 % of gold headings present | Catches a model that answers a different question |

A run that fails a gate gets no graded score. It is classified (see 2.4), not ranked.

### 2.3 Graded axes (0–1 each)

All deterministic; sentence-level alignment of output to gold after normalising
whitespace, punctuation and treating `▌▌▌▌` as a wildcard token.

| Axis | Definition | Catches |
|---|---|---|
| **Redaction recall** | target mentions redacted ÷ target mentions in gold | Failure #1 (0/36) |
| **Redaction precision** | glyphs that sit where a target was ÷ glyphs placed | Failure #2 (~0.51), B8's 56-on-36 |
| **Subject preservation** | protected mentions kept ÷ protected mentions in gold | Failure #2 (0/46) |
| **Fidelity recall** | gold body sentences found in output (fuzzy ≥ 0.9) ÷ gold sentences | Truncation (B3 Haiku large), dropped halves (B5 draws) |
| **Fabrication rate** | output sentences **not** found in gold ÷ output sentences | Invented prose, rewrites. **The hallucination metric.** |
| **Structure** | gold headings present in output, in order | Flattened or reordered documents |

Prototype check (2026-09-05, three-word left-context alignment against the raw B1
control, so a first approximation): B4 · Sonnet 5 · medium — 70 glyphs, **27 sat on
"Drupal"**, 18 on "WordPress", 22 unaligned. B8 · Haiku · medium — 40 glyphs, 18 on
"WordPress", 0 on "Drupal", 22 unaligned. Precision is measurable without an LLM judge.

### 2.4 Outcome class — the headline

| Class | Rule |
|---|---|
| **Correct** | all gates pass; recall ≥ 0.95, precision ≥ 0.95, subject ≥ 0.95, fidelity ≥ 0.90, fabrication ≤ 0.05 |
| **Degraded** | all gates pass; every axis ≥ 0.75 but not Correct. Visible on inspection, usable with a fix. |
| **Silent failure** | all gates pass **and** any axis < 0.75. Status said success; the document is wrong. |
| **Loud failure** | fails G0. Nothing delivered, or an error. |
| **Format failure** | passes G0, fails G1 or G2. |

This is the table the talk needs: for each variant × model, how many draws landed in each
class. "The variant with the least agency never failed silently" becomes a row with a
zero in it, not a sentence.

### 2.5 Efficiency and stability (reported alongside, never blended in)

- Cost, wall, calls, input/output tokens — as today, metered.
- **Cost per Correct run** = cell spend ÷ Correct draws. Undefined (∞) when zero Correct.
- **Stability** = spread of fidelity recall and of call count across draws in the cell.
  Requires n≥3; report as min–max, not as a standard deviation nobody believes at n=3.

No composite score. A single number invites exactly the ranking-by-glyph-count mistake v1
made. Class first, then axes, then cost.

### 2.6 LLM judge — optional, secondary

A judge adds paraphrase detection ("same meaning, different words") that fuzzy sentence
matching misses. Recommendation: **do not ship the report on a judge.** Run one over a
20-run sample, report agreement with the deterministic fabrication rate, and use the
disagreement cases as a slide. A deterministic rubric is defensible on stage; a judge
grading a talk about hallucination is a joke the audience will make first.

---

## 3. Re-report plan

### Phase A — rescore what exists · **$0** · ~1 day · **done 2026-09-05** (`data/score_v2.py`, `data/RUNS_V2.md`)

Every one of the 128 LLM runs that completed has its output on disk
(`scratchpad/bench/results/outputs/`); the 8 missing files are all failed runs. Nothing
needs to be rerun to rescore.

1. Build the three gold documents and target/protected lists (2.1). Hand-check the
   medium page's 36 competitor mentions against the gold body.
2. Write `scratchpad/bench/score_v2.py`: reads `metrics.jsonl` + outputs, emits
   `data/runs_v2.csv` with the gates, axes, class, and the v1 columns kept for
   comparison. `runs.csv` is not touched.
3. Produce the **v1 → v2 autopsy**: for every cell, v1 rank vs v2 class. The expected
   result — the v1 "best" B4 cell drops to Silent failure, B3 Sonnet 5 stays Correct on
   every page, B2 small/medium move from 408 % to Format failure — is itself a section of
   the new report and probably a slide.

### Phase B — fill the holes · **~$15–20** · half a day of wall time · **not started; decided 2026-09-05 to release v2 without it**

Only after Phase A, and only where the class table has cells that a single draw cannot
support. Ordered by value:

| Run | Why | Est. |
|---|---|---|
| n=3 on medium, B3/B5/B7/B8/B9, Haiku + Sonnet 5 | medium is the only page with redaction targets *and* a protected subject; class rates need more than one draw | ~$8 |
| B8, B9 on Opus 5, all pages | completes the model matrix (open-questions 4b) | ~$5 |
| Injection page through B3, B7, B9 | learning objective 3 has no data at all (open-questions 1) | ~$1 incl. B9 |
| Re-run the 4 B9 rows that have no output | B9 is the only variant whose rows are partly missing | ~$1 |

Use `run_cell.sh` with tags `v2-…`; results stay in `results/` until folded.

### Phase C — the new report · **drafted 2026-09-05** in `docs/drupalcon/v2/`; site pages still v1

New folder `docs/drupalcon/v2/`, same shape as `research/`, so both can be read side by
side and the v1 pages keep their URLs:

| File | Content |
|---|---|
| `00-what-changed.md` | Why v1's metrics were replaced; the autopsy table from Phase A |
| `01-method.md` | Task, pages, variants (unchanged) + the gold documents + rubric v2 |
| `02-scorecard.md` | Outcome-class matrix (variant × model × page), then per-axis tables |
| `03-failure-gallery.md` | The same four failures, now with the axis that catches each one |
| `04-cost-per-correct.md` | Cost, wall, calls conditioned on class |
| `05-flowdrop-findings.md` | Carried forward |
| `data/runs_v2.csv`, `data/gold/` | The new frozen dataset |

Site: regenerate the Tradeoff Explorer and Model Matrix from `runs_v2.csv` with class as
the colour and precision/fabrication as new axes; keep the v1 artifacts online, marked
superseded in `ARTIFACTS.md`.

### What to say in the README of both

> v1 scored redaction by counting marks and fidelity by counting bytes. Both were fooled
> by the same run. v2 grades recall, precision, subject preservation, fidelity and
> fabrication against a hand-cleaned gold document, and classifies every run as Correct,
> Degraded, Silent failure, Loud failure or Format failure. The raw runs are the same;
> the conclusions are re-derived.

---

## 4. Decisions needed

1. **Correct thresholds** in 2.4 — proposed 0.95/0.95/0.95/0.90/0.05. **Decided 2026-09-05: fidelity
   tightened to 0.95; no graded run changed class.** Tighten fidelity
   to 0.95 if the gold body is clean enough that Sonnet 5 B3 still passes.
2. **Which Phase B runs to buy**, if any. Phase A alone is enough to release v2; Phase B
   turns single draws into rates.
3. **Whether the v1 pages get a banner** pointing at v2, or are left as-is with the note
   in `ARTIFACTS.md` only.
