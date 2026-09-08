"""Cost and time: a scatter of mean cost against mean seconds per cell (variant x model) and
small-multiple bar figures per metric. Rendered in the browser by page.js."""


def build(ctx):
    body = ('<p class="note">A <b>cell</b> is one architecture on one model over the runs the filters leave. Means are over graded runs only; '
            'controls (B0, B1), stale and excluded runs do not count. <b>$ per correct run</b> is the cell\'s total spend divided by its correct '
            'runs, so a cheap architecture that is often wrong stops looking cheap. Click a mark to open the cell in the scorecard.</p>'
            '<p class="note">Dollars are <b>list price</b>: each run\'s recorded tokens priced against the bench\'s own table, '
            '<a href="' + ctx.repo + '/blob/main/scoring/pricing.json' + '">scoring/pricing.json</a>, pinned per model with its source and effective date. '
            'They are not what a contributor was billed; discounts, credits and OpenRouter routing vary per account and would make cost a property of the '
            'contributor instead of the run. A model without a row cannot enter the dataset.</p>'
            '<h2>Cost against time</h2><div id="scatter" class="fig"></div>'
            '<h2>Per architecture, per model</h2><div id="bars" class="fig"></div>')
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb']))
