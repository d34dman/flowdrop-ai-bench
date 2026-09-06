# Prompt

One system prompt for every model-calling cell. The front-matter is machine-read:
`glyph` is the redaction mark the scorer counts runs of, `competitors` are the names the
scorer treats as targets, `subject` must never be redacted. The text below the front-matter
is what the model sees, verbatim, in every variant (chat node, ReAct engine, Reflexion
engine and its critic, AI Agents entity). A changed prompt is a new file, `redact.v2.md`,
and every run records the sha256 of the prompt it ran with.
