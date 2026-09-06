#!/usr/bin/env python3
"""Timeline printer and HTML visualizer for a run's execution trace. Standard library only.

    python3 scoring/trace.py <run_id-prefix>                 # text timeline to stdout
    python3 scoring/trace.py <run_id-prefix> --html <outfile> # self-contained HTML page

Reads traces/<run_id>.json.gz (trace_version 1: pipelines, jobs, checkpoints, sessions,
metering). build_site.py imports load_trace/render_html to publish one page per trace.
"""
import gzip, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACES = os.path.join(ROOT, 'traces')
AI_NODE = re.compile(r'ai_provider_chat|processor_reason|ai_agents_executor|react_agent')


def load_trace(path):
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        return json.load(fh)


def find_trace(prefix):
    if not os.path.isdir(TRACES): return None
    matches = sorted(f for f in os.listdir(TRACES) if f.endswith('.json.gz') and f.startswith(prefix))
    return os.path.join(TRACES, matches[0]) if matches else None


# ------------------------------------------------------------------ shared helpers
def compact(x, n=100):
    s = x if isinstance(x, str) else json.dumps(x, separators=(',', ':'), default=str)
    return s[:n]


def is_ai(node_type):
    return bool(AI_NODE.search(node_type or ''))


def job_order(j):
    """Start second, then entity id: started is second-resolution and a skipped job has none."""
    s = j.get('started')
    return (s if s else float('inf'), int(j.get('id') or 0))


def pipeline_tree(trace):
    """id -> pipeline, and parent_id -> [child ids], preserving trace order."""
    by_id = {p['id']: p for p in trace['pipelines']}
    children = {}
    roots = []
    for p in trace['pipelines']:
        if p.get('parent_id'):
            children.setdefault(p['parent_id'], []).append(p['id'])
        else:
            roots.append(p['id'])
    return by_id, children, roots


def metering_summary(trace):
    calls = trace.get('metering') or []
    tokens_in = sum(m.get('input_tokens') or 0 for m in calls)
    tokens_out = sum(m.get('output_tokens') or 0 for m in calls)
    cost = sum(m.get('cost_usd') or 0 for m in calls)
    return len(calls), tokens_in, tokens_out, cost


def root_pipeline(trace):
    by_id, children, roots = pipeline_tree(trace)
    return by_id[roots[0]] if roots else None


# ------------------------------------------------------------------ text timeline
def render_text(trace):
    out = []
    run = trace.get('run', {})
    root = root_pipeline(trace)
    calls, tin, tout, cost = metering_summary(trace)
    t0 = root['started'] if root and root.get('started') else 0
    total_s = root['seconds'] if root else None
    out.append(f"run          {trace.get('run_id', '?')}")
    out.append(f"workflow     {run.get('workflow', '?')}  page={run.get('url_key', '?')}  model={run.get('model', '?')}")
    out.append(f"status       {(root or {}).get('status', '?')}  total={total_s}s  calls={calls}  tokens={tin}+{tout}  cost=${cost:.4f}")
    out.append('')

    by_id, children, roots = pipeline_tree(trace)

    def offset(ts):
        return round(ts - t0, 2) if ts else 0.0

    def emit_pipeline(pid, depth):
        p = by_id[pid]
        indent = '  ' * depth
        header = f"{indent}pipeline {p['id']}  {p.get('workflow_id', '?')}  {p.get('status', '?')}  +{offset(p.get('started')):.2f}s..{offset(p.get('completed')):.2f}s"
        if p.get('parent_id'):
            header += f"  └ child of {p['parent_id']}"
        out.append(header)
        jobs = sorted(p.get('jobs') or [], key=job_order)
        for j in jobs:
            dur = j.get('seconds')
            if dur is None and j.get('started') and j.get('completed'):
                dur = j['completed'] - j['started']
            star = '*' if is_ai(j.get('node_type')) else ' '
            tail = j.get('error') or compact(j.get('output'))
            out.append(f"{indent}  +{offset(j.get('started')):>8.2f}s  {(dur or 0):>6.2f}s  {j.get('status', '?'):<10}{star}{(j.get('node_type') or '?'):<36.36} {(j.get('node_id') or '?'):<28.28} → {tail}")
        for cid in children.get(pid, ()):
            emit_pipeline(cid, depth + 1)

    for rid in roots:
        emit_pipeline(rid, 0)

    cps = trace.get('checkpoints') or []
    if cps:
        out.append('')
        out.append('checkpoints:')
        for c in sorted(cps, key=lambda c: c.get('created') or 0):
            out.append(f"  +{offset(c.get('created')):>8.2f}s  node={c.get('node_id', '?')}  thread={c.get('thread_id', '?')}")

    sessions = trace.get('sessions') or []
    if sessions:
        out.append('')
        out.append('sessions:')
        for s in sessions:
            out.append(f"  session {s.get('id', '?')}  {s.get('name', '?')}  ({s.get('status', '?')})")
            for m in sorted(s.get('messages') or [], key=lambda m: m.get('sequence') or 0):
                out.append(f"    {m.get('role', '?'):<10}{compact(m.get('content'))}")

    return '\n'.join(out) + '\n'


# ------------------------------------------------------------------ HTML visualizer
CSS = """
:root{color-scheme:light dark;--bg:#fff;--fg:#1d2430;--mut:#5b6472;--line:#dde2e8;--ai:#7a5cc7;--bar:#8fa3c9;--fail:#c43d3d;--ok:#2f8f5b}
@media(prefers-color-scheme:dark){:root{--bg:#14181e;--fg:#e6e9ee;--mut:#98a2ae;--line:#2b323c;--bar:#4b638f}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:76rem;margin:0 auto;padding:1.5rem 1rem}
h1{font-size:1.4rem;margin:.2rem 0}h2{font-size:1.05rem;margin:1.6rem 0 .4rem;border-bottom:1px solid var(--line);padding-bottom:.2rem}
.sub{color:var(--mut)}
table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border-bottom:1px solid var(--line);padding:.25rem .4rem;text-align:left;vertical-align:top}
th{color:var(--mut);font-weight:600}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pipeline{margin:.8rem 0;padding-left:calc(var(--depth,0) * 1.4rem)}
.pipeline-head{color:var(--mut);font-size:.85rem;margin-bottom:.2rem}
.track{position:relative;height:1.1rem;background:var(--line);border-radius:.2rem;margin:.15rem 0;overflow:hidden}
.bar{position:absolute;top:0;bottom:0;background:var(--bar);border-radius:.2rem}
.bar.ai{background:var(--ai)}.bar.failed{background:var(--fail)}
.pill{display:inline-block;padding:0 .4rem;border-radius:1rem;font-size:.75rem;color:#fff;background:var(--mut)}
.pill.completed{background:var(--ok)}.pill.failed{background:var(--fail)}
.jobrow{margin:.25rem 0}
.jobrow summary{cursor:pointer;display:flex;gap:.5rem;align-items:center;list-style:none}
.jobrow summary::-webkit-details-marker{display:none}
.jobrow .meta{font-family:ui-monospace,monospace;font-size:.82rem;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
pre{background:var(--line);padding:.5rem;border-radius:.3rem;overflow-x:auto;font-size:.8rem;white-space:pre-wrap;word-break:break-word}
.note{color:var(--mut);font-size:.85rem}
"""


def esc(x):
    return html.escape(str(x))


def esc_pre(x):
    s = x if isinstance(x, str) else json.dumps(x, indent=1, default=str)
    return html.escape(s)


def render_html(trace):
    run = trace.get('run', {})
    root = root_pipeline(trace)
    calls, tin, tout, cost = metering_summary(trace)
    t0 = root['started'] if root and root.get('started') else 0
    total_s = root['seconds'] if root else None
    by_id, children, roots = pipeline_tree(trace)

    # index job outputs carrying sub_pipeline_id so a child pipeline can be nested after its spawning job
    spawner = {}  # child pipeline id -> (pipeline_id, job_id)
    for p in trace['pipelines']:
        for j in p.get('jobs') or []:
            out_ = j.get('output')
            spid = None
            if isinstance(out_, dict): spid = out_.get('sub_pipeline_id')
            if spid is not None:
                spawner[str(spid)] = (p['id'], j.get('id'))

    def offset(ts):
        return round(ts - t0, 2) if ts else 0.0

    span = max((root.get('completed') or 0) - t0, 1) if root else 1

    parts = [f'<title>trace {esc(trace.get("run_id", ""))}</title><style>{CSS}</style><main>']
    parts.append(f'<h1>Trace: {esc(trace.get("run_id", "?"))}</h1>')
    parts.append(f'<p class="sub">workflow {esc(run.get("workflow", "?"))} &middot; page {esc(run.get("url_key", "?"))} &middot; '
                 f'model {esc(run.get("model", "?"))} &middot; status {esc((root or {}).get("status", "?"))} &middot; '
                 f'total {esc(total_s)}s &middot; {calls} calls &middot; {tin}+{tout} tokens &middot; ${cost:.4f}</p>')

    def job_html(p, j, depth):
        started = offset(j.get('started'))
        dur = j.get('seconds')
        if dur is None and j.get('started') and j.get('completed'):
            dur = j['completed'] - j['started']
        dur = dur or 0
        left_pct = max(0, min(100, started / span * 100))
        width_pct = max(0.3, min(100 - left_pct, dur / span * 100))
        cls = 'ai' if is_ai(j.get('node_type')) else ''
        if j.get('status') == 'failed': cls += ' failed'
        tail = j.get('error') or compact(j.get('output'), 100)
        star = ' *' if is_ai(j.get('node_type')) else ''
        rows = [f'<div class="jobrow" style="--depth:{depth}"><details><summary>',
                f'<div class="track" style="width:12rem"><div class="bar {cls}" style="left:{left_pct:.1f}%;width:{width_pct:.1f}%"></div></div>',
                f'<span class="pill {esc(j.get("status", "?"))}">{esc(j.get("status", "?"))}</span>',
                f'<span class="meta">+{started:.2f}s {dur:.2f}s {esc(j.get("node_type", "?"))}{star} {esc(j.get("node_id", "?"))} → {esc(tail)}</span>',
                '</summary>',
                f'<pre>input:\n{esc_pre(j.get("input"))}</pre>',
                f'<pre>output:\n{esc_pre(j.get("output"))}</pre>']
        if j.get('error'): rows.append(f'<pre>error:\n{esc_pre(j.get("error"))}</pre>')
        rows.append(f'<pre>metadata:\n{esc_pre(j.get("metadata"))}</pre>')
        rows.append('</details></div>')
        # nest a child pipeline right after the job that spawned it
        child_id = None
        for cid, (ppid, jid) in spawner.items():
            if ppid == p['id'] and jid == j.get('id'): child_id = cid
        if child_id and child_id in by_id:
            rows.append(pipeline_html(child_id, depth + 1, nested=True))
        return '\n'.join(rows)

    def pipeline_html(pid, depth, nested=False):
        p = by_id[pid]
        chunk = [f'<div class="pipeline" style="--depth:{depth}">']
        head = f'pipeline {esc(p["id"])} &middot; {esc(p.get("workflow_id", "?"))} &middot; <span class="pill {esc(p.get("status","?"))}">{esc(p.get("status", "?"))}</span> &middot; +{offset(p.get("started")):.2f}s..{offset(p.get("completed")):.2f}s'
        if p.get('parent_id'): head += f' &middot; child of {esc(p["parent_id"])}'
        chunk.append(f'<div class="pipeline-head">{head}</div>')
        jobs = sorted(p.get('jobs') or [], key=job_order)
        already_nested = {c for c in children.get(pid, ())}
        emitted_children = set()
        for j in jobs:
            chunk.append(job_html(p, j, depth))
            for cid, (ppid, jid) in spawner.items():
                if ppid == pid and jid == j.get('id'): emitted_children.add(cid)
        # any child pipeline not identifiably spawned by a job: render after the parent
        for cid in children.get(pid, ()):
            if cid not in emitted_children:
                chunk.append(pipeline_html(cid, depth + 1))
        chunk.append('</div>')
        return '\n'.join(chunk)

    parts.append('<h2>Pipelines</h2>')
    for rid in roots:
        parts.append(pipeline_html(rid, 0))

    cps = trace.get('checkpoints') or []
    if cps:
        parts.append('<h2>Checkpoints</h2><table><tr><th>+s</th><th>node</th><th>thread</th><th>state</th></tr>')
        for c in sorted(cps, key=lambda c: c.get('created') or 0):
            parts.append(f'<tr><td>{offset(c.get("created")):.2f}</td><td>{esc(c.get("node_id", "?"))}</td>'
                         f'<td>{esc(c.get("thread_id", "?"))}</td><td><details><summary>state</summary>'
                         f'<pre>{esc_pre(c.get("state"))}</pre></details></td></tr>')
        parts.append('</table>')

    sessions = trace.get('sessions') or []
    if sessions:
        parts.append('<h2>Sessions</h2>')
        for s in sessions:
            parts.append(f'<h3 class="note">{esc(s.get("name", "?"))} ({esc(s.get("status", "?"))})</h3><table><tr><th>role</th><th>message</th></tr>')
            for m in sorted(s.get('messages') or [], key=lambda m: m.get('sequence') or 0):
                parts.append(f'<tr><td>{esc(m.get("role", "?"))}</td><td><details><summary>{esc(compact(m.get("content"), 100))}</summary>'
                             f'<pre>{esc_pre(m.get("content"))}</pre></details></td></tr>')
            parts.append('</table>')

    metering = trace.get('metering') or []
    if metering:
        parts.append('<h2>Metering</h2><table><tr><th>provider</th><th>model</th><th>op</th><th class="n">in</th><th class="n">out</th><th class="n">cached</th><th class="n">$</th><th class="n">ms</th><th>status</th></tr>')
        for m in metering:
            parts.append(f'<tr><td>{esc(m.get("provider_id","?"))}</td><td>{esc(m.get("model_id","?"))}</td><td>{esc(m.get("operation","?"))}</td>'
                         f'<td class="n">{esc(m.get("input_tokens",0))}</td><td class="n">{esc(m.get("output_tokens",0))}</td><td class="n">{esc(m.get("cached_tokens",0))}</td>'
                         f'<td class="n">{m.get("cost_usd",0):.4f}</td><td class="n">{esc(m.get("latency_ms",""))}</td><td>{esc(m.get("status","?"))}</td></tr>')
        parts.append(f'<tr><td colspan="3">total</td><td class="n">{tin}</td><td class="n">{tout}</td><td></td><td class="n">{cost:.4f}</td><td></td><td></td></tr>')
        parts.append('</table>')

    parts.append('</main>')
    return '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + '\n'.join(parts)


# ------------------------------------------------------------------ CLI
def main():
    if len(sys.argv) < 2:
        print('usage: trace.py <run_id-prefix> [--html <outfile>]', file=sys.stderr); sys.exit(1)
    prefix = sys.argv[1]
    path = find_trace(prefix)
    if not path:
        print(f'no trace found for {prefix} in {TRACES}', file=sys.stderr); sys.exit(1)
    trace = load_trace(path)
    if '--html' in sys.argv:
        outfile = sys.argv[sys.argv.index('--html') + 1]
        with open(outfile, 'w', encoding='utf-8') as fh:
            fh.write(render_html(trace))
        print(f'trace -> {outfile}')
    else:
        sys.stdout.write(render_text(trace))


if __name__ == '__main__':
    main()
