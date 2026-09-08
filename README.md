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

The label of a cell reads **input the model sees → who does the work → tools it holds**.

| | Cell | Shape |
|---|---|---|
| B0 | URL → output, nothing runs | Control. The floor: pure FlowDrop overhead. |
| B1 | URL → fetch → to-Markdown, no model | Control. Fixed pipeline, HTML to Markdown, nothing redacted. |
| B2 | HTML → LLM | Raw HTML to one model call that converts and redacts. |
| B3 | Markdown → LLM | Convert in a node, one model call redacts. |
| B4 | HTML → AI Agent + to-Markdown tool | Drupal AI Agent given the HTML, owns the converter. Peer of B3. |
| B5 | URL → ReAct agent + fetch, to-Markdown tools | FlowDrop ReAct agent given only a URL, owns both tools. |
| B6 | URL → AI Agent + fetch, to-Markdown tools | Drupal AI Agent given only a URL, owns both tools. Peer of B5. |
| B7 | URL → ReAct agent + fetch-and-convert tool | B5 plus a fused URL-to-Markdown tool. |
| B8 | URL → ReAct engine, tools in parent graph | Same tools as B7, owned by the parent workflow, passed in as an argument. |
| B9 | URL → Reflexion + critic, tools in parent graph | B8 with a critic that can send the draft back, up to three times. |

Each cell is drawn and explained, with the pairs that differ by one decision, on the
[Architectures page](https://d34dman.github.io/flowdrop-ai-bench/architectures/).

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

## Contributors

Every run on the site was contributed by someone who set up the runner, paid for the model
calls and opened a pull request. Credit follows the [all-contributors](https://allcontributors.org)
convention: 🔣 data is contributed runs, 💻 code is the runner or the site.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/d34dman"><img src="https://avatars.githubusercontent.com/u/1006481?v=4?s=80" width="80px;" alt="Shibin Das"/><br /><sub><b>Shibin Das</b></sub></a><br /><a href="https://github.com/d34dman/flowdrop-ai-bench/commits?author=d34dman" title="Code">💻</a> <a href="#data-d34dman" title="Data">🔣</a> <a href="https://github.com/d34dman/flowdrop-ai-bench/commits?author=d34dman" title="Documentation">📖</a> <a href="#infra-d34dman" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#ideas-d34dman" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/gkastanis"><img src="https://avatars.githubusercontent.com/u/15897286?v=4?s=80" width="80px;" alt="George Kastanis"/><br /><sub><b>George Kastanis</b></sub></a><br /><a href="#data-gkastanis" title="Data">🔣</a> <a href="https://github.com/d34dman/flowdrop-ai-bench/commits?author=gkastanis" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## Sponsor

Development of this benchmark and the model API usage behind every run are generously
sponsored by [Factorial GmbH](https://www.factorial.io/), the company behind FlowDrop.

## Licence

Code MIT (`LICENSE`), except the Drupal site and module under `runner/`, GPL-2.0-or-later
as Drupal requires. Corpus, prompt and dataset CC BY 4.0 (`LICENSE-CORPUS`).
