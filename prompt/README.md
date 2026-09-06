# Prompt

One system prompt for every model-calling cell. The front-matter is machine-read:
`glyph` is the redaction mark the scorer counts runs of, `competitors` are the names the
scorer treats as targets, `subject` must never be redacted. The text below the front-matter
is what the model sees, verbatim, in every variant (chat node, ReAct engine, Reflexion
engine and its critic, AI Agents entity). A changed prompt is a new file, `redact.v2.md`,
and every run records the sha256 of the prompt it ran with.

The critic template (`critic.v<n>.md`, front-matter `for:` names the prompt it reviews) is
rendered with `{{competitors}}`, `{{glyph}}` and `{{subject}}` from the prompt's
front-matter. It is versioned on its own: `critic.v2` added the rule that the subject is
never redacted, after `critic.v1` told the Reflexion actor to redact Drupal and the actor
argued back in its final answer, leaking the whole target list. Every run records the
critic's sha256 alongside the prompt's.
