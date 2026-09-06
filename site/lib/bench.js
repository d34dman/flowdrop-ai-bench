/* FlowDrop AI Bench — shared browser runtime for every visual.
 *
 * One filter state, carried in the URL query string, applied the same way on every page:
 *
 *   ?task=redact.v1&benchmark=bench_3_markdown_llm,bench_5_react_agent&model=claude-sonnet-5&page=small
 *
 * The URL is the only truth. Every link marked data-nav is rewritten to carry the current
 * query, so moving between visuals keeps the selection; copying the address shares it.
 * Filters are defined once in site/filters.json (published as data/facets.json with the
 * distinct values and counts). A visual lists the filter ids it honours in its visual.json;
 * the bar shows those, the URL keeps all of them, so a filter a page does not use survives
 * the visit and applies again on the next page.
 *
 * A visual's page.js does:
 *
 *   Bench.ready(({rows, all, facets, state, focus}) => { ...render rows... });
 *
 * `rows` is data/scores.json after the active filters, `all` before them. The callback runs
 * once when the data is loaded and again after every filter change. Numbers are numbers.
 * A visual that declares "focus": "<filter id>" in its visual.json gets that filter as a
 * single-select and `focus.value` is the one value; the rows are already restricted to it.
 */
window.Bench = (function () {
  'use strict';
  const ROOT = document.documentElement.getAttribute('data-root') || './';
  const ORDER = ['correct', 'degraded', 'silent', 'format', 'loud', 'control', 'stale', 'excluded'];
  const subs = [];
  let data = null;         // {rows, facets}
  let state = parseQuery(location.search);

  // ------------------------------------------------------------ URL state
  function parseQuery(qs) {
    const s = {};
    for (const [k, v] of new URLSearchParams(qs)) {
      if (!v) continue;
      // Values are individually encoded, so a comma inside a value survives the split.
      s[k] = new Set(v.split(',').map(decodeURIComponent).filter(Boolean));
    }
    return s;
  }
  function query() {
    const p = [];
    for (const k of Object.keys(state).sort()) {
      if (state[k].size) p.push(k + '=' + [...state[k]].sort().map(encodeURIComponent).join(','));
    }
    return p.length ? '?' + p.join('&') : '';
  }
  function set(id, values) {
    if (values && values.size) state[id] = new Set(values); else delete state[id];
    history.replaceState(null, '', location.pathname + query() + location.hash);
    rewriteLinks(); notify();
  }
  function reset() { state = {}; history.replaceState(null, '', location.pathname + location.hash); rewriteLinks(); notify(); }
  function rewriteLinks() {
    const q = query();
    document.querySelectorAll('a[data-nav]').forEach(a => {
      const base = a.getAttribute('data-nav') || a.getAttribute('href').split('?')[0];
      if (!a.getAttribute('data-nav')) a.setAttribute('data-nav', base);
      a.setAttribute('href', base + q);
    });
  }

  // ------------------------------------------------------------ filtering
  function defs() { return (data && data.facets.filters) || []; }
  function values(row, f) {
    const v = row[f.column];
    if (v === undefined || v === null || v === '') return ['-'];
    return f.split ? String(v).split(f.split).filter(Boolean) : [String(v)];
  }
  function matches(row) {
    for (const f of defs()) {
      const sel = state[f.id];
      if (!sel || !sel.size) continue;
      if (!values(row, f).some(v => sel.has(v))) return false;
    }
    return true;
  }
  function filtered() { return data.rows.filter(matches); }
  // The focus value: the single selected value of the focus filter, else the first the URL
  // names, else the first facet value. Written back to the URL so the next page inherits it.
  function focusId() { const m = document.getElementById('bench-filters'); return m ? (m.getAttribute('data-focus') || '') : ''; }
  function focusValue(f) {
    const facet = (data.facets.values[f.id] || []).map(x => x[0]);
    const sel = state[f.id] ? [...state[f.id]].filter(v => facet.includes(v)) : [];
    const v = sel.length ? sel[0] : facet[0];
    if (v !== undefined && !(state[f.id] && state[f.id].size === 1 && state[f.id].has(v))) { state[f.id] = new Set([v]); history.replaceState(null, '', location.pathname + query() + location.hash); }
    return v;
  }
  function focus() { const f = defs().find(x => x.id === focusId()); return f ? {id: f.id, label: f.label, value: focusValue(f), column: f.column, filter: f} : null; }

  // ------------------------------------------------------------ filter bar
  function label(f, v) {
    const m = f.labels && data.facets.labels[f.labels];
    return (m && m[v]) || v;
  }
  function renderBar() {
    const mount = document.getElementById('bench-filters');
    if (!mount) return;
    const wanted = (mount.getAttribute('data-filters') || '').split(',').filter(Boolean);
    const fid = mount.getAttribute('data-focus') || '';
    const show = defs().filter(f => wanted.includes(f.id) || f.id === fid);
    mount.innerHTML = '';
    if (!show.length) return;
    for (const f of show) {
      if (f.id === fid) {                              // single-select: the page compares within one value
        const facet = data.facets.values[f.id] || [];
        if (!facet.length) continue;                  // nothing to focus on yet
        const cur = focusValue(f);
        const wrap = document.createElement('label'); wrap.className = 'flt focus';
        wrap.appendChild(Object.assign(document.createElement('span'), {textContent: f.label + ': '}));
        const sel = document.createElement('select');
        for (const [v] of facet) { const o = document.createElement('option'); o.value = v; o.textContent = label(f, v); o.selected = v === cur; sel.appendChild(o); }
        sel.addEventListener('change', () => set(f.id, new Set([sel.value])));
        wrap.appendChild(sel); mount.appendChild(wrap);
        continue;
      }
      const facet = data.facets.values[f.id] || [];
      if (facet.length < 2 && !(state[f.id] && state[f.id].size)) continue;   // nothing to choose
      const sel = state[f.id] || new Set();
      const d = document.createElement('details'); d.className = 'flt' + (sel.size ? ' on' : '');
      const s = document.createElement('summary');
      s.textContent = f.label + ': ' + (sel.size ? (sel.size === 1 ? label(f, [...sel][0]) : sel.size + ' of ' + facet.length) : 'all');
      d.appendChild(s);
      const menu = document.createElement('div'); menu.className = 'menu';
      for (const [v, n] of facet) {
        const id = 'f-' + f.id + '-' + btoa(unescape(encodeURIComponent(v))).replace(/[^a-z0-9]/gi, '');
        const l = document.createElement('label');
        const c = document.createElement('input'); c.type = 'checkbox'; c.id = id; c.checked = sel.has(v);
        c.addEventListener('change', () => { const ns = new Set(state[f.id] || []); c.checked ? ns.add(v) : ns.delete(v); set(f.id, ns); });
        l.appendChild(c);
        const t = document.createElement('span'); t.textContent = label(f, v); l.appendChild(t);
        const k = document.createElement('small'); k.textContent = n; l.appendChild(k);
        menu.appendChild(l);
      }
      if (sel.size) {
        const clr = document.createElement('button'); clr.type = 'button'; clr.textContent = 'clear';
        clr.addEventListener('click', () => set(f.id, null)); menu.appendChild(clr);
      }
      d.appendChild(menu); mount.appendChild(d);
    }
    // Filters active on this URL that this visual does not show still apply: say so.
    const hidden = Object.keys(state).filter(k => state[k].size && !show.some(f => f.id === k) && defs().some(f => f.id === k));
    const rows = filtered();
    const sum = document.createElement('span'); sum.className = 'flt-sum';
    sum.textContent = rows.length === data.rows.length ? data.rows.length + ' runs' : rows.length + ' of ' + data.rows.length + ' runs';
    if (hidden.length) sum.textContent += ' (also filtered by ' + hidden.join(', ') + ')';
    mount.appendChild(sum);
    if (Object.keys(state).some(k => state[k].size)) {
      const r = document.createElement('button'); r.type = 'button'; r.className = 'flt-reset'; r.textContent = 'reset filters';
      r.addEventListener('click', reset); mount.appendChild(r);
    }
  }
  document.addEventListener('click', e => {          // one open menu at a time
    document.querySelectorAll('details.flt[open]').forEach(d => { if (!d.contains(e.target)) d.removeAttribute('open'); });
  });

  // ------------------------------------------------------------ lifecycle
  function notify() {
    renderBar();
    const rows = filtered();
    for (const fn of subs) fn({ rows, all: data.rows, facets: data.facets, state, order: ORDER, focus: focus() });
  }
  async function load() {
    const [rows, facets] = await Promise.all([
      fetch(ROOT + 'data/scores.json').then(r => r.json()),
      fetch(ROOT + 'data/facets.json').then(r => r.json())]);
    data = { rows, facets };
    focus();                                          // settle the focus value in the URL before links are written
    rewriteLinks(); notify();
  }
  function ready(fn) { subs.push(fn); if (data) fn({ rows: filtered(), all: data.rows, facets: data.facets, state, order: ORDER, focus: focus() }); }


  // ------------------------------------------------------------ pager
  // Bench.pager(el, items, rows => html, {size: 25}): renders one page of `items` into `el` with
  // prev/next and a page-size control. Page position is in memory only (never the URL: filters are
  // shared by link, a page number is not) and goes back to the first page whenever the list changes.
  const pagers = new WeakMap();
  const PAGE_SIZES = [25, 50, 100, 0];   // 0 = all
  function pager(el, items, render, o = {}) {
    let st = pagers.get(el);
    const sig = items.length + ':' + (items[0] && items[0].run_id) + ':' + (items[items.length - 1] && items[items.length - 1].run_id);
    if (!st) { st = {page: 0, size: o.size || 25, sig}; pagers.set(el, st); }
    if (st.sig !== sig) { st.page = 0; st.sig = sig; }
    const size = st.size || items.length || 1, pages = Math.max(1, Math.ceil(items.length / size));
    st.page = Math.min(st.page, pages - 1);
    const from = st.page * size, to = Math.min(items.length, from + size);
    el.innerHTML = render(items.slice(from, to));
    if (items.length <= PAGE_SIZES[0]) return;
    const nav = document.createElement('div'); nav.className = 'pager';
    const b = (t, d, dis) => { const x = document.createElement('button'); x.type = 'button'; x.textContent = t; x.disabled = dis; x.addEventListener('click', () => { st.page += d; pager(el, items, render, o); }); return x; };
    nav.appendChild(b('\u2190 previous', -1, st.page === 0));
    nav.appendChild(Object.assign(document.createElement('span'), {className: 'pos', textContent: (from + 1) + '\u2013' + to + ' of ' + items.length}));
    nav.appendChild(b('next \u2192', 1, st.page >= pages - 1));
    const sel = document.createElement('select');
    for (const n of PAGE_SIZES) { const op = document.createElement('option'); op.value = n; op.textContent = n ? n + ' per page' : 'all'; op.selected = n === st.size; sel.appendChild(op); }
    sel.addEventListener('change', () => { st.size = +sel.value; st.page = 0; pager(el, items, render, o); });
    nav.appendChild(sel);
    el.appendChild(nav);
  }

  // ------------------------------------------------------------ helpers for visuals
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pill = (c, n, title) => `<span class="pill ${esc(c)}"${title ? ` title="${esc(title)}"` : ''}>${esc(c)}${n == null ? '' : ' ' + n}</span>`;
  const cell = id => (data && data.facets.labels.cell[id]) || id;
  const num = (v, d = 2) => (v === '' || v == null || Number.isNaN(+v)) ? '—' : (+v).toFixed(d);
  const UNGRADED = new Set(['control', 'stale', 'excluded']);
  const graded = rows => rows.filter(r => !UNGRADED.has(r.outcome));
  const href = path => ROOT + path;                        // path relative to the site root

  document.addEventListener('DOMContentLoaded', () => { load().catch(e => { const m = document.getElementById('bench-filters'); if (m) m.textContent = 'data failed to load: ' + e; }); });
  // Label for any filter value (cell names for benchmarks, the id otherwise).
  const label_ = (fid, v) => { const f = defs().find(x => x.id === fid); return f ? label(f, v) : v; };
  return { ready, set, reset, state: () => state, query, esc, pill, cell, num, graded, href, label: label_, pager, ORDER, UNGRADED };
})();
