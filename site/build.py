#!/usr/bin/env python3
"""Builds the published site into _site/. Standard library only. Run scoring/score.py first.

    python3 site/build.py                 # everything: data, assets, every visual, homepage
    python3 site/build.py data            # _site/data (scores.json, facets.json, csvs), lib/, corpus, prompt, runs, outputs
    python3 site/build.py visual <id>     # _site/<id>/ only (one CI matrix job per visual)
    python3 site/build.py index           # _site/index.html (the homepage that indexes the visuals)
    python3 site/build.py list            # the registry as a JSON list, for the CI matrix

The stages are independent so CI can run them in separate jobs and assemble the folders.
A visual is site/visuals/<id>/ (see site/lib/framework.py for the contract); the homepage,
the nav and the CI matrix all come from site/registry.json.
"""
import importlib.util, json, os, shutil, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
import framework as fw


def stage_data():
    ctx = fw.Ctx()
    os.makedirs(os.path.join(fw.OUT, 'data'), exist_ok=True)
    for d in ('corpus', 'prompt', 'outputs', 'runs'):
        src = os.path.join(fw.ROOT, d)
        if os.path.isdir(src):
            if os.path.isdir(os.path.join(fw.OUT, d)): shutil.rmtree(os.path.join(fw.OUT, d))
            shutil.copytree(src, os.path.join(fw.OUT, d))
    for fn in ('runs.csv', 'scores.csv'):
        if os.path.exists(os.path.join(fw.DATA, fn)): shutil.copy(os.path.join(fw.DATA, fn), os.path.join(fw.OUT, 'data', fn))
    json.dump(ctx.rows, open(os.path.join(fw.OUT, 'data', 'scores.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(ctx.facets, open(os.path.join(fw.OUT, 'data', 'facets.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lib = os.path.join(fw.OUT, 'lib'); os.makedirs(lib, exist_ok=True)
    for fn in os.listdir(fw.HERE):
        if fn.endswith(('.js', '.css')): shutil.copy(os.path.join(fw.HERE, fn), os.path.join(lib, fn))
    open(os.path.join(fw.OUT, '.nojekyll'), 'w').close()
    print(f'data -> _site/data ({len(ctx.rows)} runs, {len(ctx.facets["values"])} facets)')


def stage_visual(vid):
    ctx = fw.Ctx(vid)
    if not ctx.visual: sys.exit(f'unknown visual {vid!r}; registry: {[v["id"] for v in ctx.registry]}')
    if os.path.isdir(ctx.out): shutil.rmtree(ctx.out)
    os.makedirs(ctx.out)
    spec = importlib.util.spec_from_file_location(f'visual_{vid}', os.path.join(ctx.visual['dir'], 'build.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.build(ctx)
    ctx.copy_visual_assets()
    if not os.path.exists(os.path.join(ctx.out, 'index.html')): sys.exit(f'visual {vid} wrote no index.html')
    print(f'visual {vid} -> _site/{vid}/')


def stage_index():
    ctx = fw.Ctx()
    esc = fw.esc
    cards = ''.join(
        f'<a class="card" data-nav href="./{v["id"]}/"><h3>{esc(v["title"])}</h3><p>{esc(v["blurb"])}</p>'
        f'<div class="f">{"filters: " + ", ".join(v["filters"]) if v["filters"] else "no filters"}</div></a>'
        for v in ctx.registry)
    body = ('<div class="stats" id="stats"></div>'
            '<p class="note">New here? <a data-nav href="./architectures/">Architectures</a> draws what each of the ten cells does and which pairs differ by one decision; '
            'every cell label on this site reads <b>input the model sees → who does the work → tools</b>.</p>'
            '<p class="note"><b>correct</b>: every axis at threshold. <b>degraded</b>: all axes ≥ 0.75. <b>silent</b>: completed and the document is wrong. '
            '<b>format</b>: HTML came back. <b>loud</b>: nothing usable delivered. <b>stale</b>: the page changed after the run; ungraded. '
            'Axes and thresholds: <code>scoring/score.py</code>.</p>'
            f'<h2>Visuals</h2><div class="cards">{cards}</div>'
            f'<h2>Contribute a run</h2><p>Clone the repo, set up the runner, run a cell, open a pull request; CI scores it and merge publishes it here. '
            f'The steps are in the <a href="{fw.REPO}#contribute-your-runs">README</a>. '
            f'Data: <a href="data/runs.csv">runs.csv</a>, <a href="data/scores.csv">scores.csv</a>, <a href="data/scores.json">scores.json</a>.</p>')
    sub = ('One task, one prompt, one owned corpus, ten workflow architectures from a fixed pipeline to an autonomous agent, '
           'compared on cost, speed and failure modes. Pick filters once; every visual keeps them.')
    os.makedirs(fw.OUT, exist_ok=True)
    open(os.path.join(fw.OUT, 'index.html'), 'w', encoding='utf-8').write(
        ctx.page(fw.SITE_NAME, body, depth=0, filters=[f['id'] for f in ctx.filters], sub=sub, scripts=('lib/home.js',), heading='Overview'))
    print('index -> _site/index.html')


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'all'
    if cmd == 'list':
        print(json.dumps([v['id'] for v in fw.load_registry()])); return
    if cmd == 'all':
        if os.path.isdir(fw.OUT): shutil.rmtree(fw.OUT)
        stage_data()
        for v in fw.load_registry(): stage_visual(v['id'])
        stage_index()
    elif cmd == 'data': stage_data()
    elif cmd == 'visual': stage_visual(argv[2])
    elif cmd == 'index': stage_index()
    else: sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
