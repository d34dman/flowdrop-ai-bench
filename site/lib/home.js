/* Homepage: headline counts that follow the filters. */
Bench.ready(({rows, all, order}) => {
  const g = Bench.graded(rows);
  const by = {}; for (const r of g) by[r.outcome] = (by[r.outcome] || 0) + 1;
  const models = new Set(), cells = new Set(), tags = new Set();
  for (const r of rows) { for (const m of String(r.model_family || '').split(',')) if (m) models.add(m); cells.add(r.variant); tags.add(r.tag); }
  const stat = (n, l) => `<div><b>${n}</b><span>${l}</span></div>`;
  document.getElementById('stats').innerHTML =
    stat(rows.length === all.length ? rows.length : rows.length + ' / ' + all.length, 'runs') + stat(g.length, 'graded') +
    stat(models.size, 'models') + stat(cells.size, 'cells') + stat(tags.size, 'contributor tags') +
    `<div style="align-self:center">${order.filter(o => o !== 'control' && o !== 'stale' && by[o]).map(o => Bench.pill(o, by[o])).join(' ')}</div>`;
});
