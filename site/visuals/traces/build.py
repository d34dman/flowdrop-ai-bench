"""Traces: one HTML page per traces/<run_id>.json.gz (rendered at build time from the gzipped
capture, which itself is not published for size), plus a filterable index of them."""
import importlib.util, os


def build(ctx):
    spec = importlib.util.spec_from_file_location('bench_trace', os.path.join(ctx.root, 'scoring', 'trace.py'))
    tr = importlib.util.module_from_spec(spec); spec.loader.exec_module(tr)
    src = os.path.join(ctx.root, 'traces')
    n = 0
    if os.path.isdir(src):
        for fn in sorted(os.listdir(src)):
            if not fn.endswith('.json.gz'): continue
            ctx.write(fn[:-len('.json.gz')] + '.html', tr.render_html(tr.load_trace(os.path.join(src, fn)))); n += 1
    body = (f'<p class="note">{n} traces captured. A trace is written once by the runner (<code>bench:collect</code>) and never edited; '
            f'<code>python3 scoring/trace.py &lt;run_id&gt;</code> prints the same timeline as text.</p><div class="wrap" id="traces"></div>')
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb']))
