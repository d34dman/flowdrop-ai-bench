"""Scorecard: outcome per cell and every run. The tables are rendered in the browser from
data/scores.json (page.js), so the filter bar applies to them directly."""


def build(ctx):
    body = ('<h2>Outcome per cell</h2>'
            '<p class="note">Grouped by model family: a dated id such as <code>claude-haiku-4-5-20251001</code> is a snapshot of '
            '<code>claude-haiku-4-5</code>. The snapshots that answered are listed under each family; every run below keeps its exact id. '
            'Controls (B0, B1) and stale runs are not graded.</p>'
            '<div class="wrap" id="cells"></div>'
            '<h2>Every run</h2><div class="wrap" id="runs"></div>')
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb']))
