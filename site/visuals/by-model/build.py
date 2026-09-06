"""Model focus: one model, compared across benchmarks. Rendered in the browser by page.js
through the shared Compare renderer (site/lib/compare.js)."""


def build(ctx):
    body = '<div id="cmp"></div>'
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb'], scripts=('lib/compare.js',)))
