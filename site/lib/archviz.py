"""Architecture diagrams for the benchmark cells, drawn at build time as inline SVG. Standard library only.

One small vocabulary, reused by every figure, so a reader who has decoded one diagram has decoded all
ten: a hollow dot is the workflow input, a filled dot its output, a square-cornered box is a
deterministic node, a pill is a model call, a dashed frame is an agent (the model decides what runs
inside it), small chips are tools, dotted lines are tool calls, and the outer dotted frame in B8/B9
is the parent workflow. Colour is spent once: the model call and anything that only a model can
touch wear the site accent. Everything else is currentColor and reads on both themes (bench.css,
section "architecture diagrams").

    import archviz
    archviz.figure('bench_5_react_agent')   # -> '<svg ...>...</svg>'
    archviz.legend()                         # -> the key, same vocabulary
"""
from html import escape as esc

W = 760                     # every figure shares one width so they align down the page
CHAR = 6.3                  # px per character at the 12px label size, for chip widths
STEP_H, LLM_H, CHIP_H = 46, 46, 26


def _t(x, y, s, cls='', anchor='middle', size=None, weight=None):
    st = (f' style="font-size:{size}px"' if size else '')
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}"{f" class=\"{cls}\"" if cls else ""}{st}{f" font-weight=\"{weight}\"" if weight else ""}>{esc(s)}</text>'


def _two(x, cy, label, sub, cls_sub='subl'):
    if not sub: return _t(x, cy + 4, label)
    return _t(x, cy - 3, label) + _t(x, cy + 12, sub, cls_sub)


def step(x, y, w, label, sub=None):
    """Deterministic node: does one fixed thing, no judgement."""
    return f'<g class="st"><rect x="{x}" y="{y}" width="{w}" height="{STEP_H}"/>{_two(x + w / 2, y + STEP_H / 2, label, sub)}</g>'


def llm(x, y, w, label='Model call', sub=None):
    """One model call: the box whose behaviour the benchmark is about."""
    return f'<g class="llm"><rect x="{x}" y="{y}" width="{w}" height="{LLM_H}" rx="{LLM_H / 2}"/>{_two(x + w / 2, y + LLM_H / 2, label, sub)}</g>'


def chip_w(label):
    return int(len(label) * CHAR + 22)


def chip(cx, y, label, hi=False):
    """A tool the model may call. `hi` marks the one the figure is about."""
    w = chip_w(label)
    return (f'<g class="tool{" hi" if hi else ""}"><rect x="{cx - w / 2}" y="{y}" width="{w}" height="{CHIP_H}" rx="{CHIP_H / 2}"/>'
            f'{_t(cx, y + 17, label, size=11.5)}</g>')


def io_in(x, cy, label='URL'):
    return f'<g class="io in"><circle cx="{x}" cy="{cy}" r="6"/>{_t(x, cy + 22, label, "lbl")}</g>'


def io_out(x, cy, label='Markdown'):
    return f'<g class="io out"><circle cx="{x}" cy="{cy}" r="6"/>{_t(x, cy + 22, label, "lbl")}</g>'


def arrow(x1, y1, x2, y2, label=None, cls='flow', above=True):
    """Data moving from one node to the next; the label is the payload."""
    s = f'<path class="{cls}" d="M{x1} {y1} L{x2} {y2}" marker-end="url(#arch-arrow)"/>'
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        s += _t(mx, my - 7 if above else my + 15, label, 'lbl')
    return s


def toolcall(x1, y1, x2, y2, label=None, side='r'):
    """A tool call from a model: dotted, no arrowhead, the payload that comes back as the label."""
    s = f'<path class="tl" d="M{x1} {y1} L{x2} {y2}"/>'
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        s += _t(mx + (7 if side == 'r' else -7), my + 4, label, 'lbl', anchor='start' if side == 'r' else 'end')
    return s


def frame(x, y, w, h, title, cls='agent', sub=None):
    """Agent boundary (dashed) or parent workflow (dotted): what happens inside is not fixed by the graph."""
    s = f'<g class="frame {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>{_t(x + 12, y + 16, title, "ttl", anchor="start")}'
    if sub: s += _t(x + w - 12, y + 16, sub, 'lbl', anchor='end')
    return s + '</g>'


def loop(cx, cy, label='reason · act · observe'):
    """The agent loop: a near-complete circle with an arrowhead, read as 'repeat until done'."""
    r = 11
    return (f'<g class="loopg"><path class="flow" d="M{cx + r} {cy} A{r} {r} 0 1 1 {cx} {cy - r}" marker-end="url(#arch-arrow)"/>'
            f'<path class="flow" d="M{cx} {cy - r} A{r} {r} 0 0 0 {cx - r} {cy}" style="marker:none"/>'
            f'{_t(cx + r + 8, cy + 4, label, "lbl", anchor="start")}</g>')


def port(x, y, label=None, anchor='middle', dy=-10):
    s = f'<circle class="port" cx="{x}" cy="{y}" r="4"/>'
    if label: s += _t(x, y + dy, label, 'lbl', anchor=anchor)
    return s


def svg(h, body, aria):
    return (f'<svg class="arch" role="img" aria-label="{esc(aria)}" viewBox="0 0 {W} {h}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><marker id="arch-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0.5 L10 5 L0 9.5 z" fill="currentColor"/></marker></defs>{body}</svg>')


# ------------------------------------------------------------------ straight pipelines (B0-B3)

def _chain(cy, items):
    """Lay out io/step/llm nodes left to right with labelled arrows between them, centred in W.
    items: list of ('in'|'out', label) | ('step'|'llm', label, sub, w) | ('edge', payload)."""
    GAP = 66
    widths = []
    for it in items:
        if it[0] in ('in', 'out'): widths.append(12)
        elif it[0] == 'edge': widths.append(GAP)
        else: widths.append(it[3])
    x = (W - sum(widths)) / 2
    out, prev_right = [], None
    for it, w in zip(items, widths):
        if it[0] == 'in': out.append(io_in(x + 6, cy, it[1])); prev_right = x + 12
        elif it[0] == 'out': out.append(io_out(x + 6, cy, it[1])); prev_right = x + 12
        elif it[0] == 'edge': out.append(arrow(prev_right + 2, cy, x + w - 2, cy, it[1])); prev_right = None
        elif it[0] == 'step': out.append(step(x, cy - STEP_H / 2, w, it[1], it[2])); prev_right = x + w
        elif it[0] == 'llm': out.append(llm(x, cy - LLM_H / 2, w, it[1], it[2])); prev_right = x + w
        x += w
    return ''.join(out)


def b0():
    body = _chain(60, [('in', 'URL'), ('edge', 'URL, untouched'), ('step', 'Output', 'nothing runs', 130), ('edge', ''), ('out', 'the URL')])
    return svg(110, body, 'B0: the URL passes from input to output with no fetch, no conversion and no model call.')


def b1():
    body = _chain(60, [('in', 'URL'), ('edge', 'URL'), ('step', 'Fetch', 'HTTP node', 110), ('edge', 'HTML'),
                       ('step', 'To Markdown', 'html_to_markdown node', 160), ('edge', 'Markdown'), ('out', 'Markdown, unredacted')])
    return svg(110, body, 'B1: fetch, then a deterministic HTML to Markdown node; no model call, nothing redacted.')


def b2():
    body = _chain(60, [('in', 'URL'), ('edge', 'URL'), ('step', 'Fetch', 'HTTP node', 110), ('edge', 'raw HTML'),
                       ('llm', 'Model call', 'convert and redact', 170), ('edge', ''), ('out', 'Markdown')])
    return svg(110, body, 'B2: fetch, then one model call receives the raw HTML and both converts and redacts.')


def b3():
    body = _chain(60, [('in', 'URL'), ('edge', 'URL'), ('step', 'Fetch', 'HTTP node', 100), ('edge', 'HTML'),
                       ('step', 'To Markdown', 'node', 130), ('edge', 'Markdown'), ('llm', 'Model call', 'redact only', 140),
                       ('edge', ''), ('out', 'Markdown')])
    return svg(110, body, 'B3: fetch, deterministic conversion, then one model call that only redacts.')


# ------------------------------------------------------------------ agents (B4-B9)

def _agent(x, y, w, h, title, sub, llm_label, llm_sub, tools, hi=None, loop_label='reason · act · observe · repeat', tool_labels=None):
    """A dashed agent frame with the model call at the top, the loop glyph beside it, tool chips along the
    bottom and a dotted call line to each, labelled with what the tool returns."""
    out = [frame(x, y, w, h, title, 'agent', sub)]
    lw = 150
    lx, ly = x + 28, y + 34
    out.append(llm(lx, ly, lw, llm_label, llm_sub))
    out.append(loop(lx + lw + 26, ly + LLM_H / 2, loop_label))
    n = len(tools)
    if n:
        cy = y + h - 36 - CHIP_H / 2
        span = w - 60
        gap = span / n
        for i, t in enumerate(tools):
            cx = x + 30 + gap * (i + .5)
            out.append(chip(cx, cy - CHIP_H / 2, t, hi=(t == hi)))
            out.append(toolcall(lx + lw / 2, ly + LLM_H, cx, cy - CHIP_H / 2))
            lbl = (tool_labels or {}).get(t)
            if lbl: out.append(_t(cx, cy + CHIP_H / 2 + 14, lbl, 'lbl'))
    return ''.join(out)


def b4():
    cy = 105
    body = io_in(30, cy) + arrow(38, cy, 96, cy, 'URL') + step(100, cy - STEP_H / 2, 100, 'Fetch', 'HTTP node')
    body += arrow(202, cy, 268, cy, 'HTML')
    body += _agent(272, 22, 330, 180, 'Drupal AI Agent', 'given the HTML', 'Model call', 'redact, may convert',
                   ['html_to_markdown'], loop_label='may or may not call it', tool_labels={'html_to_markdown': 'returns Markdown'})
    body += arrow(604, cy, 700, cy, 'Markdown') + io_out(708, cy, '')
    return svg(216, body, 'B4: the graph fetches the HTML and hands it to a Drupal AI Agent that owns a to-Markdown tool and chooses when to use it.')


def _url_agent(title, sub, tools, hi=None, tool_labels=None, aria=''):
    cy = 120
    body = io_in(30, cy) + arrow(38, cy, 196, cy, 'URL only')
    body += _agent(200, 22, 400, 210, title, sub, 'Model call', 'plan, call tools, redact', tools, hi=hi, tool_labels=tool_labels)
    body += arrow(602, cy, 700, cy, 'Markdown') + io_out(708, cy, '')
    return svg(246, body, aria)


def b5():
    return _url_agent('FlowDrop ReAct agent', 'tools in its own toolbox', ['Fetch', 'To Markdown'],
                      tool_labels={'Fetch': 'returns HTML', 'To Markdown': 'HTML in, Markdown back'},
                      aria='B5: only a URL goes in; a FlowDrop ReAct agent holds a fetch tool and a to-Markdown tool and loops until it has redacted Markdown. The page text passes through the model between the two tools.')


def b6():
    return _url_agent('Drupal AI Agent', 'tools in its own configuration', ['http_fetch', 'html_to_markdown'],
                      tool_labels={'http_fetch': 'returns HTML', 'html_to_markdown': 'HTML in, Markdown back'},
                      aria='B6: the Drupal AI Agents peer of B5; only a URL goes in and the agent fetches, converts and redacts with its own tools.')


def b7():
    return _url_agent('FlowDrop ReAct agent', 'one more tool than B5', ['Fetch', 'To Markdown', 'URL to Markdown'], hi='URL to Markdown',
                      tool_labels={'Fetch': 'returns HTML', 'To Markdown': 'Markdown back', 'URL to Markdown': 'URL in, Markdown back'},
                      aria='B7: B5 plus a fused URL-to-Markdown tool, so the page can be fetched and converted in one call without its text passing through the model.')


def _parent(engine_title, engine_sub, engine_body_fn, aria, h=290):
    """B8/B9: a parent workflow frame owning the tool nodes, a bare engine frame inside it, dotted lines
    from the tools up to the engine's tool port."""
    px, py, pw, ph = 110, 14, 540, h - 28
    ex, ey, ew, eh = 200, 44, 360, 118
    cy = ey + eh / 2 + 6
    body = frame(px, py, pw, ph, 'parent workflow', 'parent', 'owns the tools')
    body += frame(ex, ey, ew, eh, engine_title, 'agent', engine_sub)
    body += engine_body_fn(ex, ey, ew, eh)
    # tools as nodes of the parent, wired into one port on the engine
    port_x, port_y = ex + ew / 2, ey + eh
    body += port(port_x, port_y)
    body += _t(port_x + 12, port_y + 30, 'tools, passed in as an execution argument', 'lbl', anchor='start')
    tools = ['Fetch', 'To Markdown', 'URL to Markdown']
    labels = {'Fetch': 'returns HTML', 'To Markdown': 'Markdown back', 'URL to Markdown': 'URL in, Markdown back'}
    ty = py + ph - 24 - CHIP_H
    gap = (pw - 60) / len(tools)
    for i, t in enumerate(tools):
        cx = px + 30 + gap * (i + .5)
        body += chip(cx, ty, t)
        body += f'<path class="tl" d="M{cx} {ty} L{cx} {port_y + 34} L{port_x} {port_y + 34} L{port_x} {port_y + 4}"/>'
        body += _t(cx, ty + CHIP_H + 15, labels[t], 'lbl')
    body += io_in(30, cy) + arrow(38, cy, ex - 4, cy, 'URL only')
    body += arrow(ex + ew + 2, cy, 700, cy, 'Markdown') + io_out(708, cy, '')
    return svg(h, body, aria)


def b8():
    def engine(ex, ey, ew, eh):
        lw = 150; lx = ex + 30; ly = ey + 40
        return llm(lx, ly, lw, 'Model call', 'plan, call tools, redact') + loop(lx + lw + 26, ly + LLM_H / 2, 'reason · act · observe')
    return _parent('ReAct engine', 'own toolbox empty', engine,
                   'B8: the same three tools as B7 are nodes of the parent workflow and are handed to a bare ReAct engine as an execution argument.')


def b9():
    def engine(ex, ey, ew, eh):
        lw = 104; ly = ey + 36
        ax = ex + 26; kx = ex + ew - 26 - lw
        s = llm(ax, ly, lw, 'Actor', 'plan, tools, draft') + llm(kx, ly, lw, 'Critic', 'review the draft')
        mid = ly + LLM_H / 2
        s += arrow(ax + lw + 2, mid - 8, kx - 2, mid - 8, 'draft')
        s += f'<path class="flow" d="M{kx - 2} {mid + 10} L{ax + lw + 2} {mid + 10}" marker-end="url(#arch-arrow)"/>'
        s += _t((ax + lw + kx) / 2, mid + 26, 'REVISE, up to 3 times', 'lbl')
        return s
    return _parent('Reflexion engine', 'own toolbox empty', engine,
                   'B9: B8 with a Reflexion engine; a critic model call reviews the actor\'s draft against the rules and returns it for revision up to three times before it is emitted.', h=300)


FIGURES = {'bench_0_floor': b0, 'bench_1_reference': b1, 'bench_2_raw_html_llm': b2, 'bench_3_markdown_llm': b3,
           'bench_4_ai_agent_tool': b4, 'bench_5_react_agent': b5, 'bench_6_agent_autonomous': b6,
           'bench_7_react_optimized': b7, 'bench_8_react_with_tools_in_parent': b8,
           'bench_9_reflexion_with_tools_in_parent': b9}


def figure(cell_id):
    return FIGURES[cell_id]()


def legend():
    """The vocabulary, drawn once, two rows."""
    y1, y2 = 34, 104
    body = io_in(30, y1, 'input') + io_out(90, y1, 'output')
    body += step(140, y1 - STEP_H / 2, 150, 'Deterministic node', 'fixed behaviour')
    body += llm(320, y1 - LLM_H / 2, 150, 'Model call', 'the model decides')
    body += frame(500, y1 - 30, 230, 60, 'Agent', 'agent', 'model chooses what runs')
    body += chip(90, y2 - CHIP_H / 2, 'Tool') + _t(90, y2 + 32, 'a tool the model may call', 'lbl')
    body += f'<path class="tl" d="M180 {y2} L250 {y2}"/>' + _t(215, y2 + 22, 'tool call', 'lbl')
    body += f'<path class="flow" d="M285 {y2} L375 {y2}" marker-end="url(#arch-arrow)"/>' + _t(330, y2 - 8, 'HTML', 'lbl') + _t(330, y2 + 22, 'data, labelled with its payload', 'lbl')
    body += loop(440, y2, 'the agent loop, until done')
    body += frame(560, y2 - 30, 180, 44, 'parent workflow', 'parent') + _t(650, y2 + 32, 'the graph that owns the tools', 'lbl')
    return svg(150, body, 'Legend: hollow dot input, filled dot output, square box deterministic node, pill model call, dashed frame agent, chip tool, dotted line tool call, arrow data flow labelled with its payload, circular arrow the agent loop, dotted frame parent workflow.')
