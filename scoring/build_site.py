#!/usr/bin/env python3
"""Builds the published site into _site/: index page with the scorecard, plus the
corpus, prompt and data folders copied in. Standard library only.

    python3 scoring/build_site.py        # after scoring/score.py
"""
import csv, html, json, os, shutil
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, '_site')
REPO = 'https://github.com/d34dman/flowdrop-ai-bench'
ORDER = ['correct', 'degraded', 'silent', 'format', 'loud', 'control']
CELL = {'bench_0_floor': 'B0 floor', 'bench_1_reference': 'B1 reference', 'bench_2_raw_html_llm': 'B2 raw HTML → LLM',
        'bench_3_markdown_llm': 'B3 Markdown → LLM', 'bench_4_ai_agent_tool': 'B4 AI Agent + tool',
        'bench_5_react_agent': 'B5 ReAct agent', 'bench_6_agent_autonomous': 'B6 autonomous agent',
        'bench_7_react_optimized': 'B7 ReAct, URL tool', 'bench_8_react_with_tools_in_parent': 'B8 ReAct, tools in parent',
        'bench_9_reflexion_with_tools_in_parent': 'B9 Reflexion, tools in parent'}
CSS = """
:root{--bg:#fff;--fg:#1d2430;--mut:#5b6472;--line:#dde2e8;--ok:#2f8f5b;--deg:#c98a12;--sil:#c43d3d;--fmt:#7a5cc7;--loud:#777;--ctl:#9aa3ad}
@media(prefers-color-scheme:dark){:root{--bg:#14181e;--fg:#e6e9ee;--mut:#98a2ae;--line:#2b323c}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:64rem;margin:0 auto;padding:2rem 1.2rem}
h1{font-size:1.9rem;margin:.2rem 0}.sub{color:var(--mut);margin:0 0 1.5rem}
table{border-collapse:collapse;width:100%;font-size:.92rem;margin:.6rem 0 1.4rem}th,td{border-bottom:1px solid var(--line);padding:.35rem .5rem;text-align:left;vertical-align:top}
th{color:var(--mut);font-weight:600}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:0 .5rem;border-radius:1rem;color:#fff;font-size:.8rem}
.correct{background:var(--ok)}.degraded{background:var(--deg)}.silent{background:var(--sil)}.format{background:var(--fmt)}.loud{background:var(--loud)}.control{background:var(--ctl)}
.wrap{overflow-x:auto}code{font-size:.9em}.note{color:var(--mut);font-size:.9rem}
"""

def pill(c, n=None):
    return f'<span class="pill {c}">{c}{"" if n is None else " " + str(n)}</span>'

def main():
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'scores.csv'), encoding='utf-8')))
    m = json.load(open(os.path.join(ROOT, 'corpus', 'v1', 'manifest.json'), encoding='utf-8'))
    if os.path.isdir(SITE): shutil.rmtree(SITE)
    os.makedirs(SITE)
    for d in ('corpus', 'prompt', 'data', 'outputs', 'runs'):
        if os.path.isdir(os.path.join(ROOT, d)): shutil.copytree(os.path.join(ROOT, d), os.path.join(SITE, d))
    open(os.path.join(SITE, '.nojekyll'), 'w').close()

    graded = [r for r in rows if r['outcome'] not in ('control', 'stale')]
    cells = defaultdict(Counter); cost = defaultdict(list)
    for r in graded:
        k = (r['variant'], r['models'] or '-', r['page']); cells[k][r['outcome']] += 1
        if r['outcome'] == 'correct': cost[k].append(float(r['cost_usd'] or 0))
    total = Counter(r['outcome'] for r in graded)

    def esc(x): return html.escape(str(x))
    parts = [f'<title>FlowDrop AI Bench</title><style>{CSS}</style><main>',
             '<h1>FlowDrop AI Bench</h1>',
             f'<p class="sub">One task, one prompt, one owned corpus, ten workflow architectures. {len(rows)} runs, {len(graded)} graded. '
             f'Source, corpus and every run: <a href="{REPO}">{REPO.split("//")[1]}</a>.</p>',
             '<p>' + ' '.join(pill(o, total.get(o, 0)) for o in ORDER if o != 'control') + '</p>',
             '<p class="note"><b>correct</b>: every axis at threshold. <b>degraded</b>: all axes ≥ 0.75. <b>silent</b>: completed and the document is wrong. '
             '<b>format</b>: HTML came back. <b>loud</b>: nothing usable delivered. Axes and thresholds: <code>scoring/score.py</code>.</p>']
    parts.append('<h2>Outcome per cell</h2><div class="wrap"><table><tr><th>Variant</th><th>Model</th><th>Page</th><th class="n">Runs</th><th>Outcomes</th><th class="n">$ per correct run</th></tr>')
    for k in sorted(cells):
        c = cells[k]; n = sum(c.values()); cc = cost.get(k, [])
        parts.append(f'<tr><td>{esc(CELL.get(k[0], k[0]))}</td><td><code>{esc(k[1])}</code></td><td>{esc(k[2])}</td><td class="n">{n}</td>'
                     f'<td>{" ".join(pill(o, c[o]) for o in ORDER if c.get(o))}</td><td class="n">{(sum(cc)/len(cc)):.4f}</td></tr>' if cc else
                     f'<tr><td>{esc(CELL.get(k[0], k[0]))}</td><td><code>{esc(k[1])}</code></td><td>{esc(k[2])}</td><td class="n">{n}</td>'
                     f'<td>{" ".join(pill(o, c[o]) for o in ORDER if c.get(o))}</td><td class="n">—</td></tr>')
    parts.append('</table></div>')
    parts.append('<h2>Every run</h2><div class="wrap"><table><tr><th>Run</th><th>Model</th><th>Page</th>' +
                 ''.join(f'<th class="n">{a}</th>' for a in ('recall', 'recall_real', 'recall_fictional', 'precision', 'subject', 'homonym', 'fidelity', 'fabrication')) +
                 '<th class="n">glyphs</th><th class="n">leaks</th><th class="n">calls</th><th class="n">s</th><th class="n">$</th><th>Outcome</th><th>Output</th></tr>')
    for r in sorted(rows, key=lambda r: (r['variant'], r['models'], r['page'], r['ts'])):
        parts.append(f'<tr><td>{esc(CELL.get(r["variant"], r["variant"]))} <span class="note">{esc(r["tag"])}</span></td><td><code>{esc(r["models"] or "-")}</code></td><td>{esc(r["page"])}</td>' +
                     ''.join(f'<td class="n">{esc(r[a])}</td>' for a in ('recall', 'recall_real', 'recall_fictional', 'precision', 'subject', 'homonym', 'fidelity', 'fabrication')) +
                     f'<td class="n">{esc(r["glyphs"])}</td><td class="n">{esc(r["leaks"])}</td><td class="n">{esc(r["llm_calls"])}</td><td class="n">{esc(r["total_seconds"])}</td><td class="n">{esc(r["cost_usd"])}</td>'
                     f'<td>{pill(r["outcome"])}</td><td><a href="outputs/{esc(r["run_id"])}.md">md</a></td></tr>')
    parts.append('</table></div>')
    parts.append('<h2>Corpus</h2><table><tr><th>Page</th><th class="n">Gold bytes</th><th class="n">Headings</th><th class="n">Targets</th><th class="n">Homonyms</th><th class="n">Protected</th><th>Chrome mentions</th></tr>')
    for p, d in m['pages'].items():
        parts.append(f'<tr><td><a href="corpus/v1/{p}.html">{p}</a> · <a href="corpus/v1/gold/{p}.md">gold</a></td><td class="n">{d["gold_bytes"]}</td><td class="n">{d["headings"]}</td>'
                     f'<td class="n">{len(d["targets"])}</td><td class="n">{len(d["homonyms"])}</td><td class="n">{len(d["protected"])}</td><td>{esc(", ".join(f"{k} ×{v}" for k, v in d["chrome"].items()))}</td></tr>')
    parts.append(f'</table><p class="note">Glyph <code>{esc(m["glyph"])}</code>. Competitors: {esc(", ".join(m["competitors"]))}. Prompt: <a href="prompt/redact.v1.md">redact.v1.md</a> '
                 f'(sha256 {m["prompt_sha256"][:12]}). Data: <a href="data/runs.csv">runs.csv</a>, <a href="data/scores.csv">scores.csv</a>.</p>')
    parts.append(f'<h2>Contribute a run</h2><p>Set up the runner (currently the <a href="https://github.com/d34dman/flowdrop-drupal-demo">FlowDrop Drupal demo</a>), run a cell, export it, open a pull request. '
                 f'The steps are in the <a href="{REPO}#contribute-your-runs">README</a>. This page is rebuilt by CI on every merge.</p></main>')
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + '\n'.join(parts))
    print(f'site -> {SITE}/index.html ({len(rows)} runs)')

if __name__ == '__main__':
    main()
