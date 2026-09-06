"""Variant x model matrix: correct over graded per cell, rendered in the browser."""


def build(ctx):
    body = ('<p class="note">Each cell is <b>correct / graded</b> runs for that architecture on that model, over the pages and tags '
            'selected above. Click a cell to open it in the scorecard.</p><div class="wrap mx" id="matrix"></div>')
    ctx.write('index.html', ctx.page(ctx.visual['title'], body, sub=ctx.visual['blurb']))
