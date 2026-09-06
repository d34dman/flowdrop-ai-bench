"""Corpus and prompt: static, built from every corpus/<version>/manifest.json; nothing to filter."""
import os
from framework import esc


def build(ctx):
    parts = []
    versions = sorted(d for d in os.listdir(os.path.join(ctx.root, 'corpus')) if d.startswith('v') and os.path.isdir(os.path.join(ctx.root, 'corpus', d)))
    for version in versions:
        m = ctx.manifest(version)
        parts.append(f'<h2>Corpus {esc(version)}</h2><div class="wrap"><table><tr><th>Page</th><th class="n">Gold bytes</th><th class="n">Headings</th>'
                     '<th class="n">Targets</th><th class="n">Homonyms</th><th class="n">Protected</th><th>Chrome mentions</th></tr>')
        for p, d in m['pages'].items():
            parts.append(f'<tr><td><a href="../corpus/{version}/{p}.html">{esc(p)}</a> &middot; <a href="../corpus/{version}/gold/{p}.md">gold</a></td>'
                         f'<td class="n">{d["gold_bytes"]}</td><td class="n">{d["headings"]}</td><td class="n">{len(d["targets"])}</td>'
                         f'<td class="n">{len(d["homonyms"])}</td><td class="n">{len(d["protected"])}</td>'
                         f'<td>{esc(", ".join(f"{k} x{v}" for k, v in d["chrome"].items()))}</td></tr>')
        parts.append(f'</table></div><p class="note">Glyph <code>{esc(m["glyph"])}</code>. Subject: {esc(m.get("subject", ""))}. '
                     f'Competitors: {esc(", ".join(m["competitors"]))} (real: {esc(", ".join(m.get("real_names", [])))}). '
                     f'Protected: {esc(", ".join(m["protected_names"]))}. Prompt: <a href="../prompt/{esc(m["prompt"])}">{esc(m["prompt"])}</a> '
                     f'(sha256 {esc(m["prompt_sha256"][:12])}). Served from <code>{esc(m["base_url"])}</code>.</p>')
    parts.append('<h2>Why an owned corpus</h2><p>The pages are original prose about Drupal and six competitors, two real and four fictional, '
                 'so the gold document is known by construction, the pages never change under a run, and traps can be planted on purpose. '
                 f'The long form is in the <a href="{ctx.repo}#why-an-owned-corpus-and-why-the-cast-is-mixed">README</a>.</p>')
    ctx.write('index.html', ctx.page(ctx.visual['title'], ''.join(parts), sub=ctx.visual['blurb']))
