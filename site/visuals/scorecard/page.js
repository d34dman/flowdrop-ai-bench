/* Scorecard tables, rendered from the filtered rows. */
Bench.ready(({rows, order}) => {
  const {esc, pill, cell} = Bench;
  const AX = ['recall', 'recall_real', 'recall_fictional', 'precision', 'subject', 'homonym', 'fidelity', 'fabrication'];
  const graded = Bench.graded(rows);
  const cells = new Map();
  for (const r of graded) {
    const k = [r.variant, r.model_family || r.models || '-', r.page].join(' ');
    const c = cells.get(k) || {n: 0, out: {}, cost: [], exact: new Set(), k: k.split(' ')};
    c.n++; c.out[r.outcome] = (c.out[r.outcome] || 0) + 1;
    if (r.outcome === 'correct') c.cost.push(+r.cost_usd || 0);
    if (r.models && r.models !== c.k[1]) c.exact.add(r.models);
    cells.set(k, c);
  }
  const ce = document.getElementById('cells');
  if (!cells.size) ce.innerHTML = '<div class="empty">No graded runs match.</div>';
  else ce.innerHTML = '<table><tr><th>Variant</th><th>Model</th><th>Page</th><th class="n">Runs</th><th>Outcomes</th><th class="n">$ per correct run</th></tr>' +
    [...cells.values()].sort((a, b) => a.k.join().localeCompare(b.k.join())).map(c =>
      `<tr><td>${esc(cell(c.k[0]))}</td><td><code>${esc(c.k[1])}</code>${c.exact.size ? `<br><span class="note">${esc([...c.exact].sort().join(', '))}</span>` : ''}</td>` +
      `<td>${esc(c.k[2])}</td><td class="n">${c.n}</td><td>${order.filter(o => c.out[o]).map(o => pill(o, c.out[o])).join(' ')}</td>` +
      `<td class="n">${c.cost.length ? (c.cost.reduce((a, b) => a + b, 0) / c.cost.length).toFixed(4) : '-'}</td></tr>`).join('') + '</table>';

  const re = document.getElementById('runs');
  if (!rows.length) re.innerHTML = '<div class="empty">No runs match.</div>';
  else Bench.pager(re, [...rows].sort((a, b) => (a.variant + a.models + a.page + a.ts).localeCompare(b.variant + b.models + b.page + b.ts)), page => '<table><tr><th>Run</th><th>Model</th><th>Page</th>' + AX.map(a => `<th class="n">${a}</th>`).join('') +
    '<th class="n">glyphs</th><th class="n">leaks</th><th class="n">calls</th><th class="n">s</th><th class="n">$</th><th>Outcome</th><th>Output</th><th>Trace</th></tr>' +
    page.map(r =>
      `<tr><td>${esc(cell(r.variant))} <span class="note">${esc(r.tag)}</span></td><td><code>${esc(r.models || '-')}</code></td><td>${esc(r.page)}</td>` +
      AX.map(a => `<td class="n">${esc(r[a])}</td>`).join('') +
      `<td class="n">${esc(r.glyphs)}</td><td class="n">${esc(r.leaks)}</td><td class="n">${esc(r.llm_calls)}</td><td class="n">${esc(r.total_seconds)}</td><td class="n">${esc(r.cost_usd)}</td>` +
      `<td>${pill(r.outcome, null, r.excluded_reason ? r.excluded_kind + ': ' + r.excluded_reason : '')}</td><td><a href="${Bench.href('outputs/' + encodeURIComponent(r.run_id) + '.md')}">md</a></td>` +
      `<td>${r.trace ? `<a href="${Bench.href('traces/' + encodeURIComponent(r.run_id) + '.html')}">trace</a>` : '-'}</td></tr>`).join('') + '</table>');
});
