/* Cost and time. One mark per cell (variant x model family); colour is the model, fixed by
 * facet order so filtering never repaints a survivor. Text wears text tokens, never the series
 * colour. Values live in the tooltip and at bar tips; the scorecard has every run. */
Bench.ready(({rows, facets}) => {
  const {esc, cell} = Bench;
  const g = Bench.graded(rows);
  const S = document.getElementById('scatter'), B = document.getElementById('bars');
  if (!g.length) { S.innerHTML = B.innerHTML = '<div class="empty">No graded runs match.</div>'; return; }

  // ---- cells
  const MODELS = (facets.values.model || []).map(x => x[0]).filter(m => m !== '-').sort();   // fixed order: slot = index
  const slot = m => { const i = MODELS.indexOf(m); return i < 0 ? 'none' : 's' + (i % 8 + 1); };
  const mname = m => m === '-' ? 'no model call' : m;
  const cells = new Map();
  for (const r of g) {
    const m = r.model_family || '-', k = r.variant + '|' + m;
    const c = cells.get(k) || {v: r.variant, m, n: 0, ok: 0, cost: 0, secs: 0, calls: 0};
    c.n++; if (r.outcome === 'correct') c.ok++;
    c.cost += +r.cost_usd || 0; c.secs += +r.total_seconds || 0; c.calls += +r.llm_calls || 0;
    cells.set(k, c);
  }
  const C = [...cells.values()].map(c => ({...c, mcost: c.cost / c.n, msecs: c.secs / c.n, mcalls: c.calls / c.n, rate: c.ok / c.n, pcr: c.ok ? c.cost / c.ok : null}));
  const link = c => { const p = new URLSearchParams(Bench.query()); p.set('benchmark', c.v); if (c.m !== '-') p.set('model', c.m); return Bench.href('scorecard/') + '?' + p; };
  const short = v => (cell(v).match(/^B\d+/) || [v])[0];
  const usd = x => x == null ? '–' : '$' + (x < 0.01 ? x.toFixed(4) : x.toFixed(3));
  const sec = x => x == null ? '–' : (x < 10 ? x.toFixed(1) : Math.round(x)) + ' s';
  const pct = c => Math.round(100 * c.rate) + '% correct (' + c.ok + ' of ' + c.n + ')';
  const tip = c => `<b>${esc(cell(c.v))}</b> · ${esc(mname(c.m))}<br>${esc(pct(c))}<br>${usd(c.mcost)} and ${sec(c.msecs)} per run, ${c.mcalls.toFixed(1)} calls<br>${usd(c.pcr)} per correct run`;

  // ---- legend (identity never by colour alone: the legend names each swatch, the marks carry short labels)
  const legend = '<div class="legend viz">' + [...MODELS, ...(C.some(c => c.m === '-') ? ['-'] : [])].map(m => `<span><i class="${slot(m)}"></i>${esc(mname(m))}</span>`).join('') +
    '<span><i class="hollow"></i>fewer than half the runs correct</span></div>';

  // ---- scatter: x = mean seconds (log), y = mean $ (linear)
  {
    const W = 720, H = 410, L = 56, R = 16, T = 30, Bo = 44;
    const xs = C.map(c => c.msecs).filter(x => x > 0), ys = C.map(c => c.mcost);
    const xmin = Math.min(...xs) / 1.3, xmax = Math.max(...xs) * 1.3, ymax = Math.max(...ys, 0.001) * 1.12;
    const X = x => L + (Math.log10(Math.max(x, xmin)) - Math.log10(xmin)) / (Math.log10(xmax) - Math.log10(xmin)) * (W - L - R);
    const Y = y => T + (1 - y / ymax) * (H - T - Bo);
    const xt = []; for (const d of [1, 10, 100, 1000]) for (const k of [1, 2, 5]) { const v = d * k; if (v >= xmin && v <= xmax) xt.push(v); }
    const ystep = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5].find(s => ymax / s <= 6) || 1;
    const yt = []; for (let v = 0; v <= ymax; v += ystep) yt.push(+v.toFixed(6));
    // Labels: right of the dot, else left, else above or below; a label that fits nowhere is dropped
    // (the tooltip and the bars below still name the cell). Boxes are approximate.
    const sorted = C.slice().sort((a, b) => b.mcost - a.mcost), boxes = [];
    const hit = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
    const marks = sorted.map((c, i) => {
      const x = X(c.msecs), y = Y(c.mcost), hollow = c.rate < .5, t = short(c.v), w = t.length * 6.6 + 2, h = 11;
      const cands = [[x + 9, y + 3.5, x + 9, y - 6], [x - 9 - w, y + 3.5, x - 9 - w, y - 6], [x - w / 2, y - 10, x - w / 2, y - 19], [x - w / 2, y + 17, x - w / 2, y + 8]];
      let lab = '';
      for (const [tx, ty, bx, by] of cands) {
        const b = {x: bx, y: by, w, h};
        if (bx < L || bx + w > W - R) continue;
        if (!boxes.some(o => hit(b, o)) && !sorted.some(o => o !== c && Math.abs(X(o.msecs) - (bx + w / 2)) < w / 2 + 6 && Math.abs(Y(o.mcost) - (by + h / 2)) < h / 2 + 6)) {
          boxes.push(b); lab = `<text x="${tx}" y="${ty}">${esc(t)}</text>`; break;
        }
      }
      return `<a href="${link(c)}" class="mk ${slot(c.m)}${hollow ? ' hollow' : ''}" data-i="${i}"><circle cx="${x}" cy="${y}" r="9" class="hit"/><circle cx="${x}" cy="${y}" r="5.5"/>${lab}</a>`;
    });
    S.innerHTML = legend + `<svg class="viz scatter" viewBox="0 0 ${W} ${H}" role="img" aria-label="Mean cost against mean seconds per cell">` +
      yt.map(v => `<line class="grid" x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tick" x="${L - 8}" y="${Y(v) + 3.5}" text-anchor="end">${v ? '$' + v : '0'}</text>`).join('') +
      xt.map(v => `<line class="grid" y1="${T}" y2="${H - Bo}" x1="${X(v)}" x2="${X(v)}"/><text class="tick" x="${X(v)}" y="${H - Bo + 16}" text-anchor="middle">${v}</text>`).join('') +
      `<line class="axis" x1="${L}" x2="${W - R}" y1="${H - Bo}" y2="${H - Bo}"/>` +
      `<text class="axl" x="${W - R}" y="${H - 8}" text-anchor="end">mean seconds per run, log scale</text>` +
      `<text class="axl" x="${L}" y="${T - 14}">mean $ per run</text>` +
      marks.join('') + '</svg>';
    hover(S, sorted);
  }

  // ---- bars: one table, a row per architecture, a bar per model in each metric column
  {
    const METRICS = [['mcost', 'mean $ per run', usd], ['msecs', 'mean seconds per run', sec], ['pcr', '$ per correct run', usd]];
    const variants = [...new Set(C.map(c => c.v))].sort();
    const order = [...MODELS, '-'];
    const max = Object.fromEntries(METRICS.map(([k]) => [k, Math.max(...C.map(c => c[k] || 0))]));
    const flat = []; // for hover
    const col = (v, k, fmt) => {
      const cs = order.map(m => C.find(c => c.v === v && c.m === m)).filter(Boolean);
      const h = 12, gap = 2, W = 260, LW = 58, Hh = cs.length * (h + gap) - gap;
      return `<svg class="viz bars" viewBox="0 0 ${W} ${Hh}" width="${W}" height="${Hh}">` + cs.map((c, i) => {
        const val = c[k], y = i * (h + gap), w = val == null ? 0 : Math.max(2, (W - LW) * val / max[k]);
        flat.push(c);
        return `<a href="${link(c)}" class="mk ${slot(c.m)}${c.rate < .5 ? ' hollow' : ''}" data-i="${flat.length - 1}"><rect class="hit" x="0" y="${y}" width="${W}" height="${h}"/>` +
          (val == null ? `<text class="tick" x="0" y="${y + h - 2.5}">no correct run</text>`
            : `<rect x="0" y="${y}" width="${w}" height="${h}" rx="0"/><rect class="cap" x="${Math.max(0, w - 4)}" y="${y}" width="4" height="${h}" rx="3"/><text class="tick" x="${w + 5}" y="${y + h - 2.5}">${fmt(val)}</text>`) + '</a>';
      }).join('') + '</svg>';
    };
    B.innerHTML = legend + '<div class="wrap"><table class="costtab"><tr><th>Architecture</th>' + METRICS.map(([, l]) => `<th>${l}</th>`).join('') + '</tr>' +
      variants.map(v => `<tr><td>${esc(cell(v))}</td>` + METRICS.map(([k, , f]) => `<td>${col(v, k, f)}</td>`).join('') + '</tr>').join('') + '</table></div>';
    hover(B, flat);
  }

  function hover(root, list) {
    let t = document.getElementById('viz-tip');
    if (!t) { t = document.createElement('div'); t.id = 'viz-tip'; t.hidden = true; document.body.appendChild(t); }
    root.querySelectorAll('a.mk').forEach(a => {
      a.addEventListener('mouseenter', () => { t.innerHTML = tip(list[+a.dataset.i]); t.hidden = false; });
      a.addEventListener('mousemove', e => { t.style.left = (e.clientX + 14) + 'px'; t.style.top = (e.clientY + 14) + 'px'; });
      a.addEventListener('mouseleave', () => { t.hidden = true; });
    });
  }
});
