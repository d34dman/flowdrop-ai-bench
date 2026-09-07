"""Architecture diagrams for the benchmark cells, drawn at build time as inline SVG. Standard library only.

One small vocabulary, reused by every figure, so a reader who has decoded one diagram has decoded all
ten. Every role has a shape, an icon and a colour, and keeps them on every page:

    input / output      hollow ring in, filled dot out; ink
    deterministic node  square-cornered card, cube icon; slate
    model call          filled pill on the accent gradient, sparkle icon; the only strongly filled shape
    agent               dashed violet frame on a violet wash: the model decides what runs inside it
    tool                teal chip, hexagon icon; a tool the model may call
    tool call           dashed teal curve from the model to the chip, arrowhead at the chip
    data flow           solid ink arrow, the payload named in a pill on the line
    the agent loop      one open circle with an arrowhead, read as "repeat until done"
    parent workflow     dotted amber frame on an amber wash: the graph that owns the tools

Colours are CSS custom properties (bench.css, section "architecture diagrams") so the figures follow
the light and dark themes; nothing here hard-codes a colour.

    import archviz
    archviz.figure('bench_5_react_agent')   # -> '<svg ...>...</svg>'
    archviz.legend()                         # -> the key, same vocabulary
"""
from html import escape as esc

W = 760                     # every figure shares one width so they align down the page
CH, CH_SUB, CH_LBL = 6.9, 5.8, 6.1   # px per character at the label, sub and edge-label sizes, for widths
NODE_H, CHIP_H = 52, 30
ICON = 16                   # icon box, drawn at 0..16 and translated into place


# ------------------------------------------------------------------ primitives

def _t(x, y, s, cls='', anchor='middle', size=None, weight=None):
    st = f' style="font-size:{size}px"' if size else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{f" class=\"{cls}\"" if cls else ""}{st}'
            f'{f" font-weight=\"{weight}\"" if weight else ""}>{esc(s)}</text>')


def _icon(kind, x, y):
    """A 16px glyph at (x, y): 'spark' model call, 'cube' deterministic node, 'hex' tool."""
    if kind == 'spark':
        d = 'M8 0.5C8.7 4.7 11.3 7.3 15.5 8C11.3 8.7 8.7 11.3 8 15.5C7.3 11.3 4.7 8.7 0.5 8C4.7 7.3 7.3 4.7 8 0.5Z'
        return f'<path class="ic" transform="translate({x:.1f} {y:.1f})" d="{d}"/>'
    if kind == 'cube':
        d = 'M8 1.2L14.5 4.8V11.2L8 14.8L1.5 11.2V4.8Z M1.5 4.8L8 8.4L14.5 4.8 M8 8.4V14.8'
        return f'<path class="ic ln" transform="translate({x:.1f} {y:.1f})" d="{d}"/>'
    if kind == 'hex':
        d = 'M8 1L14.1 4.5V11.5L8 15L1.9 11.5V4.5Z'
        return (f'<g transform="translate({x:.1f} {y:.1f})"><path class="ic" d="{d}"/>'
                f'<circle class="ic-hole" cx="8" cy="8" r="2.6"/></g>')
    return ''


def _node(cls, icon, x, y, w, h, label, sub, rx):
    """Card with an icon on the left and one or two lines of text after it."""
    cy = y + h / 2
    tx = x + 14 + ICON + 10
    s = f'<g class="{cls}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{rx}"/>'
    s += _icon(icon, x + 14, cy - ICON / 2)
    if sub: s += _t(tx, cy - 3, label, anchor='start') + _t(tx, cy + 12.5, sub, 'subl', anchor='start')
    else: s += _t(tx, cy + 4.5, label, anchor='start')
    return s + '</g>'


def node_w(label, sub=None):
    return int(14 + ICON + 10 + max(len(label) * CH, len(sub or '') * CH_SUB) + 16)


def step(x, y, label, sub=None, w=None):
    """Deterministic node: does one fixed thing, no judgement."""
    w = w or node_w(label, sub)
    return _node('st', 'cube', x, y, w, NODE_H, label, sub, 6)


def llm(x, y, label='Model call', sub=None, w=None):
    """One model call: the box whose behaviour the benchmark is about."""
    w = w or node_w(label, sub)
    return _node('llm', 'spark', x, y, w, NODE_H, label, sub, NODE_H / 2)


def chip_w(label):
    return int(12 + 14 + 7 + len(label) * 6.5 + 14)


def chip(cx, y, label, hi=False):
    """A tool the model may call. `hi` marks the one the figure is about."""
    w = chip_w(label)
    x = cx - w / 2
    s = (f'<g class="tool{" hi" if hi else ""}"><rect x="{x:.1f}" y="{y}" width="{w}" height="{CHIP_H}" rx="{CHIP_H / 2}"/>'
         f'<g transform="translate({x + 12:.1f} {y + CHIP_H / 2 - 7:.1f}) scale(.875)">{_icon("hex", 0, 0)}</g>'
         f'{_t(x + 12 + 14 + 7, y + CHIP_H / 2 + 4.5, label, anchor="start", size=12.5)}')
    if hi: s += f'<circle class="badge" cx="{x + w - 2:.1f}" cy="{y + 2}" r="7"/><text class="badge-t" x="{x + w - 2:.1f}" y="{y + 5.5}" text-anchor="middle">+</text>'
    return s + '</g>'


def io_in(x, cy, label='URL'):
    return f'<g class="io in"><circle cx="{x}" cy="{cy}" r="7"/><circle class="dot" cx="{x}" cy="{cy}" r="2.4"/>{_t(x, cy + 25, label, "lbl")}</g>'


def io_out(x, cy, label='Markdown'):
    return f'<g class="io out"><circle cx="{x}" cy="{cy}" r="7"/>{_t(x, cy + 25, label, "lbl")}</g>'


def pill(x, y, s, cls='lbl'):
    """An edge label with a page-coloured backing so it may sit on a line."""
    w = len(s) * CH_LBL + 12
    return (f'<rect class="lblbg" x="{x - w / 2:.1f}" y="{y - 10}" width="{w:.1f}" height="16" rx="8"/>'
            + _t(x, y + 2, s, cls))


def arrow(x1, y1, x2, y2, label=None, above=True):
    """Data moving from one node to the next; the label is the payload."""
    s = f'<path class="flow" d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" marker-end="url(#arch-arrow)"/>'
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        s += pill(mx, my - 13 if above else my + 15, label)
    return s


def toolcall(x1, y1, x2, y2):
    """A tool call from a model: dashed teal curve, arrowhead at the tool."""
    c = (y2 - y1) * .55
    return (f'<path class="tl" d="M{x1:.1f} {y1:.1f} C{x1:.1f} {y1 + c:.1f} {x2:.1f} {y2 - c:.1f} {x2:.1f} {y2:.1f}" '
            f'marker-end="url(#arch-arrow-tool)"/>')


def ortho(pts, r=8):
    """A polyline with rounded corners through pts, as a path 'd'."""
    if len(pts) < 3: return 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
    for i in range(1, len(pts) - 1):
        (px, py), (cx, cy), (nx, ny) = pts[i - 1], pts[i], pts[i + 1]
        dx1, dy1 = cx - px, cy - py; l1 = (dx1 ** 2 + dy1 ** 2) ** .5 or 1
        dx2, dy2 = nx - cx, ny - cy; l2 = (dx2 ** 2 + dy2 ** 2) ** .5 or 1
        rr = min(r, l1 / 2, l2 / 2)
        d += f' L{cx - dx1 / l1 * rr:.1f} {cy - dy1 / l1 * rr:.1f} Q{cx:.1f} {cy:.1f} {cx + dx2 / l2 * rr:.1f} {cy + dy2 / l2 * rr:.1f}'
    return d + f' L{pts[-1][0]:.1f} {pts[-1][1]:.1f}'


def frame(x, y, w, h, title, cls='agent', sub=None):
    """Agent boundary (dashed) or parent workflow (dotted): what happens inside is not fixed by the graph."""
    s = (f'<g class="frame {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14"/>'
         f'<rect class="tab" x="{x + 14}" y="{y - 11}" width="{len(title) * 8.7 + 26:.1f}" height="22" rx="11"/>'
         f'{_t(x + 27, y + 4.5, title, "ttl", anchor="start")}')
    if sub: s += _t(x + w - 16, y + 22, sub, 'lbl', anchor='end')
    return s + '</g>'


def loop(cx, cy, label='reason · act · observe'):
    """The agent loop: one open circle, gap on the right, arrowhead at the end of the arc."""
    import math
    r, a = 12, math.radians(38)
    sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)      # start, lower right
    ex, ey = cx + r * math.cos(a), cy - r * math.sin(a)      # end, upper right
    return (f'<g class="loopg"><path d="M{sx:.1f} {sy:.1f} A{r} {r} 0 1 1 {ex:.1f} {ey:.1f}" marker-end="url(#arch-arrow-loop)"/>'
            f'{_t(cx + r + 12, cy + 4, label, "lbl", anchor="start")}</g>')


def port(x, y):
    return f'<circle class="port" cx="{x}" cy="{y}" r="5"/>'


def svg(h, body, aria):
    return (f'<svg class="arch" role="img" aria-label="{esc(aria)}" viewBox="0 0 {W} {h}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs>'
            f'<marker id="arch-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 1 L10 5 L0 9 z" class="mk-flow"/></marker>'
            f'<marker id="arch-arrow-tool" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0 1 L10 5 L0 9 z" class="mk-tool"/></marker>'
            f'<marker id="arch-arrow-loop" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            f'<path d="M0 1 L10 5 L0 9 z" class="mk-loop"/></marker>'
            f'<linearGradient id="arch-llm-grad" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" class="g0"/><stop offset="1" class="g1"/></linearGradient>'
            f'<filter id="arch-shadow" x="-10%" y="-20%" width="120%" height="150%">'
            f'<feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#000" flood-opacity=".14"/></filter>'
            f'</defs>{body}</svg>')


# ------------------------------------------------------------------ straight pipelines (B0-B3)

def _chain(cy, items):
    """Lay out io/step/llm nodes left to right with labelled arrows between them, centred in W.
    items: list of ('in'|'out', label) | ('step'|'llm', label, sub) | ('edge', payload)."""
    widths, edges = [], 0
    for it in items:
        if it[0] in ('in', 'out'): widths.append(14)
        elif it[0] == 'edge': widths.append(0); edges += 1
        else: widths.append(node_w(it[1], it[2]))
    gap = min(92, (W - 48 - sum(widths)) / max(edges, 1))
    widths = [gap if it[0] == 'edge' else w for it, w in zip(items, widths)]
    x = (W - sum(widths)) / 2
    out, prev_right = [], None
    for it, w in zip(items, widths):
        if it[0] == 'in': out.append(io_in(x + 7, cy, it[1])); prev_right = x + 14
        elif it[0] == 'out': out.append(io_out(x + 7, cy, it[1])); prev_right = x + 14
        elif it[0] == 'edge': out.append(arrow(prev_right + 3, cy, x + w - 3, cy, it[1])); prev_right = None
        elif it[0] == 'step': out.append(step(x, cy - NODE_H / 2, it[1], it[2])); prev_right = x + w
        elif it[0] == 'llm': out.append(llm(x, cy - NODE_H / 2, it[1], it[2])); prev_right = x + w
        x += w
    return ''.join(out)


def b0():
    body = _chain(62, [('in', 'URL'), ('edge', 'URL, untouched'), ('step', 'Output', 'nothing runs'), ('edge', ''), ('out', 'the URL')])
    return svg(118, body, 'B0: the URL passes from input to output with no fetch, no conversion and no model call.')


def b1():
    body = _chain(62, [('in', 'URL'), ('edge', 'URL'), ('step', 'Fetch', 'HTTP node'), ('edge', 'HTML'),
                       ('step', 'To Markdown', 'html_to_markdown node'), ('edge', 'Markdown'), ('out', 'Markdown, unredacted')])
    return svg(118, body, 'B1: fetch, then a deterministic HTML to Markdown node; no model call, nothing redacted.')


def b2():
    body = _chain(62, [('in', 'URL'), ('edge', 'URL'), ('step', 'Fetch', 'HTTP node'), ('edge', 'raw HTML'),
                       ('llm', 'Model call', 'convert and redact'), ('edge', ''), ('out', 'Markdown')])
    return svg(118, body, 'B2: fetch, then one model call receives the raw HTML and both converts and redacts.')


def b3():
    body = _chain(62, [('in', 'URL'), ('edge', 'URL'), ('step', 'Fetch', 'HTTP node'), ('edge', 'HTML'),
                       ('step', 'To Markdown', 'node'), ('edge', 'Markdown'), ('llm', 'Model call', 'redact only'),
                       ('edge', ''), ('out', 'Markdown')])
    return svg(118, body, 'B3: fetch, deterministic conversion, then one model call that only redacts.')


# ------------------------------------------------------------------ agents (B4-B9)

def _agent_w(tools, min_w):
    """Frame width that fits the chips with a fixed gap between them."""
    need = sum(chip_w(t) for t in tools) + 22 * (len(tools) - 1) + 2 * 34
    return max(min_w, need)


def _agent(x, y, w, h, title, sub, llm_label, llm_sub, tools, hi=None, loop_label='reason · act · observe · repeat', tool_labels=None):
    """A dashed agent frame with the model call at the top, the loop glyph beside it, tool chips along the
    bottom and a dashed call curve to each, labelled with what the tool returns."""
    out = [frame(x, y, w, h, title, 'agent', sub)]
    lw = node_w(llm_label, llm_sub)
    lx, ly = x + 28, y + 40
    out.append(llm(lx, ly, llm_label, llm_sub, w=lw))
    out.append(loop(lx + lw + 30, ly + NODE_H / 2, loop_label))
    if tools:
        cy = y + h - 44 - CHIP_H / 2
        widths = [chip_w(t) for t in tools]
        gap = (w - 2 * 34 - sum(widths)) / max(len(tools) - 1, 1) if len(tools) > 1 else 0
        cx0 = x + (w - sum(widths) - gap * (len(tools) - 1)) / 2
        for t, cw in zip(tools, widths):
            cx = cx0 + cw / 2
            out.append(toolcall(lx + lw / 2, ly + NODE_H, cx, cy - CHIP_H / 2 - 1))
            out.append(chip(cx, cy - CHIP_H / 2, t, hi=(t == hi)))
            lbl = (tool_labels or {}).get(t)
            if lbl: out.append(_t(cx, cy + CHIP_H / 2 + 16, lbl, 'lbl'))
            cx0 += cw + gap
    return ''.join(out)


def b4():
    cy = 116
    fw = node_w('Fetch', 'HTTP node')
    body = io_in(26, cy) + arrow(36, cy, 86, cy, 'URL') + step(90, cy - NODE_H / 2, 'Fetch', 'HTTP node', w=fw)
    ax = 90 + fw + 62
    body += arrow(90 + fw + 3, cy, ax - 3, cy, 'HTML')
    aw = 380
    body += _agent(ax, 30, aw, 186, 'Drupal AI Agent', 'given the HTML', 'Model call', 'redact, may convert',
                   ['html_to_markdown'], loop_label='may skip the tool', tool_labels={'html_to_markdown': 'returns Markdown'})
    body += arrow(ax + aw + 3, cy, 712, cy, 'Markdown') + io_out(722, cy, '')
    return svg(232, body, 'B4: the graph fetches the HTML and hands it to a Drupal AI Agent that owns a to-Markdown tool and chooses when to use it.')


def _url_agent(title, sub, tools, hi=None, tool_labels=None, aria=''):
    cy = 130
    aw = _agent_w(tools, 400)
    ax = (W - aw) / 2 + 16
    body = io_in(30, cy) + arrow(40, cy, ax - 3, cy, 'URL only')
    body += _agent(ax, 30, aw, 216, title, sub, 'Model call', 'plan, call tools, redact', tools, hi=hi, tool_labels=tool_labels)
    body += arrow(ax + aw + 3, cy, 712, cy, 'Markdown') + io_out(722, cy, '')
    return svg(262, body, aria)


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


def _parent(engine_title, engine_sub, engine_body_fn, aria, ew=380):
    """B8/B9: a parent workflow frame owning the tool nodes, a bare engine frame inside it, a bus from the
    tools up to the engine's tool port."""
    tools = ['Fetch', 'To Markdown', 'URL to Markdown']
    labels = {'Fetch': 'returns HTML', 'To Markdown': 'Markdown back', 'URL to Markdown': 'URL in, Markdown back'}
    px, py, pw = 96, 24, 568
    ex, ey, eh = (W - ew) / 2 + 16, 58, 126
    cy = ey + eh / 2 + 4
    port_x, port_y = ex + ew / 2, ey + eh
    bus_y = port_y + 34
    ty = bus_y + 30
    ph = ty + CHIP_H + 16 + 26 - py
    h = py + ph + 18
    body = frame(px, py, pw, ph, 'parent workflow', 'parent', 'owns the tools')
    body += frame(ex, ey, ew, eh, engine_title, 'agent', engine_sub)
    body += engine_body_fn(ex, ey, ew, eh)
    widths = [chip_w(t) for t in tools]
    gap = (pw - 2 * 40 - sum(widths)) / (len(tools) - 1)
    cx0 = px + 40
    centres = []
    for cw in widths:
        centres.append(cx0 + cw / 2); cx0 += cw + gap
    for cx in centres:
        body += f'<path class="tl bus" d="{ortho([(cx, ty), (cx, bus_y), (port_x, bus_y), (port_x, port_y + 8)])}"/>'
    body += f'<path class="tl bus" d="M{port_x} {bus_y} L{port_x} {port_y + 8}" marker-end="url(#arch-arrow-tool)"/>'
    for t, cx in zip(tools, centres):
        body += chip(cx, ty, t)
        body += _t(cx, ty + CHIP_H + 16, labels[t], 'lbl')
    body += port(port_x, port_y)
    body += _t(port_x + 12, port_y + 22, 'tools, passed in as an execution argument', 'lbl', anchor='start')
    body += io_in(30, cy) + arrow(40, cy, ex - 3, cy, 'URL only')
    body += arrow(ex + ew + 3, cy, 712, cy, 'Markdown') + io_out(722, cy, '')
    return svg(h, body, aria)


def b8():
    def engine(ex, ey, ew, eh):
        lw = node_w('Model call', 'plan, call tools, redact'); lx = ex + 30; ly = ey + 40
        return llm(lx, ly, 'Model call', 'plan, call tools, redact', w=lw) + loop(lx + lw + 30, ly + NODE_H / 2, 'reason · act · observe')
    return _parent('ReAct engine', 'own toolbox empty', engine,
                   'B8: the same three tools as B7 are nodes of the parent workflow and are handed to a bare ReAct engine as an execution argument.', ew=420)


def b9():
    def engine(ex, ey, ew, eh):
        lw = max(node_w('Actor', 'plan, tools, draft'), node_w('Critic', 'review the draft')); ly = ey + 36
        ax = ex + 24; kx = ex + ew - 24 - lw
        s = llm(ax, ly, 'Actor', 'plan, tools, draft', w=lw) + llm(kx, ly, 'Critic', 'review the draft', w=lw)
        mid = ly + NODE_H / 2
        s += f'<path class="flow" d="M{ax + lw + 3} {mid - 9} L{kx - 3} {mid - 9}" marker-end="url(#arch-arrow)"/>'
        s += pill((ax + lw + kx) / 2, mid - 9, 'draft')
        s += f'<path class="flow" d="M{kx - 3} {mid + 11} L{ax + lw + 3} {mid + 11}" marker-end="url(#arch-arrow)"/>'
        s += pill((ax + lw + kx) / 2, mid + 30, 'REVISE, up to 3 times')
        return s
    return _parent('Reflexion engine', 'own toolbox empty', engine,
                   'B9: B8 with a Reflexion engine; a critic model call reviews the actor\'s draft against the rules and returns it for revision up to three times before it is emitted.', ew=440)


FIGURES = {'bench_0_floor': b0, 'bench_1_reference': b1, 'bench_2_raw_html_llm': b2, 'bench_3_markdown_llm': b3,
           'bench_4_ai_agent_tool': b4, 'bench_5_react_agent': b5, 'bench_6_agent_autonomous': b6,
           'bench_7_react_optimized': b7, 'bench_8_react_with_tools_in_parent': b8,
           'bench_9_reflexion_with_tools_in_parent': b9}


def figure(cell_id):
    return FIGURES[cell_id]()


def legend():
    """The vocabulary, drawn once, two rows."""
    y1, y2 = 48, 128
    body = io_in(30, y1, 'input') + io_out(86, y1, 'output')
    body += step(130, y1 - NODE_H / 2, 'Deterministic node', 'fixed behaviour')
    sw = node_w('Deterministic node', 'fixed behaviour')
    lx = 130 + sw + 22
    body += llm(lx, y1 - NODE_H / 2, 'Model call', 'the model decides')
    lw = node_w('Model call', 'the model decides')
    fx = lx + lw + 26
    body += frame(fx, y1 - 30, W - fx - 8, 62, 'Agent', 'agent', 'model chooses what runs')
    body += chip(74, y2 - CHIP_H / 2, 'Tool') + _t(74, y2 + 34, 'a tool the model may call', 'lbl')
    body += f'<path class="tl" d="M150 {y2} L232 {y2}" marker-end="url(#arch-arrow-tool)"/>' + _t(191, y2 + 24, 'tool call', 'lbl')
    body += f'<path class="flow" d="M266 {y2} L366 {y2}" marker-end="url(#arch-arrow)"/>' + pill(316, y2 - 13, 'HTML') + _t(316, y2 + 24, 'data, named by its payload', 'lbl')
    body += loop(412, y2, 'the agent loop, until done')
    body += frame(586, y2 - 27, 166, 50, 'parent workflow', 'parent') + _t(669, y2 + 40, 'the graph that owns the tools', 'lbl')
    return svg(180, body, 'Legend: hollow ring input, filled dot output, square card deterministic node, filled pill model call, dashed violet frame agent, teal chip tool, dashed teal curve tool call, solid arrow data flow labelled with its payload, open circle with arrowhead the agent loop, dotted amber frame parent workflow.')
