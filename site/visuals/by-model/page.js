Bench.ready(({rows, focus}) => {
  const el = document.getElementById('cmp');
  if (!focus || focus.value === undefined) { el.innerHTML = '<div class="empty">No runs yet.</div>'; return; }
  document.querySelector('main h1').textContent = 'Model focus: ' + focus.value;
  Compare.render(el, rows, {
    by: 'variant', head: 'Benchmark', label: Bench.cell, order: Bench.ORDER,
    link: v => { const p = new URLSearchParams(Bench.query()); p.set('benchmark', v); return Bench.href('by-benchmark/') + '?' + p; }
  });
});
