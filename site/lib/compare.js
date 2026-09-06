/* Shared renderer for the focus pages: one dimension fixed, rows compared along another.
 *
 *   Compare.render(el, rows, {by: 'variant', label: v => Bench.cell(v), order: ORDER, link: v => url})
 *
 * Two tables: correctness (graded runs, outcome counts as a labelled stacked bar, correct
 * rate) and means of the axes, calls, seconds and cost per group. Only graded runs count
 * toward correctness and axis means; controls, stale and excluded runs are listed in their own column
 * so nothing disappears silently.
 */
window.Compare = (function () {
  const AX = ['recall', 'precision', 'subject', 'homonym', 'fidelity', 'fabrication'];
  const mean = xs => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
  const f2 = x => x == null ? '-' : x.toFixed(2);
  function render(el, rows, o) {
    const {esc, pill} = Bench;
    const groups = new Map();
    for (const r of rows) {
      const k = String(r[o.by] || '-');
      const g = groups.get(k) || {k, n: 0, graded: 0, ungraded: 0, out: {}, ax: Object.fromEntries(AX.map(a => [a, []])), calls: [], secs: [], cost: []};
      g.n++;
      if (Bench.UNGRADED.has(r.outcome)) g.ungraded++;
      else {
        g.graded++; g.out[r.outcome] = (g.out[r.outcome] || 0) + 1;
        for (const a of AX) if (r[a] !== '' && r[a] != null) g.ax[a].push(+r[a]);
        if (r.llm_calls !== '') g.calls.push(+r.llm_calls); if (r.total_seconds !== '') g.secs.push(+r.total_seconds); if (r.cost_usd !== '') g.cost.push(+r.cost_usd);
      }
      groups.set(k, g);
    }
    const gs = [...groups.values()].sort((a, b) => a.k.localeCompare(b.k));
    if (!gs.length) { el.innerHTML = '<div class="empty">No runs match.</div>'; return; }
    const ORDER = o.order.filter(x => !Bench.UNGRADED.has(x));
    const name = k => o.link ? `<a href="${o.link(k)}">${esc(o.label(k))}</a>` : esc(o.label(k));
    const stack = g => g.graded ? '<span class="stack" title="' + ORDER.filter(x => g.out[x]).map(x => x + ' ' + g.out[x]).join(', ') + '">' +
      ORDER.filter(x => g.out[x]).map(x => `<i class="${x}" style="flex:${g.out[x]}">${g.out[x]}</i>`).join('') + '</span>' : '<span class="note">no graded runs</span>';
    const legend = '<div class="legend">' + ORDER.map(x => `<span><i class="${x}"></i>${x}</span>`).join('') + '</div>';
    el.innerHTML =
      `<h2>Correctness</h2>${legend}<div class="wrap"><table class="cmp"><tr><th>${esc(o.head)}</th><th class="n">graded</th><th>outcomes</th><th class="n">correct</th><th class="n">not graded</th></tr>` +
      gs.map(g => `<tr><td>${name(g.k)}</td><td class="n">${g.graded}</td><td class="bar">${stack(g)}</td>` +
        `<td class="n">${g.graded ? Math.round(100 * (g.out.correct || 0) / g.graded) + '%' : '-'}<span class="hbar"><i style="width:${g.graded ? 100 * (g.out.correct || 0) / g.graded : 0}%"></i></span></td>` +
        `<td class="n">${g.ungraded || ''}</td></tr>`).join('') + '</table></div>' +
      `<h2>Axes, mean over graded runs</h2><div class="wrap"><table class="cmp"><tr><th>${esc(o.head)}</th>` + AX.map(a => `<th class="n">${a}</th>`).join('') +
      '<th class="n">calls</th><th class="n">s</th><th class="n">$</th></tr>' +
      gs.filter(g => g.graded).map(g => `<tr><td>${name(g.k)}</td>` + AX.map(a => `<td class="n">${f2(mean(g.ax[a]))}</td>`).join('') +
        `<td class="n">${f2(mean(g.calls))}</td><td class="n">${f2(mean(g.secs))}</td><td class="n">${mean(g.cost) == null ? '-' : mean(g.cost).toFixed(4)}</td></tr>`).join('') + '</table></div>';
  }
  return { render, AX };
})();
