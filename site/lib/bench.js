/* FlowDrop AI Bench — shared browser runtime for every visual.
 *
 * One study and one filter state, carried in the URL query string, applied the same way on
 * every page:
 *
 *   ?study=claude-2026-09&benchmark=bench_3_markdown_llm,bench_5_react_agent&page=small
 *
 * The URL is the only truth. Every link marked data-nav is rewritten to carry the current
 * query, so moving between visuals keeps the selection; copying the address shares it.
 *
 * A study (studies/<id>.json, published in data/facets.json) is a named, frozen scope: the
 * rows every page starts from before the on-page filters. `?study=all` is every run. When the
 * address names no study the site opens in registry.json's default and writes it into the
 * address, so a copied link keeps meaning the same rows when the default later changes.
 * Filters narrow within the study; a filter value the study does not contain is shown greyed
 * as "not in study" and a notice says so, never a silently empty table. Reset clears the
 * filters and keeps the study.
 *
 * Filters are defined once in site/filters.json (published as data/facets.json with the
 * distinct values and counts over every run). A visual lists the filter ids it honours in its
 * visual.json; the bar shows those, the URL keeps all of them, so a filter a page does not
 * use survives the visit and applies again on the next page.
 *
 * A visual's page.js does:
 *
 *   Bench.ready(({rows, all, everything, facets, state, study, focus}) => { ...render rows... });
 *
 * `rows` is data/scores.json after the study and the active filters, `all` after the study
 * only, `everything` the whole dataset. `facets.values` are recounted within the study, so a
 * legend or a menu built from them shows what the study contains. The callback runs once when
 * the data is loaded and again after every change. Numbers are numbers. A visual that declares
 * "focus": "<filter id>" in its visual.json gets that filter as a single-select and
 * `focus.value` is the one value; the rows are already restricted to it.
 */
window.Bench = (function () {
  'use strict';
  const ROOT = document.documentElement.getAttribute('data-root') || './';
  const ORDER = ['correct', 'degraded', 'silent', 'format', 'loud', 'control', 'stale', 'excluded'];
  const ALL = 'all';                                  // ?study=all: every run
  const subs = [];
  let data = null;         // {rows, facets}
  let study = null;        // the active study record, or null for every run
  let studyParam = new URLSearchParams(location.search).get('study');
  let state = parseQuery(location.search);

  // ------------------------------------------------------------ URL state
  function parseQuery(qs) {
    const s = {};
    for (const [k, v] of new URLSearchParams(qs)) {
      if (!v || k === 'study') continue;
      // Values are individually encoded, so a comma inside a value survives the split.
      s[k] = new Set(v.split(',').map(decodeURIComponent).filter(Boolean));
    }
    return s;
  }
  function studies() { return (data && data.facets.studies) || []; }
  function query() {
    const p = [];
    if (studies().length) p.push('study=' + encodeURIComponent(study ? study.id : ALL));
    for (const k of Object.keys(state).sort()) {
      if (state[k].size) p.push(k + '=' + [...state[k]].sort().map(encodeURIComponent).join(','));
    }
    return p.length ? '?' + p.join('&') : '';
  }
  function writeUrl() { history.replaceState(null, '', location.pathname + query() + location.hash); }
  function set(id, values) {
    if (values && values.size) state[id] = new Set(values); else delete state[id];
    writeUrl(); rewriteLinks(); notify();
  }
  function reset() { state = {}; writeUrl(); rewriteLinks(); notify(); }
  // Settle the study from the address: a known id, `all`, else the registry default. Written
  // back so every link and every copied address names it explicitly.
  function settleStudy() {
    const list = studies();
    if (!list.length) { study = null; return; }
    if (studyParam === ALL) study = null;
    else study = list.find(s => s.id === studyParam) || list.find(s => s.id === data.facets.default_study) || null;
    writeUrl();
  }
  function setStudy(id) {
    studyParam = id; settleStudy(); rewriteLinks(); notify();
  }
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
  function inStudy(row) {
    if (!study) return true;
    for (const f of defs()) {
      const want = study.scope[f.id];
      if (!want) continue;
      const have = values(row, f);
      if (have.length === 1 && have[0] === '-') continue;   // no value at all (a control run has no model): belongs to every study
      if (!have.some(v => want.includes(v))) return false;
    }
    return true;
  }
  function universe() { return data.rows.filter(inStudy); }
  function matches(row) {
    for (const f of defs()) {
      const sel = state[f.id];
      if (!sel || !sel.size) continue;
      if (!values(row, f).some(v => sel.has(v))) return false;
    }
    return true;
  }
  function filtered() { return universe().filter(matches); }
  // Facet values recounted within the study, in the published order; values the study has no
  // run for are dropped here and listed separately by outside().
  let scoped = null;       // {values: {fid: [[v, n]]}, outside: {fid: [v]}} for the current study
  function rescope() {
    const rows = universe(), vals = {}, out = {};
    for (const f of defs()) {
      const c = new Map();
      for (const r of rows) for (const v of values(r, f)) c.set(v, (c.get(v) || 0) + 1);
      const order = (data.facets.values[f.id] || []).map(x => x[0]);
      for (const v of c.keys()) if (!order.includes(v)) order.push(v);
      vals[f.id] = order.filter(v => c.has(v)).map(v => [v, c.get(v)]);
      out[f.id] = order.filter(v => !c.has(v));
    }
    scoped = {values: vals, outside: out};
  }
  function facets() { return Object.assign({}, data.facets, {values: scoped.values}); }
  // The focus value: the single selected value of the focus filter, else the first the URL
  // names, else the first value the study has. Written back to the URL so the next page inherits it.
  function focusId() { const m = document.getElementById('bench-filters'); return m ? (m.getAttribute('data-focus') || '') : ''; }
  function focusValue(f) {
    const facet = (scoped.values[f.id] || []).map(x => x[0]);
    const sel = state[f.id] ? [...state[f.id]].filter(v => facet.includes(v)) : [];
    const v = sel.length ? sel[0] : facet[0];
    if (v !== undefined && !(state[f.id] && state[f.id].size === 1 && state[f.id].has(v))) { state[f.id] = new Set([v]); writeUrl(); }
    return v;
  }
  function focus() { const f = defs().find(x => x.id === focusId()); return f ? {id: f.id, label: f.label, value: focusValue(f), column: f.column, filter: f} : null; }

  // ------------------------------------------------------------ filter bar
  function label(f, v) {
    const m = f.labels && data.facets.labels[f.labels];
    return (m && m[v]) || v;
  }
  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function renderStudyRow(mount) {
    const list = studies();
    if (!list.length) return;
    const row = el('div', 'study-row');
    const lab = el('label', 'k', 'Study'); lab.htmlFor = 'bench-study';
    const sel = el('select'); sel.id = 'bench-study';
    for (const s of list) { const o = el('option', null, s.title); o.value = s.id; o.selected = !!study && s.id === study.id; sel.appendChild(o); }
    const o = el('option', null, 'Everything, every run'); o.value = ALL; o.selected = !study; sel.appendChild(o);
    sel.addEventListener('change', () => setStudy(sel.value));
    row.appendChild(lab); row.appendChild(sel);
    row.appendChild(el('span', 'blurb', study ? study.blurb : 'Every run in the dataset, across every model, corpus version and contributor. Pick a study for a curated comparison.'));
    mount.appendChild(row);
  }
  function renderBar() {
    const mount = document.getElementById('bench-filters');
    if (!mount) return;
    const wanted = (mount.getAttribute('data-filters') || '').split(',').filter(Boolean);
    const fid = mount.getAttribute('data-focus') || '';
    const show = defs().filter(f => wanted.includes(f.id) || f.id === fid);
    mount.innerHTML = '';
    renderStudyRow(mount);
    if (!show.length && !studies().length) return;
    for (const f of show) {
      const facet = scoped.values[f.id] || [];
      if (f.id === fid) {                              // single-select: the page compares within one value
        if (!facet.length) continue;                  // nothing to focus on yet
        const cur = focusValue(f);
        const wrap = el('label', 'flt focus');
        wrap.appendChild(el('span', null, f.label + ': '));
        const sel = el('select');
        for (const [v] of facet) { const o = el('option', null, label(f, v)); o.value = v; o.selected = v === cur; sel.appendChild(o); }
        sel.addEventListener('change', () => set(f.id, new Set([sel.value])));
        wrap.appendChild(sel); mount.appendChild(wrap);
        continue;
      }
      const outside = study ? (scoped.outside[f.id] || []) : [];
      if (facet.length < 2 && !outside.length && !(state[f.id] && state[f.id].size)) continue;   // nothing to choose
      const sel = state[f.id] || new Set();
      const d = el('details', 'flt' + (sel.size ? ' on' : ''));
      d.appendChild(el('summary', null, f.label + ': ' + (sel.size ? (sel.size === 1 ? label(f, [...sel][0]) : sel.size + ' of ' + facet.length) : 'all')));
      const menu = el('div', 'menu');
      const item = (v, n, out) => {
        const id = 'f-' + f.id + '-' + btoa(unescape(encodeURIComponent(v))).replace(/[^a-z0-9]/gi, '');
        const l = el('label', out ? 'out' : null);
        const c = el('input'); c.type = 'checkbox'; c.id = id; c.checked = sel.has(v);
        c.addEventListener('change', () => { const ns = new Set(state[f.id] || []); c.checked ? ns.add(v) : ns.delete(v); set(f.id, ns); });
        l.appendChild(c); l.appendChild(el('span', null, label(f, v)));
        l.appendChild(el('small', null, out ? 'not in study' : n));
        l.title = out ? 'No run of this study has this value; choose Everything as the study to include it.' : '';
        menu.appendChild(l);
      };
      for (const [v, n] of facet) item(v, n, false);
      if (outside.length) { menu.appendChild(el('hr')); for (const v of outside) item(v, 0, true); }
      if (sel.size) {
        const clr = el('button', null, 'clear'); clr.type = 'button';
        clr.addEventListener('click', () => set(f.id, null)); menu.appendChild(clr);
      }
      d.appendChild(menu); mount.appendChild(d);
    }
    // Filters active on this URL that this visual does not show still apply: say so.
    const hidden = Object.keys(state).filter(k => state[k].size && !show.some(f => f.id === k) && defs().some(f => f.id === k));
    const rows = filtered(), all = universe();
    const sum = el('span', 'flt-sum');
    sum.textContent = (rows.length === all.length ? all.length + ' runs' : rows.length + ' of ' + all.length + ' runs') + (study ? ' in this study' : '');
    if (hidden.length) sum.textContent += ' (also filtered by ' + hidden.join(', ') + ')';
    mount.appendChild(sum);
    if (Object.keys(state).some(k => state[k].size)) {
      const r = el('button', 'flt-reset', study ? 'reset filters, keep study' : 'reset filters'); r.type = 'button';
      r.addEventListener('click', reset); mount.appendChild(r);
    }
    // A selected value the study has no run for: say which, offer the way out.
    if (study) {
      const outs = [];
      for (const f of defs()) for (const v of (state[f.id] || [])) if ((scoped.outside[f.id] || []).includes(v)) outs.push(f.label.toLowerCase() + ' ' + label(f, v));
      if (outs.length) {
        const n = el('div', 'flt-note');
        n.appendChild(el('b', null, outs.join(', ')));
        n.appendChild(document.createTextNode((outs.length === 1 ? ' is' : ' are') + ' not part of this study. '));
        const a = el('a', null, 'Show everything'); a.href = '#';
        a.addEventListener('click', e => { e.preventDefault(); setStudy(ALL); });
        n.appendChild(a); n.appendChild(document.createTextNode(' to include it, or clear that filter.'));
        mount.appendChild(n);
      }
    }
  }
  document.addEventListener('click', e => {          // one open menu at a time
    document.querySelectorAll('details.flt[open]').forEach(d => { if (!d.contains(e.target)) d.removeAttribute('open'); });
  });

  // ------------------------------------------------------------ lifecycle
  function payload() {
    return { rows: filtered(), all: universe(), everything: data.rows, facets: facets(), state, study, order: ORDER, focus: focus() };
  }
  function notify() {
    rescope(); renderBar();
    const p = payload();
    for (const fn of subs) fn(p);
  }
  async function load() {
    const [rows, facets] = await Promise.all([
      fetch(ROOT + 'data/scores.json').then(r => r.json()),
      fetch(ROOT + 'data/facets.json').then(r => r.json())]);
    data = { rows, facets };
    settleStudy(); rescope();
    focus();                                          // settle the focus value in the URL before links are written
    rewriteLinks(); notify();
  }
  function ready(fn) { subs.push(fn); if (data) fn(payload()); }


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
    nav.appendChild(b('← previous', -1, st.page === 0));
    nav.appendChild(Object.assign(document.createElement('span'), {className: 'pos', textContent: (from + 1) + '–' + to + ' of ' + items.length}));
    nav.appendChild(b('next →', 1, st.page >= pages - 1));
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
  const cellCode = id => cell(id).split(' ')[0];   // 'B4' from 'B4 HTML → …'; the anchor on the architectures page
  const num = (v, d = 2) => (v === '' || v == null || Number.isNaN(+v)) ? '—' : (+v).toFixed(d);
  const UNGRADED = new Set(['control', 'stale', 'excluded']);
  const graded = rows => rows.filter(r => !UNGRADED.has(r.outcome));
  const href = path => ROOT + path;                        // path relative to the site root

  document.addEventListener('DOMContentLoaded', () => { load().catch(e => { const m = document.getElementById('bench-filters'); if (m) m.textContent = 'data failed to load: ' + e; }); });
  // Label for any filter value (cell names for benchmarks, the id otherwise).
  const label_ = (fid, v) => { const f = defs().find(x => x.id === fid); return f ? label(f, v) : v; };
  return { ready, set, reset, setStudy, study: () => study, state: () => state, query, esc, pill, cell, cellCode, num, graded, href, label: label_, pager, ORDER, UNGRADED };
})();
