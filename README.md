# FlowDrop AI Bench

**A living benchmark of AI content workflows.** One task, one prompt, one owned corpus,
ten architectures from a fixed pipeline to an autonomous agent, compared on correctness,
cost, speed and failure modes.

**→ Results: <https://d34dman.github.io/flowdrop-ai-bench/>**

## The task

Fetch a page, convert it to Markdown faithfully, and redact every mention of a fixed list
of competing CMS products with `████`. Leave everything else untouched, including the same
words used in other senses.

## The architectures

| | Cell | Shape |
|---|---|---|
| B0 | floor | Fetch only, no conversion, no model. Control. |
| B1 | reference | Fixed pipeline, HTML to Markdown, no model. Control. |
| B2 | raw HTML → LLM | Raw HTML to one LLM call. |
| B3 | Markdown → LLM | Markdown to one LLM call. |
| B4 | AI Agent + tool | Drupal AI Agent given the HTML, owns the Markdown tool. Peer of B3. |
| B5 | ReAct agent | FlowDrop ReAct agent given a URL, owns fetch and Markdown tools. |
| B6 | autonomous agent | Drupal AI Agent given a URL, owns fetch and Markdown tools. Peer of B5. |
| B7 | ReAct, URL tool | ReAct agent with optimized tools. |
| B8 | ReAct, tools in parent | Tools run in the parent pipeline. |
| B9 | Reflexion, tools in parent | Reflexion agent with a critic, tools in the parent. |

Every cell runs the same prompt on the same three pages, on any model your provider key
offers. A run is graded on recall, precision, subject, homonym, fidelity, fabrication and
structure, then classed as **correct**, **degraded**, **silent**, **format** or **loud**.

## Run a cell

```sh
echo 'ANTHROPIC_KEY=sk-ant-...' >> .ddev/.env
ddev start && sh bin/setup.sh
ddev drush bench:wizard
```

Then `git add runs outputs && git commit && git push` and open a pull request. CI scores
it, merge publishes it. Details, what is welcome and what changes the experiment:
[CONTRIBUTING.md](CONTRIBUTING.md).

## Why an owned corpus, and why the cast is mixed

The first version fetched live third-party pages and republished their text. We had no
consent for either, so every figure from it was discarded.

The pages here are original prose about Drupal and six competitors: two real (WordPress,
Joomla) and four fictional (Hexagrid, Lumen CMS, Marrow, Sitewright). Because we wrote
them, the gold document is known by construction, the pages never change under a run, and
traps are planted on purpose: a competitor's name used as a surname or a unit, which must
not be redacted, and competitor names in navigation, alt text and citations, which are
chrome rather than document.

Real names give a reader a familiar target. Fictional names have no model prior, so a
model can only redact them by following the list it was given. The scorer reports recall
for each class separately; the gap between them is how much a cell leans on what the
model already knows rather than on the instruction.

## More

- [CONTRIBUTING.md](CONTRIBUTING.md), contributing runs, exclusions, adding a visual.
- [DEVELOPMENT.md](DEVELOPMENT.md), repository layout, the site framework, building locally.
- [runner/README.md](runner/README.md), the Drupal site that runs the cells.

## Licence

Code MIT (`LICENSE`), except the Drupal site and module under `runner/`, GPL-2.0-or-later
as Drupal requires. Corpus, prompt and dataset CC BY 4.0 (`LICENSE-CORPUS`).
