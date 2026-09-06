Bench.ready(({rows, focus}) => {
  const el = document.getElementById('cmp');
  if (!focus || focus.value === undefined) { el.innerHTML = '<div class="empty">No runs yet.</div>'; return; }
  document.querySelector('main h1').textContent = 'Benchmark focus: ' + Bench.cell(focus.value);
  Compare.render(el, rows, {
    by: 'model_family', head: 'Model', label: v => v, order: Bench.ORDER,
    link: v => { const p = new URLSearchParams(Bench.query()); p.set('model', v); return Bench.href('by-model/') + '?' + p; }
  });
});
