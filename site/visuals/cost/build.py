"""Cost and time: a scatter of mean cost against mean seconds per cell (variant x model) and
small-multiple bar figures per metric. Rendered in the browser by page.js."""


def build(ctx):
    body = ('<p class="note">A <b>cell</b> is one architecture on one model over the runs the filters leave. Means are over graded runs only; '
            'controls (B0, B1), stale and excluded runs do not count. <b>$ per correct run</b> is the cell\'s total spend divided by its correct '
            'runs, so a cheap architecture that is often wrong stops looking cheap. Click a mark to open the cell in the scorecard.</p>'
            '<h2>Cost against time</h2><div id="scatter" class="fig"></div>'
            '<h2>Per architecture, per model</h2><div id="bars" class="fig"></div>')
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb']))
