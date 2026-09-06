# FlowDrop AI Bench

A benchmark for AI-assisted content workflows built with [FlowDrop](https://flowdrop.io).
One task, one prompt, one owned corpus, ten workflow architectures from a fixed pipeline
to a fully autonomous agent, so their cost, speed and failure modes can be compared on
equal footing.

**The task:** fetch a page, convert it to Markdown faithfully, and redact every mention of
a fixed list of competing CMS products with `████` while leaving everything else, including
the same words used in other senses, untouched.

## Layout

| Path | What |
|---|---|
| `corpus/v1/` | Three pages we wrote and host ourselves (`small.html`, `medium.html`, `large.html`), their gold Markdown bodies, and `manifest.json` with every target, protected name and homonym trap by position. Served at <https://d34dman.github.io/flowdrop-ai-bench/corpus/v1/>. Never edited in place; a change is `v2/`. |
| `corpus/build.py` | Regenerates the HTML, gold and manifest from `corpus/v1/src/`. Standard library only. |
| `prompt/redact.v1.md` | The one system prompt every model-calling cell runs with. Its front-matter defines the glyph and the competitor list. |

The runner, scorer, dataset and site arrive in the next phases; see the plan in the
FlowDrop workspace (`process/plans/flowdrop-ai-bench.md`) or the issues here.

## Why a fictional corpus

The first version of this benchmark fetched live third-party pages and republished their
text in its results. We had no consent for either, so every figure from that version was
discarded. The pages here are original prose about Drupal and five fictional competitors
(Quillpress, Hexagrid, Lumen CMS, Marrow, Sitewright). Because we wrote them, the gold
document is known by construction, the pages never change under a run, and we can plant
traps on purpose: a competitor's name used as a surname or a unit, which must not be
redacted, and competitor names in navigation, alt text and citations, which are chrome
rather than document.

## Licence

Code is MIT (`LICENSE`). Corpus, prompt and dataset are CC BY 4.0 (`LICENSE-CORPUS`).
