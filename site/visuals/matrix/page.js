Bench.ready(({rows}) => {
  const {esc, cell} = Bench;
  const g = Bench.graded(rows);
  const el = document.getElementById('matrix');
  if (!g.length) { el.innerHTML = '<div class="empty">No graded runs match.</div>'; return; }
  const variants = [...new Set(g.map(r => r.variant))].sort();
  const models = [...new Set(g.map(r => r.model_family || '-'))].sort();
  const m = {};
  for (const r of g) { const k = r.variant + '|' + (r.model_family || '-'); m[k] = m[k] || {n: 0, ok: 0}; m[k].n++; if (r.outcome === 'correct') m[k].ok++; }
  // A cell link opens the scorecard with variant and model added to the current filters.
  const link = (v, mo) => {
    const p = new URLSearchParams(Bench.query());
    p.set('benchmark', v); p.set('model', mo);
    return Bench.href('scorecard/') + '?' + p.toString();
  };
  el.innerHTML = '<table><tr><th>Variant</th>' + models.map(x => `<th><code>${esc(x)}</code></th>`).join('') + '</tr>' +
    variants.map(v => `<tr><td>${esc(cell(v))}</td>` + models.map(mo => {
      const c = m[v + '|' + mo];
      if (!c) return '<td class="c">.</td>';
      const pct = Math.round(100 * c.ok / c.n);
      return `<td class="c"><a href="${link(v, mo)}">${c.ok} / ${c.n}<span class="bar"><i style="width:${pct}%"></i></span></a></td>`;
    }).join('') + '</tr>').join('') + '</table>';
});
