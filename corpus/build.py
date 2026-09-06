#!/usr/bin/env python3
"""Builds a corpus version: src/*.md + template.html -> *.html, gold/*.md, manifest.json.

Standard library only. Run from anywhere:  python3 corpus/build.py [v1]

Source pages are Markdown with two kinds of inline marker, stripped from every output:
  [[h:Name]]   a homonym: this occurrence of a competitor's name is NOT the product
               (a person, a place, a unit). Must not be redacted. Listed in the manifest.
  [[t:Name]]   an extra target the automatic scan would miss (e.g. "Lumen" for "Lumen CMS").
Every other occurrence of a competitor name in the body is a target by construction.
Protected names are found by scanning. Competitor names inside the chrome (template and
per-page src/<page>.chrome.html) are counted per name and listed as chrome, so a glyph
placed there can be told apart from one placed on the document.
"""
import hashlib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VERSION = sys.argv[1] if len(sys.argv) > 1 else 'v1'
CORPUS = os.path.join(HERE, VERSION)
BASE_URL = f'https://d34dman.github.io/flowdrop-ai-bench/corpus/{VERSION}/'

def read_prompt():
    p = os.path.join(ROOT, 'prompt', 'redact.v1.md')
    txt = open(p, encoding='utf-8').read()
    fm = txt.split('---')[1]
    meta = {}
    for line in fm.strip().splitlines():
        k, v = line.split(':', 1); v = v.strip()
        if v.startswith('['): v = [x.strip() for x in v.strip('[]').split(',')]
        meta[k.strip()] = v.strip('"') if isinstance(v, str) else v
    return meta, hashlib.sha256(txt.encode()).hexdigest()

PROTECTED = ['Drupal', 'PHP', 'Symfony', 'Twig', 'MySQL', 'PostgreSQL', 'SQLite', 'Composer',
             'GitLab', 'Linux', 'Apache', 'Nginx', 'JSON:API', 'GraphQL', 'React', 'Node.js',
             'Redis', 'Docker', 'Kubernetes', 'Markdown']

MARK = re.compile(r'\[\[(h|t):([^\]]+)\]\]')

# --- minimal Markdown -> HTML -------------------------------------------------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*([^*]+)\*(?!\w)', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s

def md_to_html(md):
    out, i, lines = [], 0, md.split('\n')
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        m = re.match(r'^(#{1,6}) (.*)', l)
        if m:
            n = len(m.group(1)); out.append(f'<h{n}>{inline(m.group(2))}</h{n}>'); i += 1; continue
        if l.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            head, body = rows[0], [r for r in rows[2:]]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table>')
            continue
        if re.match(r'^[-*] ', l) or re.match(r'^\d+\. ', l):
            ordered = bool(re.match(r'^\d+\. ', l)); items = []
            while i < len(lines) and (re.match(r'^[-*] ', lines[i]) or re.match(r'^\d+\. ', lines[i])):
                items.append(re.sub(r'^([-*]|\d+\.) ', '', lines[i])); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if l.startswith('> '):
            q = []
            while i < len(lines) and lines[i].startswith('> '): q.append(lines[i][2:]); i += 1
            out.append('<blockquote><p>' + inline(' '.join(q)) + '</p></blockquote>'); continue
        p = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6} |[-*] |\d+\. |> |\|)', lines[i]):
            p.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(p)) + '</p>')
    return '\n'.join(out)

# --- positions ----------------------------------------------------------------
def positions(text, name, exclude=()):
    """(line, col) of every whole-word occurrence of name, 1-based, skipping exclude."""
    res = []
    for ln, line in enumerate(text.split('\n'), 1):
        for m in re.finditer(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', line):
            if (ln, m.start() + 1) not in exclude: res.append({'name': name, 'line': ln, 'col': m.start() + 1})
    return res

def build_page(page, meta):
    src = open(os.path.join(CORPUS, 'src', f'{page}.md'), encoding='utf-8').read()
    # Resolve markers: record positions in the stripped (gold) text.
    gold, homonyms, extra, off_line, cursor = '', [], [], {}, 0
    out_lines = []
    for ln, line in enumerate(src.split('\n'), 1):
        clean, pos = '', 0
        for m in MARK.finditer(line):
            clean += line[pos:m.start()]
            col = len(clean) + 1
            (homonyms if m.group(1) == 'h' else extra).append({'name': m.group(2), 'line': ln, 'col': col})
            clean += m.group(2); pos = m.end()
        clean += line[pos:]; out_lines.append(clean)
    gold = '\n'.join(out_lines).rstrip() + '\n'
    comps = meta['competitors']
    hom_pos = {(h['line'], h['col']) for h in homonyms}
    targets = []
    for c in comps:
        targets += positions(gold, c, exclude=hom_pos)
    # A bare-word marker like [[t:Lumen]] may sit at a position also matched by the
    # full name scan; de-duplicate on (line, col).
    seen = {(t['line'], t['col']) for t in targets}
    for e in extra:
        if (e['line'], e['col']) not in seen: targets.append(e)
    targets.sort(key=lambda t: (t['line'], t['col']))
    protected = []
    for p in PROTECTED: protected += positions(gold, p)
    protected.sort(key=lambda t: (t['line'], t['col']))
    title = re.match(r'^# (.*)', gold).group(1)
    first_p = next(l for l in gold.split('\n')[1:] if l.strip() and not l.startswith('#'))
    chrome_path = os.path.join(CORPUS, 'src', f'{page}.chrome.html')
    page_chrome = open(chrome_path, encoding='utf-8').read() if os.path.exists(chrome_path) else ''
    tpl = open(os.path.join(CORPUS, 'template.html'), encoding='utf-8').read()
    page_html = (tpl.replace('{{title}}', html.escape(title)).replace('{{description}}', html.escape(first_p[:150]))
                 .replace('{{body}}', md_to_html(gold)).replace('{{page_chrome}}', page_chrome).replace('{{version}}', VERSION))
    chrome_text = re.sub(r'\{\{body\}\}', '', tpl) + page_chrome
    chrome = {c: len(re.findall(r'(?<![\w-])' + re.escape(c) + r'(?![\w-])', chrome_text)) for c in comps}
    chrome = {k: v for k, v in chrome.items() if v}
    os.makedirs(os.path.join(CORPUS, 'gold'), exist_ok=True)
    open(os.path.join(CORPUS, 'gold', f'{page}.md'), 'w', encoding='utf-8').write(gold)
    open(os.path.join(CORPUS, f'{page}.html'), 'w', encoding='utf-8').write(page_html)
    return {
        'html': f'{page}.html', 'url': BASE_URL + f'{page}.html', 'gold': f'gold/{page}.md',
        'sha256': hashlib.sha256(page_html.encode()).hexdigest(),
        'gold_sha256': hashlib.sha256(gold.encode()).hexdigest(),
        'html_bytes': len(page_html.encode()), 'gold_bytes': len(gold.encode()),
        'headings': len(re.findall(r'^#{1,6} ', gold, re.M)),
        'tables': gold.count('|---'),
        'targets': targets, 'homonyms': homonyms, 'protected': protected, 'chrome': chrome,
    }

def main():
    meta, prompt_sha = read_prompt()
    pages = {p: build_page(p, meta) for p in ('small', 'medium', 'large')}
    manifest = {
        'version': VERSION, 'base_url': BASE_URL, 'glyph': meta['glyph'], 'subject': meta['subject'],
        'competitors': meta['competitors'], 'real_names': meta.get('real', []), 'protected_names': PROTECTED,
        'prompt': 'prompt/redact.v1.md', 'prompt_sha256': prompt_sha,
        'pages': pages,
    }
    json.dump(manifest, open(os.path.join(CORPUS, 'manifest.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"{'page':7} {'html':>7} {'gold':>7} {'head':>4} {'tgt':>3} {'hom':>3} {'prot':>4}  chrome")
    for p, d in pages.items():
        print(f"{p:7} {d['html_bytes']:7} {d['gold_bytes']:7} {d['headings']:4} {len(d['targets']):3} {len(d['homonyms']):3} {len(d['protected']):4}  {d['chrome']}")

if __name__ == '__main__':
    main()
