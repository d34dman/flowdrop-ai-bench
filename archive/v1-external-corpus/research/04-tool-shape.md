# Tool shape: the argument that costs 18× more

This is the cleanest controlled experiment in the research, and it maps directly onto
**learning objective 1** (output format, token economy, atomicity).

## The change

Two FlowDrop ReAct agents. Same node, same model, same system prompt, same pages. One
line of difference, in the tool schema:

```
B5   html_to_markdown(content: string)   ← the page itself
B7   url_to_markdown(url: string)        ← a reference to the page
```

## Why that one line is expensive

To call B5's tool, the model must **emit the entire document as output tokens**. The page
crosses the model boundary three times: in as context, out as a tool argument, back in as
a tool result. Then the ReAct loop re-sends the whole transcript on the next iteration.

That has four consequences, and only the first is obvious:

1. **Output tokens are billed at 5× input** on Sonnet 5 ($10 vs $2 per MTok).
2. **It is capped by `max_tokens`** — a long page can simply not fit through.
3. **It is reconstruction, not copying.** The model regenerates the document from its own
   representation, and can drop parts of it silently.
4. **It compounds per iteration**, because the loop re-sends everything.

B7's argument is a URL — about ten tokens, regardless of page size. The fetch and the
conversion run server-side in Drupal. Only the finished Markdown enters the conversation,
once.

## The numbers — Sonnet 5, one draw each

| Page | | Calls | Tokens in | Cost | Wall | Retention |
|---|---|---|---|---|---|---|
| small | B5 | 3 | 47,539 | $0.1345 | 39.9s | 50.6% |
| small | **B7** | **2** | **9,399** | **$0.0826** | 52.0s | **94.6%** |
| medium | B5 | 2 | 91,622 | $0.3077 | 113.5s | 93.4% |
| medium | **B7** | **2** | **7,468** | **$0.0603** | **41.9s** | 93.2% |
| large | B5 | 4 | 1,055,106 | $2.4665 | 316.1s | 74.3% |
| large | **B7** | **2** | **56,955** | **$0.4092** | **224.7s** | **79.7%** |

| Page | Input tokens | Cost |
|---|---|---|
| small | **5.1× fewer** | 1.6× cheaper |
| medium | **12.3× fewer** | 5.1× cheaper |
| large | **18.5× fewer** | **6.0× cheaper** |

**It is not a quality trade.** On the large page B7 costs a sixth and retains *more*
(79.7% vs 74.3%). On the medium page the two are indistinguishable in fidelity (93.2% vs
93.4%) at a fifth of the price.

## The part that matters more than the cost

Three draws of the small page, same model, same prompt:

| | Draw 1 | Draw 2 | Draw 3 | Spread |
|---|---|---|---|---|
| **B5** chars | 5,818 | 8,318 | 3,721 | **4,597** |
| **B5** retention | 70.5% | 95.1% | 50.6% | **44.5 pts** |
| **B5** cost | $0.1925 | $0.2712 | $0.1345 | $0.1367 |
| **B7** chars | 8,715 | 8,715 | 8,716 | **1** |
| **B7** retention | 94.6% | 94.6% | 94.6% | **0.0 pts** |
| **B7** cost | $0.0820 | $0.0824 | $0.0826 | $0.0006 |

A one-character spread across three runs, against a 4,597-character spread. **The
architecture, not the model, is what made the output reproducible.**

## Does it survive a model change?

B7 re-run end to end on Sonnet 4.6:

| Page | Sonnet 5 | Sonnet 4.6 |
|---|---|---|
| small | 94.6%, 2 calls, $0.083 | 69.3%, 2 calls, $0.066 |
| medium | 93.2%, 2 calls, $0.060 | 93.3%, 2 calls, $0.067 |
| large | 79.7%, 2 calls, $0.409 | 80.9%, 2 calls, $0.363 |

**Two calls on every page for both models**, and near-identical fidelity on the two pages
carrying real content. Contrast with B5 in the matrix, where changing the model changed
the call count, moved cost by an order of magnitude, and in one case determined whether
anything came back at all.

## The generalisation for the talk

> **Never pass bulk content through the model's output channel.** Pass a handle — an ID,
> a URL, a config key — and let deterministic code resolve it.

This is the same principle as learning objective 1's *DSL vs JSON* and objective 4's
*predictable identifiers*, applied to a different payload. In the FlowDrop editor agent
the payload is workflow config rather than a web page, but the failure is identical: a
model asked to re-emit a large structure will occasionally re-emit it wrong, and you will
not be told.

## Caveat

Both variants were re-verified to receive their system prompt before this comparison.
The earlier B7 runs at ~30% retention are **excluded** — they hit the port bug. Their
input-token count is the tell: 9,061 without the prompt, 9,399 with it.

## What tool shape does *not* fix

Redaction accuracy. On the medium page B7 left 2 competitor mentions readable; B5 left 1.
Tool shape governs how the document moves, not how carefully the model reads it. That
remains a prompting and evaluation problem in both architectures.
