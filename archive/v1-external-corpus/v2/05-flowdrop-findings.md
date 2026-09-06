# FlowDrop findings, carried forward

The four upstream bugs and their fixes are unchanged from v1 and live in
[`../research/06-flowdrop-findings.md`](../research/06-flowdrop-findings.md):

1. An exposed-but-unconnected port silently erases the system prompt (flowdrop#3592438).
2. The ReAct loop re-sends its transcript uncached (flowdrop#3592437), and caching is
   unreachable through the OpenAI-compatible endpoint anyway (ai_provider_anthropic#3607961).
3. The pipeline memory ceiling produces a non-atomic failure: the answer exists, the run fails.
4. A skipped tool branch fails a re-entered loop instead of skipping downstream
   (flowdrop#3592443), which took out three B9 cells on the first sweep; fixed upstream the
   same day.

Also from the last sweep: the workflow editor drops the `orchestrator_settings` key on save,
which `launch.php` needs to start a run (`set_sync_orchestrator.php` restores it; commit 4ac17e6).

What the re-grade and the last sweep add:

- **The B5 shadowing correction stands and matters more now.** With B5's rows valid, the
  eleven draws of B5 Sonnet 5 on the small page are the largest single cell in the dataset,
  and they are the evidence that v1's failure #4 was a metric artefact.
- **A confirmation gate is a fifth way to not fail loudly.** B8 on Opus 5, medium page,
  paused three times on the `http_request` tool's confirmation gate before the gate was
  waived (commit f5923a4). A paused pipeline reports neither success nor failure; the run
  cost $0.008 each time and produced nothing. v2 lists these rows and excludes them from the
  class counts, but a production pipeline would have to decide what a pause means.
- **The heading blind spot is a prompt-and-post-processing finding, not a FlowDrop bug**,
  but it is the kind of thing a FlowDrop validation node should exist for: a deterministic
  regex pass over the agent's output would have turned six `degraded` draws into `correct`.
  See [03-failure-gallery.md](03-failure-gallery.md), #6.
