Bench.ready(({rows, focus}) => {
  const el = document.getElementById('cmp');
  if (!focus || focus.value === undefined) { el.innerHTML = '<div class="empty">No runs yet.</div>'; return; }
  const h1 = document.querySelector('main h1');
  h1.textContent = 'Benchmark focus: ' + Bench.cell(focus.value) + ' ';
  const a = document.createElement('a'); a.className = 'arch-link'; a.textContent = 'architecture';
  a.href = Bench.href('architectures/') + '#' + Bench.cellCode(focus.value); h1.appendChild(a);
  Compare.render(el, rows, {
    by: 'model_family', head: 'Model', label: v => v, order: Bench.ORDER,
    link: v => { const p = new URLSearchParams(Bench.query()); p.set('model', v); return Bench.href('by-model/') + '?' + p; }
  });
});
