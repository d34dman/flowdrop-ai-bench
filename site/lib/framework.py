"""Shared build-time framework for the published site. Standard library only.

A visual is a folder under site/visuals/<id>/ with:

    visual.json   {"title", "blurb", "filters": [filter ids from site/filters.json],
                   "focus": optional filter id the page needs exactly one value of (a select)}
    build.py      def build(ctx): writes ctx.out/index.html (and anything else it needs)
    page.js       optional; included on the visual's pages, receives Bench.ready(...)

`ctx` (a Ctx below) carries the scored rows, the facets, the registry, the corpus
manifests, the set of run ids that have a trace, and `ctx.page(...)`, which wraps a body in
the site chrome (header, nav, filter bar mount, footer, scripts) so every page looks and
behaves the same. Filters are client-side: a visual renders from data/scores.json in the
browser through site/lib/bench.js, so one build serves every filter combination. Build-time
rendering (ctx.rows) is for pages that need it, such as one HTML per trace.
"""
import csv, hashlib, html, json, os, re, shutil
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_SRC = os.path.dirname(HERE)                       # site/
ROOT = os.path.dirname(SITE_SRC)                       # repo
OUT = os.path.join(ROOT, '_site')
DATA = os.path.join(ROOT, 'data')
REPO = 'https://github.com/d34dman/flowdrop-ai-bench'
SITE_NAME = 'FlowDrop AI Bench'
ORDER = ['correct', 'degraded', 'silent', 'format', 'loud', 'control', 'stale']
def load_cells():
    """site/cells.json: the ten benchmark cells in ladder order, each with label, name, shape, tests, peers, family."""
    return json.load(open(os.path.join(os.path.dirname(HERE), 'cells.json'), encoding='utf-8'))['cells']


CELLS = load_cells()
CELL = {c['id']: c['label'] for c in CELLS}          # cell id -> the label every page prints
LABELS = {'cell': CELL}
# Factorial wordmark (site/lib/factorial.svg, fill=currentColor so it wears the footer ink). Factorial GmbH
# sponsors the development of this benchmark and pays for the model API usage behind every run.
SPONSOR_URL = 'https://www.factorial.io/'
# Ledger columns that stay strings even when they look numeric.
TEXT_COLUMNS = {'run_id', 'tag', 'workflow', 'url_key', 'corpus_version', 'page_sha256', 'prompt_sha256', 'glyph',
                'flowdrop_version', 'harness_version', 'ts', 'pipeline_status', 'failed_nodes', 'models', 'model_family',
                'page', 'variant', 'outcome', 'task', 'excluded_kind', 'excluded_reason'}


def esc(x):
    return html.escape(str(x))


def _typed(k, v):
    if k in TEXT_COLUMNS or v == '' or v is None: return v
    try:
        return int(v) if v.lstrip('-').isdigit() else float(v)
    except ValueError:
        return v


def load_json(path):
    return json.load(open(path, encoding='utf-8'))


def load_rows():
    """data/scores.csv as typed dicts, plus `trace` (bool) per run."""
    p = os.path.join(DATA, 'scores.csv')
    if not os.path.exists(p): return []
    rows = [{k: _typed(k, v) for k, v in r.items()} for r in csv.DictReader(open(p, encoding='utf-8'))]
    traced = traced_ids()
    for r in rows: r['trace'] = r['run_id'] in traced
    return rows


def traced_ids():
    d = os.path.join(ROOT, 'traces')
    return {fn[:-len('.json.gz')] for fn in os.listdir(d) if fn.endswith('.json.gz')} if os.path.isdir(d) else set()


def load_filters():
    return load_json(os.path.join(SITE_SRC, 'filters.json'))['filters']


def load_palette():
    return load_json(os.path.join(SITE_SRC, 'palette.json'))


def model_slots(rows, palette):
    """model family -> colour slot number, from site/palette.json. A family the map does not pin
    gets a slot from its name hash (stable across builds, but unchosen) and a warning on stderr:
    pin it in palette.json so it never collides with a neighbour."""
    import hashlib, sys
    n = len(palette['slots'])
    pinned = {k: int(v) for k, v in palette['models'].items()}
    seen = set()
    for r in rows:
        for m in str(r.get('model_family') or '').split(','):
            if m and m != '-': seen.add(m)
    out = dict(pinned)
    for m in sorted(seen - set(pinned)):
        out[m] = int(hashlib.sha1(m.encode()).hexdigest(), 16) % n + 1
        print(f'warning: model {m!r} has no colour in site/palette.json; using hashed slot {out[m]} — pin it', file=sys.stderr)
    return out


def build_facets(rows, filters):
    """Distinct values with counts per filter, in the filter's declared order else by count.
    Also carries the model colour map (site/palette.json) so every page paints a model the same."""
    palette = load_palette()
    out = {'filters': filters, 'labels': LABELS, 'values': {}, 'palette': {'slots': palette['slots'], 'models': model_slots(rows, palette)}}
    for f in filters:
        c = Counter()
        for r in rows:
            v = r.get(f['column'])
            vals = [x for x in str(v).split(f['split']) if x] if f.get('split') and v not in ('', None) else [str(v) if v not in ('', None) else '-']
            for x in vals: c[x] += 1
        if f.get('order'):
            keyf = lambda kv, o=f['order']: (o.index(kv[0]) if kv[0] in o else len(o), kv[0])
        else:
            keyf = lambda kv: (-kv[1], kv[0])
        out['values'][f['id']] = sorted(c.items(), key=keyf)
    return out


# Folders the data stage publishes at the site root; a visual cannot take one of these ids.
RESERVED = {'corpus', 'prompt', 'outputs', 'runs', 'data', 'lib'}


def sponsor_mark():
    return open(os.path.join(SITE_SRC, 'lib', 'factorial.svg'), encoding='utf-8').read().strip()


def load_registry():
    ids = load_json(os.path.join(SITE_SRC, 'registry.json'))['visuals']
    vis = []
    for vid in ids:
        if vid in RESERVED or not re.fullmatch(r'[a-z][a-z0-9-]*', vid):
            raise SystemExit(f'visual id {vid!r} is reserved or not [a-z0-9-]; see RESERVED in site/lib/framework.py')
        d = os.path.join(SITE_SRC, 'visuals', vid)
        meta = load_json(os.path.join(d, 'visual.json'))
        vis.append({'id': vid, 'dir': d, 'has_js': os.path.exists(os.path.join(d, 'page.js')), **meta})
    return vis


class Ctx:
    def __init__(self, visual_id=None):
        self.root, self.site, self.repo = ROOT, OUT, REPO
        self.rows = load_rows()
        self.filters = load_filters()
        self.facets = build_facets(self.rows, self.filters)
        self.registry = load_registry()
        self.traced = traced_ids()
        self.visual = next((v for v in self.registry if v['id'] == visual_id), None)
        self.out = os.path.join(OUT, visual_id) if visual_id else OUT
        self.CELL, self.CELLS, self.ORDER = CELL, CELLS, ORDER
        self._manifests = {}

    def manifest(self, version='v1'):
        if version not in self._manifests:
            self._manifests[version] = load_json(os.path.join(ROOT, 'corpus', version, 'manifest.json'))
        return self._manifests[version]

    def graded(self):
        return [r for r in self.rows if r['outcome'] not in ('control', 'stale', 'excluded')]

    def write(self, rel, text):
        p = os.path.join(self.out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(text)
        return p

    def page(self, title, body, depth=None, filters=None, sub=None, scripts=(), head='', heading=None):
        """Full HTML page in the site chrome. `depth` is how many folders below _site the page
        sits (1 for _site/<visual>/index.html); `filters` the ids the bar shows (defaults to
        the visual's); `scripts` extra JS paths relative to the site root."""
        if depth is None: depth = 1 if self.visual else 0
        root = '../' * depth if depth else './'
        v = self.visual or {}
        flt = v.get('filters', []) if filters is None else filters
        foc = f' data-focus="{esc(v["focus"])}"' if v.get('focus') else ''
        nav = ''.join(f'<a data-nav href="{root}{x["id"]}/"{" class=cur" if v and x["id"] == v["id"] else ""}>{esc(x["title"])}</a>' for x in self.registry)
        js = [f'{root}lib/bench.js'] + ([f'{root}{v["id"]}/page.js'] if v.get('has_js') else []) + [root + s for s in scripts]
        return (f'<!doctype html><html lang="en" data-root="{root}"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title) if title == SITE_NAME else esc(title) + ' · ' + SITE_NAME}</title>'
                f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">'
                f'<link rel="stylesheet" href="{root}lib/bench.css">{head}</head><body>'
                f'<header class="site"><div class="in"><a class="brand" data-nav href="{root}">{SITE_NAME}<small>A living benchmark of AI content workflows</small></a><nav>{nav}</nav></div></header>'
                f'<main><h1>{esc(heading or title)}</h1>' + (f'<p class="sub">{sub}</p>' if sub else '') +
                f'<div id="bench-filters" data-filters="{",".join(flt)}"{foc}></div>{body}</main>'
                f'<footer class="site"><p>Source, corpus and every run: <a href="{REPO}">{REPO.split("//")[1]}</a>. '
                f'Rebuilt by CI on every merge. Filters live in the address bar; copy it to share the view.</p>'
                f'<p class="sponsor"><a href="{SPONSOR_URL}" rel="noopener" aria-label="Factorial GmbH">{sponsor_mark()}</a>'
                f'<span>Development of this benchmark and the API usage behind every run are generously sponsored by '
                f'<a href="{SPONSOR_URL}" rel="noopener">Factorial GmbH</a>, the company behind FlowDrop.</span></p></footer>'
                + ''.join(f'<script src="{s}"></script>' for s in js) + '</body></html>')

    def copy_visual_assets(self):
        """page.js (and any other non-build file) of the current visual into its output folder."""
        if not self.visual: return
        os.makedirs(self.out, exist_ok=True)
        for fn in os.listdir(self.visual['dir']):
            if fn in ('build.py', 'visual.json') or fn.startswith('.') or fn == '__pycache__': continue
            shutil.copy(os.path.join(self.visual['dir'], fn), os.path.join(self.out, fn))


def sha256_file(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()
