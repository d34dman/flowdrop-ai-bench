#!/usr/bin/env python3
"""Deterministic scorer for FlowDrop AI Bench. No LLM. Standard library only.

Grades every run in runs/*.json whose output is in outputs/<run_id>.md against the gold
body of its corpus page, using the manifest's target, protected, homonym and chrome
lists. Writes data/runs.csv (ledger + metering, one row per run) and data/scores.csv
(the same rows plus the axes and the outcome class).

    python3 scoring/score.py                      # score everything
    python3 scoring/score.py --explain <run_id-prefix>

Axes, all in [0, 1]:
  recall      correct glyphs / (correct glyphs + leaks). A leak is a target name still
              readable in a document sentence. Names in chrome do not count either way.
  precision   correct glyphs / glyphs placed on document text. A glyph on a protected
              name, a homonym, or an ordinary word is a miss.
  subject     protected names kept / (kept + glyphs placed on protected names).
  homonym     homonyms kept / (kept + glyphs placed on homonyms); 1.0 when none is present.
  fidelity    gold sentences (>= 4 words) found in the output at >= 0.90 similarity,
              redaction-tolerant / gold sentences.
  fabrication output sentences found neither in the gold nor in the page chrome /
              output sentences.
  structure   gold headings found / gold headings.
Gates: G0 delivered (>= 500 chars), G1 format (Markdown, not HTML, at least one heading),
G2 scope (structure >= 0.5). Class: loud (G0 fails), format (G1 fails), silent (G2 fails
or any axis below 0.75 with all gates passed), degraded (all axes >= 0.75, not all at
threshold), correct (recall, precision, subject, homonym, fidelity >= 0.95 and
fabrication <= 0.05). B0 and B1 are controls: scored, classed 'control'.
A run named in exclusions/ (see scoring/exclude.py) is classed 'excluded': kept in the
CSVs with excluded_kind and excluded_reason, ungraded like 'stale'.
"""
import csv, difflib, html as htmlmod, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS, OUT, DATA, EXCL = (os.path.join(ROOT, d) for d in ('runs', 'outputs', 'data', 'exclusions'))
RED, HOM = 'REDACTEDTOKEN', 'HOMONYMTOKEN'
MIN_WORDS, MATCH = 4, 0.90
THRESH = dict(recall=0.95, precision=0.95, subject=0.95, homonym=0.95, fidelity=0.95, fabrication=0.05)
DEGRADED = 0.75
CONTROLS = ('bench_0_floor', 'bench_1_reference')
EXPLAIN = '--explain' in sys.argv

# ------------------------------------------------------------------ corpus
_corpus = {}

def corpus(version):
    if version in _corpus: return _corpus[version]
    base = os.path.join(ROOT, 'corpus', version)
    m = json.load(open(os.path.join(base, 'manifest.json'), encoding='utf-8'))
    glyph_char = m['glyph'][0]
    comps = [c.lower() for c in m['competitors']]
    comp_first = [c.split()[0] for c in comps]                 # 'lumen cms' -> 'lumen'
    suffixes = {c.split()[1] for c in comps if ' ' in c}      # {'cms'}
    prot = [p.lower() for p in m['protected_names']]
    real = [c.lower().split()[0] for c in m.get('real_names', [])]  # first word, like comp_first
    pages = {}
    for page, d in m['pages'].items():
        gtext = open(os.path.join(base, d['gold']), encoding='utf-8').read()
        # Mark each homonym at its exact position so it is neither a target nor a leak.
        lines = gtext.split('\n')
        for h in sorted(d['homonyms'], key=lambda h: (h['line'], -h['col'])):
            ln, col, name = h['line'] - 1, h['col'] - 1, h['name']
            assert lines[ln][col:col + len(name)].lower() == name.lower(), (page, h)
            lines[ln] = lines[ln][:col] + f' {HOM} ' + lines[ln][col + len(name):]
        gmarked = '\n'.join(lines)
        gs, gh = sentences(canon(gmarked, glyph_char))
        page_html = open(os.path.join(base, d['html']), encoding='utf-8').read()
        chrome = html_text(page_html)
        cs, _ = sentences(canon(chrome, glyph_char))
        pages[page] = dict(sents=gs, heads=gh, index=Index(gs, gh, comp_first), chrome_index=Index(cs, gh, comp_first),
                           targets=len(d['targets']), homonyms=len(d['homonyms']),
                           protected=len(d['protected']), sha256=d['sha256'])
    _corpus[version] = dict(glyph=m['glyph'], glyph_char=glyph_char, comps=comp_first, suffixes=suffixes,
                            prot=prot, real=real, pages=pages)
    return _corpus[version]

def html_text(page_html):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', page_html, flags=re.S | re.I)
    t = re.sub(r'<br\s*/?>|</(p|li|h[1-6]|tr|div|section|nav|footer|header|aside)>', '\n', t, flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    return htmlmod.unescape(t)

# ------------------------------------------------------------------ text prep
def canon(text, glyph_char):
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = text.replace('&amp;', '&')
    text = re.sub(re.escape(glyph_char) + r'+', ' ' + RED + ' ', text)
    text = re.sub(r'▌+|█+', ' ' + RED + ' ', text)          # tolerate the legacy glyph
    return text

def unfence(text):
    m = re.match(r'\s*```[a-zA-Z]*\s*\n(.*)\n```\s*$', text, re.S)
    return m.group(1) if m else text

def html_density(text):
    tags = len(re.findall(r'</?(?:div|span|p|a|table|body|html|ul|li|h[1-6])\b[^>]*>', text, re.I))
    return tags / max(len(text) / 1000, .001)

def norm_words(s):
    s = s.lower().replace('’', "'").replace('‘', "'")
    s = re.sub(r'[#*_`>|]', ' ', s)
    s = s.replace(RED.lower(), RED).replace(HOM.lower(), HOM)
    return [w for w in re.findall(r"[a-z0-9À-ɏ:]+(?:'[a-z]+)?|" + RED + '|' + HOM, s) if w and w != ':']

def sentences(text):
    out, heads = [], []
    for para in re.split(r'\n\s*\n|\n(?=\s*[-*]\s)|\n(?=\s*\d+\.\s)|\n(?=#)|\n(?=\|)', text):
        para = para.strip()
        if not para: continue
        if para.startswith('#'):
            heads.append(norm_words(para.lstrip('#').strip())); continue
        if para.startswith('|'):
            for row in para.split('\n'):
                if re.match(r'^\|[-\s|:]+\|$', row): continue
                w = norm_words(row)
                if len(w) >= 2: out.append(w)      # table rows are short by nature
            continue
        para = re.sub(r'^\s*(?:[-*]|\d+\.)\s+', '', para)
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z"“(])', para):
            w = norm_words(s)
            if len(w) >= MIN_WORDS: out.append(w)
    return out, heads

def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

class Index:
    def __init__(self, sents, extra, comps):
        self.sents, self.comps = sents, comps
        self.sets = [set(w for w in s if w not in (RED, HOM)) for s in sents]
        self.blob = ' ' + ' '.join(' '.join(x) for x in list(sents) + list(extra)) + ' '
        self.grams = set()
        for x in list(sents) + list(extra):
            m = self.mask(x)
            for i in range(len(m) - 3): self.grams.add(tuple(m[i:i + 4]))
        self.inv = {}
        for i, st in enumerate(self.sets):
            for w in st: self.inv.setdefault(w, []).append(i)
        self.common = {w for w, ids in self.inv.items() if len(ids) > 0.2 * max(len(sents), 5)}
    def is_target(self, w): return any(w.startswith(c) for c in self.comps)
    def mask(self, words):
        out = []
        for w in words:
            t = RED if (w == RED or self.is_target(w)) else w
            if t == RED and out and out[-1] == RED: continue
            out.append(t)
        return out
    def contains(self, words):
        seq = ' ' + ' '.join(words) + ' '
        if seq in self.blob: return True
        seq = ' ' + ' '.join(self.mask(words)) + ' '
        blob = re.sub(r"\b(" + '|'.join(re.escape(c) for c in self.comps) + r")[a-z0-9']*", RED, self.blob)
        blob = re.sub(r'(?:' + RED + r' )+' + RED, RED, blob)
        return seq in blob
    def coverage(self, words):
        m = self.mask(words)
        if len(m) < 4: return 1.0 if self.contains(words) else 0.0
        hit = [False] * len(m)
        for i in range(len(m) - 3):
            if tuple(m[i:i + 4]) in self.grams:
                for k in range(i, i + 4): hit[k] = True
        return sum(hit) / len(m)
    def best(self, words):
        ws = set(w for w in words if w not in (RED, HOM))
        if not ws: return None, 0
        if self.contains(words): return -1, 1.0
        cand = Counter()
        for w in ws - self.common:
            for i in self.inv.get(w, ()): cand[i] += 1
        best, score = None, 0
        for i, c in cand.most_common(40):
            j = c / max(len((ws - self.common) | (self.sets[i] - self.common)), 1)
            if j < 0.3: break
            s = self.sents[i]
            r = max(ratio(words, s), ratio(self.mask(words), self.mask(s)))
            if r > score: best, score = i, r
        return best, score

# ------------------------------------------------------------------ scoring
def score(text, page, version):
    C = corpus(version); g = C['pages'][page]
    is_target = lambda w: any(w.startswith(c) for c in C['comps'])
    is_prot = lambda w: any(w.startswith(p) for p in C['prot'])
    # real vs fictional competitor: the gap between the two recalls is how much a cell
    # leans on model prior rather than on the prompt's list.
    cls_of = lambda w: 'real' if any(w.startswith(c) for c in C['real']) else 'fict'
    raw = text
    text = unfence(text); fenced = text is not raw
    density = html_density(text)
    text = canon(text, C['glyph_char'])
    osents, oheads = sentences(text)
    glyphs_total = len(re.findall(re.escape(C['glyph_char']) + r'+|▌+', raw))
    gc = Counter()   # glyph_correct, glyph_protected, glyph_homonym, glyph_other, glyph_chrome
    leaks = leaks_chrome = hom_kept = 0
    lc = Counter()   # leaks by class: real, fict

    def leak(words, n=None):
        """Count readable target words as leaks (at most n of them), by class."""
        nonlocal leaks
        ws = [w for w in words if is_target(w)]
        if n is not None: ws = ws[:n]
        leaks += len(ws)
        for w in ws: lc[cls_of(w)] += 1

    def classify_glyphs(gold_words, out_words):
        """Word-align an output sentence with its gold sentence; say what each glyph covers."""
        nonlocal leaks, hom_kept
        sm = difflib.SequenceMatcher(None, gold_words, out_words, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            seg_g, seg_o = gold_words[i1:i2], out_words[j1:j2]
            k = seg_o.count(RED)
            if tag == 'equal':
                leak(seg_o)
                continue
            if k:
                pool = [w for w in seg_g if w not in C['suffixes']] if tag == 'replace' else []
                pool.sort(key=lambda w: 0 if is_target(w) else 1 if w == HOM else 2 if is_prot(w) else 3)
                for _ in range(k):
                    w = pool.pop(0) if pool else None
                    if w is not None and is_target(w): gc['correct'] += 1; gc['correct_' + cls_of(w)] += 1
                    elif w == HOM: gc['homonym'] += 1
                    elif w is not None and is_prot(w): gc['protected'] += 1
                    else: gc['other'] += 1
                if EXPLAIN: print(f'  glyph x{k} <- gold {seg_g} | out: {" ".join(out_words)[:100]}')
            # homonyms kept: a HOM in gold aligned to a readable target word in the output
            if HOM in seg_g:
                readable = sum(1 for w in seg_o if is_target(w))
                hom_kept += min(seg_g.count(HOM), readable)
                # those readable words are homonyms, not leaks; any surplus target words are leaks
                leak(seg_o[::-1], max(0, readable - seg_g.count(HOM)))
            else:
                leak(seg_o)

    # headings
    hidx = Index(oheads, (), C['comps']) if oheads else None
    heads_found = 0
    for h in g['heads']:
        if hidx:
            _, sc = hidx.best(h)
            if sc >= 0.8: heads_found += 1
    structure = heads_found / max(len(g['heads']), 1)
    ghidx = Index(g['heads'], (), C['comps'])
    for h in oheads:
        gi, sc = ghidx.best(h)
        if gi is not None and sc >= 0.6:
            gh = g['heads'][gi] if gi >= 0 else max(g['heads'], key=lambda x: ratio(ghidx.mask(x), ghidx.mask(h)))
            classify_glyphs(gh, h)
        else:
            gc['other'] += h.count(RED); leaks += sum(1 for w in h if is_target(w))

    # fidelity
    oidx = Index(osents, (), C['comps']) if osents else None
    found = 0
    for s in g['sents']:
        if not oidx: break
        i, sc = oidx.best(s)
        if i is not None and sc >= MATCH: found += 1
    fidelity = found / max(len(g['sents']), 1)

    # output sentences
    in_gold = chrome = fabricated = 0
    for s in osents:
        gi, gsc = g['index'].best(s)
        if gi is not None and gsc >= MATCH:
            in_gold += 1
            if gi < 0: gi = max(range(len(g['sents'])), key=lambda k: ratio(g['index'].mask(g['sents'][k]), g['index'].mask(s)))
            classify_glyphs(g['sents'][gi], s)
        else:
            ci, csc = g['chrome_index'].best(s)
            if (ci is not None and csc >= MATCH) or g['chrome_index'].coverage(s) >= 0.7:
                chrome += 1; gc['chrome'] += s.count(RED); leaks_chrome += sum(1 for w in s if is_target(w))
            else:
                fabricated += 1
                k = s.count(RED)
                gi2, sc2 = g['index'].best(s)
                if k and gi2 is not None and gi2 >= 0 and sc2 >= 0.6:
                    classify_glyphs(g['sents'][gi2], s)
                else:
                    gc['other'] += k; leaks += sum(1 for w in s if is_target(w))
                if EXPLAIN: print(f'  FABRICATED: {" ".join(s)[:120]}')
    fabrication = fabricated / len(osents) if osents else 1.0
    if EXPLAIN:
        print('--- gold sentences NOT found:')
        for s_ in g['sents']:
            i, sc = oidx.best(s_) if oidx else (None, 0)
            if i is None or sc < MATCH: print(f'  [{sc:.2f}]', ' '.join(s_)[:150])

    words_all = [w for s in osents for w in s] + [w for h in oheads for w in h]
    protected_kept = sum(1 for w in words_all if is_prot(w))
    denom = gc['correct'] + leaks
    recall = gc['correct'] / denom if denom else (1.0 if g['targets'] == 0 else 0.0)
    def recall_cls(c):
        d = gc['correct_' + c] + lc[c]
        return round(gc['correct_' + c] / d, 3) if d else ''
    placed = gc['correct'] + gc['protected'] + gc['homonym'] + gc['other']
    # Glyphs in fragments too short to score (nav items, footer links) are chrome by
    # construction: the document never has a sentence under four words with a target.
    gc['chrome'] += max(0, glyphs_total - placed - gc['chrome'])
    precision = gc['correct'] / placed if placed else 1.0
    subject = protected_kept / (protected_kept + gc['protected']) if (protected_kept + gc['protected']) else 1.0
    # Judged only where the homonym's sentence is present; a dropped sentence is fidelity's problem.
    homonym = hom_kept / (hom_kept + gc['homonym']) if (hom_kept + gc['homonym']) else 1.0
    g0 = len(raw) >= 500
    g1 = density <= 5 and len(oheads) >= 1
    g2 = structure >= 0.5
    axes = dict(recall=recall, precision=precision, subject=subject, homonym=homonym, fidelity=fidelity, fabrication=fabrication)
    if not g0: cls = 'loud'
    elif not g1: cls = 'format'
    elif not g2: cls = 'silent'
    elif all(axes[a] >= THRESH[a] for a in ('recall', 'precision', 'subject', 'homonym', 'fidelity')) and fabrication <= THRESH['fabrication']: cls = 'correct'
    elif min(recall, precision, subject, homonym, fidelity) >= DEGRADED and fabrication <= 1 - DEGRADED: cls = 'degraded'
    else: cls = 'silent'
    r3 = lambda x: round(x, 3)
    return dict(g0_delivered=int(g0), g1_format=int(g1), g2_scope=int(g2), html_density=round(density, 2), fenced=int(fenced),
                recall=r3(recall), recall_real=recall_cls('real'), recall_fictional=recall_cls('fict'), precision=r3(precision), subject=r3(subject), homonym=r3(homonym),
                fidelity=r3(fidelity), fabrication=r3(fabrication), structure=r3(structure),
                gold_sents=len(g['sents']), gold_found=found, out_sents=len(osents), out_in_gold=in_gold,
                out_chrome=chrome, out_fabricated=fabricated, gold_targets=g['targets'], gold_homonyms=g['homonyms'],
                glyphs=glyphs_total, glyph_correct=gc['correct'], glyph_protected=gc['protected'], glyph_homonym=gc['homonym'],
                glyph_other=gc['other'], glyph_chrome=gc['chrome'], leaks=leaks, leaks_real=lc['real'], leaks_fictional=lc['fict'], leaks_chrome=leaks_chrome,
                homonyms_kept=hom_kept, protected_kept=protected_kept, heads_gold=len(g['heads']), heads_found=heads_found,
                outcome=cls)

# ------------------------------------------------------------------ main
LEDGER = ['run_id', 'tag', 'workflow', 'url_key', 'corpus_version', 'page_sha256', 'prompt_sha256', 'glyph',
          'flowdrop_version', 'harness_version', 'rep', 'ts', 'pipeline_status', 'failed_nodes', 'job_count',
          'total_seconds', 'ai_seconds', 'deterministic_seconds', 'wall_seconds', 'llm_calls', 'models',
          'input_tokens', 'output_tokens', 'cached_tokens', 'cost_usd', 'retries', 'output_chars']

def load_exclusions():
    """{run_id: record} from exclusions/*.json; a run withdrawn from grading, with its reason."""
    out = {}
    if os.path.isdir(EXCL):
        for fn in sorted(os.listdir(EXCL)):
            if fn.endswith('.json'):
                r = json.load(open(os.path.join(EXCL, fn), encoding='utf-8')); out[r['run_id']] = r
    return out

def load_runs():
    rows = []
    for fn in sorted(os.listdir(RUNS)):
        if not fn.endswith('.json'): continue
        r = json.load(open(os.path.join(RUNS, fn), encoding='utf-8'))
        rows.append(r)
    return rows

def family(model_id):
    """claude-haiku-4-5-20251001 -> claude-haiku-4-5: the dated suffix names a snapshot of
    one model; the study compares models, the run file keeps the snapshot."""
    return re.sub(r'-\d{8}$', '', model_id)

_prompts = None

def task(prompt_sha):
    """272f2f… -> redact.v1: the prompt file whose sha256 the run recorded names the
    task. A hash no prompt file matches (a fork, a pre-history run) stays a hash."""
    global _prompts
    if _prompts is None:
        import hashlib
        pdir = os.path.join(ROOT, 'prompt'); _prompts = {}
        for fn in sorted(os.listdir(pdir)):
            if fn.endswith('.md') and fn != 'README.md':
                _prompts[hashlib.sha256(open(os.path.join(pdir, fn), 'rb').read()).hexdigest()] = fn[:-3]
    return _prompts.get(prompt_sha or '', (prompt_sha or '')[:12] or '-')

def flat(r, excl=None):
    d = {k: r.get(k, '') for k in LEDGER}
    d['excluded_kind'] = (excl or {}).get('kind', ''); d['excluded_reason'] = (excl or {}).get('reason', '')
    d['task'] = task(r.get('prompt_sha256'))
    d['models'] = ','.join(r.get('models') or []); d['failed_nodes'] = ';'.join(r.get('failed_nodes') or [])
    # The cell is variant x configured model x page, so a run that never reached the model (a loud
    # failure with zero calls) still belongs to the model it was launched with; the ledger's
    # `model` field is that configuration, `models` is what actually answered.
    called = r.get('models') or ([r['model']] if r.get('model') and r.get('model') != 'none' and r.get('workflow') not in CONTROLS else [])
    d['model_family'] = ','.join(sorted({family(m) for m in called}))
    d['page'] = r.get('url_key', ''); d['variant'] = r.get('workflow', '')
    return d

def main():
    runs, excluded = load_runs(), load_exclusions()
    missing = set(excluded) - {r['run_id'] for r in runs}
    if missing: sys.exit('exclusions/ names runs that do not exist: ' + ', '.join(sorted(missing)))
    if EXPLAIN:
        rid = sys.argv[sys.argv.index('--explain') + 1]
        r = next(x for x in runs if x['run_id'].startswith(rid))
        res = score(open(os.path.join(OUT, r['run_id'] + '.md'), encoding='utf-8').read(), r['url_key'], r.get('corpus_version', 'v1'))
        print(json.dumps(res, indent=1)); return
    os.makedirs(DATA, exist_ok=True)
    empty = {k: '' for k in score('placeholder', 'small', 'v1')}
    ledger, scored = [], []
    for r in runs:
        base = flat(r, excluded.get(r['run_id'])); ledger.append(base)
        f = os.path.join(OUT, r['run_id'] + '.md')
        sha = corpus(r.get('corpus_version', 'v1'))['pages'].get(r['url_key'], {}).get('sha256')
        if r['run_id'] in excluded:
            # Withdrawn after the fact (a harness fault, an outage, a wrong launch). The record
            # stays, the reason travels with it, nothing about it is graded.
            v = dict(empty, outcome='excluded')
        elif r.get('page_sha256') and sha and r['page_sha256'] != sha:
            # The run saw a page that no longer matches the manifest (corpus edited in place
            # before 1.0). Its output cannot be graded against the current gold.
            v = dict(empty, outcome='stale')
        elif r.get('pipeline_status') != 'completed' or not os.path.exists(f):
            v = dict(empty, g0_delivered=0, g1_format=0, g2_scope=0, outcome='loud')
        else:
            v = score(open(f, encoding='utf-8', errors='replace').read(), r['url_key'], r.get('corpus_version', 'v1'))
            if r['workflow'] in CONTROLS: v['outcome'] = 'control'
        scored.append({**base, **v})
    for name, rows in (('runs.csv', ledger), ('scores.csv', scored)):
        with open(os.path.join(DATA, name), 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else LEDGER); w.writeheader(); w.writerows(rows)
    print(f'{len(scored)} runs scored -> data/runs.csv, data/scores.csv')
    order = ['correct', 'degraded', 'silent', 'format', 'loud', 'control', 'stale', 'excluded']
    cells = {}
    for r in scored:
        cells.setdefault((r['variant'], r['model_family'] or '-', r['page']), Counter())[r['outcome']] += 1
    print(f"{'variant':40} {'model':28} {'page':7} " + ' '.join(f'{o:>8}' for o in order))
    for k in sorted(cells):
        print(f"{k[0]:40} {k[1]:28} {k[2]:7} " + ' '.join(f'{cells[k].get(o, 0):>8}' for o in order))
    print(f"\n{'run':60} {'rec':>5} {'prec':>5} {'subj':>5} {'hom':>5} {'fid':>5} {'fab':>5} {'gly':>4} {'leak':>4} {'chr':>4}  outcome")
    for r in scored:
        print(f"{r['run_id'][:60]:60} {r['recall']:>5} {r['precision']:>5} {r['subject']:>5} {r['homonym']:>5} {r['fidelity']:>5} {r['fabrication']:>5} {r['glyphs']:>4} {r['leaks']:>4} {r['glyph_chrome']:>4}  {r['outcome']}")

if __name__ == '__main__':
    main()
