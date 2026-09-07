"""The ten cells explained: a ladder from 'the graph decides everything' to 'the model decides
everything', one figure per cell drawn from site/lib/archviz.py, and the peer relations that make
the cells comparable. Static: no filters, no data. Anchored by cell code (#B4) so every other
page can link a cell label here."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lib'))
import archviz

FAMILIES = [
    ('control', 'Controls, no model', 'The floor and the reference. Free, deterministic, and the yardstick for time and structure.'),
    ('one-call', 'One model call', 'A fixed graph with a single model call in it. The graph decides the order of work; the model does one job.'),
    ('agent', 'Agents', 'The model decides what runs and when. What moves between cells is the input it is given, the tools it holds, and who owns them.'),
]


def build(ctx):
    from framework import esc
    cells = ctx.CELLS
    by_id = {c['id']: c for c in cells}
    code = lambda cid: by_id[cid]['code']

    # 1. the ladder: ten chips in three families, each a jump link
    ladder = ''.join(
        f'<div class="fam"><h3>{esc(title)}</h3><p>{esc(blurb)}</p><div class="chips">' +
        ''.join(f'<a href="#{c["code"]}"><b>{c["code"]}</b> {esc(c["name"])}</a>' for c in cells if c['family'] == fam) +
        '</div></div>' for fam, title, blurb in FAMILIES)

    # 2. the reading order: which pairs differ by one thing
    pairs = [
        ('bench_2_raw_html_llm', 'bench_3_markdown_llm', 'Who converts. B2 makes the model transcribe HTML; B3 converts in a node and spends the model on redaction only.'),
        ('bench_3_markdown_llm', 'bench_4_ai_agent_tool', 'Who sequences. Same two jobs; in B3 the graph orders them, in B4 the agent decides whether and when to call the converter.'),
        ('bench_5_react_agent', 'bench_6_agent_autonomous', 'Which runtime. Same autonomy, same tools, same prompt; B5 is a FlowDrop ReAct agent, B6 a Drupal AI Agent.'),
        ('bench_5_react_agent', 'bench_7_react_optimized', 'Tool shape. B7 adds one fused fetch-and-convert tool, so the page text need not pass through the model.'),
        ('bench_7_react_optimized', 'bench_8_react_with_tools_in_parent', 'Tool ownership. Same tools; in B7 the agent holds them, in B8 they are nodes of the parent workflow handed in as an argument.'),
        ('bench_8_react_with_tools_in_parent', 'bench_9_reflexion_with_tools_in_parent', 'A critic. B9 is B8 with a review loop: a second model call checks the draft and can send it back, up to three times.'),
    ]
    pair_rows = ''.join(
        f'<tr><td><a href="#{code(a)}">{code(a)}</a> <span class="vs">vs</span> <a href="#{code(b)}">{code(b)}</a></td><td>{esc(t)}</td></tr>'
        for a, b, t in pairs)

    # 3. one figure per cell
    figs = ''
    for c in cells:
        peers = ', '.join(f'<a href="#{code(p)}">{code(p)}</a>' for p in c['peers'])
        figs += (f'<section class="cell" id="{c["code"]}"><h3><span class="code">{c["code"]}</span> {esc(c["name"])}</h3>'
                 f'<p class="shape">{esc(c["shape"])}</p>'
                 f'<figure>{archviz.figure(c["id"])}<figcaption><b>What it tests.</b> {esc(c["tests"])}'
                 + (f' <span class="peers">Read against {peers}.</span>' if peers else '') +
                 f'</figcaption></figure>'
                 f'<p class="also">On the other pages this cell is <code>{esc(c["label"])}</code>. '
                 f'<a data-nav href="../by-benchmark/?benchmark={c["id"]}">Its results across models</a>.</p></section>')

    body = (f'<p class="note">Every cell runs the same prompt on the same pages. What differs is the architecture around the model: '
            f'what it is given (a URL, the HTML, or Markdown), whether it runs once or in a loop, which tools it holds, and who owns them. '
            f'The labels used everywhere on this site read <b>input the model sees → who does the work → tools</b>.</p>'
            f'<h2>The ladder</h2><div class="ladder">{ladder}</div>'
            f'<h2>Read them in pairs</h2><p class="note">Each pair differs by one decision, so the gap between the two rows in the '
            f'<a data-nav href="../matrix/">matrix</a> or the <a data-nav href="../cost/">cost figures</a> is the price or the value of that decision.</p>'
            f'<div class="wrap"><table class="pairs">{pair_rows}</table></div>'
            f'<h2>Every cell</h2><figure class="legend-fig">{archviz.legend()}<figcaption>The vocabulary every figure below uses.</figcaption></figure>'
            f'{figs}')
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb']))
