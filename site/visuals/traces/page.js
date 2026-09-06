Bench.ready(({rows}) => {
  const {esc, pill, cell} = Bench;
  const t = rows.filter(r => r.trace).sort((a, b) => String(b.ts || '').localeCompare(String(a.ts || '')));
  const el = document.getElementById('traces');
  if (!t.length) { el.innerHTML = '<div class="empty">No traced runs match.</div>'; return; }
  Bench.pager(el, t, rows => '<table><tr><th>Run</th><th>Model</th><th>Page</th><th class="n">jobs</th><th class="n">calls</th><th class="n">s</th><th class="n">$</th><th>Outcome</th><th>When</th></tr>' +
    rows.map(r => `<tr><td><a href="./${encodeURIComponent(r.run_id)}.html">${esc(cell(r.variant))}</a> <span class="note">${esc(r.tag)}</span></td>` +
      `<td><code>${esc(r.models || '-')}</code></td><td>${esc(r.page)}</td><td class="n">${esc(r.job_count)}</td><td class="n">${esc(r.llm_calls)}</td>` +
      `<td class="n">${esc(r.total_seconds)}</td><td class="n">${esc(r.cost_usd)}</td><td>${pill(r.outcome)}</td><td class="note">${esc(String(r.ts).slice(0, 16).replace('T', ' '))}</td></tr>`).join('') + '</table>');
});
