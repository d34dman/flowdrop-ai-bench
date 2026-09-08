#!/usr/bin/env python3
"""Dataset gate for FlowDrop AI Bench. Standard library only. No network.

    python3 scoring/check.py                       # full scan of the tree
    python3 scoring/check.py --base origin/main    # + pull-request rules against that ref
    python3 scoring/check.py --base origin/main --allow-code
    python3 scoring/check.py --root <dir>          # scan another checkout

Exit 0 when clean, 1 when anything fails. Warnings never fail the run. When run under
GitHub Actions every finding is emitted as a workflow annotation and a summary is appended
to the job summary.

The dataset is four folders of plain data files and nothing else:

    runs/<run_id>.json   outputs/<run_id>.md   traces/<run_id>.json.gz   exclusions/<run_id>.json

Full scan, every file in those folders, every time:

  shape      the name is <run_id> plus exactly that extension, <run_id> matches RUN_ID, no
             sub-folders, no dotfiles (.gitkeep excepted), regular file, mode 100644 in git
             (no symlink, no executable bit), size under the per-folder cap
  text       UTF-8, no NUL byte, no secret-looking string (API keys, tokens, private keys,
             KEY=value assignments); outputs additionally carry no active content
             (<script, <iframe, <object, <embed, javascript:, on*= handlers; page chrome such as <form> is data)
  runs       one JSON object with the required keys and types; run_id, workflow, url_key
             and rep agree with the filename; corpus_version is a folder under corpus/ and
             url is that corpus's published URL for url_key; hashes are hex; counts >= 0
  traces     valid gzip that inflates to under TRACE_INFLATED_MAX bytes (zip-bomb guard)
             and to one JSON object whose run_id is the filename; its run exists
  outputs    its run exists; a completed run that recorded output_chars > 0 has an output;
             a completed run without an output recorded no output (output_chars null/0)
  exclusions its run exists, kind is known, reason is a sentence, by and ts are present

Pull-request rules (with --base):

  append-only  no file in the four folders is modified, renamed, deleted or type-changed
  scope        every changed path is inside the four folders; anything else (runner/,
               scoring/, site/, .github/, ...) fails unless --allow-code, which CI grants to
               the `code-change` label or a repository owner/member. Data PRs from anyone
               are then reviewed by machine; code PRs are reviewed by a person.
"""
import argparse, io, json, os, re, subprocess, sys, zlib

RUN_ID = re.compile(r'^bench_\d+_[a-z0-9_]+__(small|medium|large)__r\d+__\d{10}__[A-Za-z0-9._-]{1,80}__[0-9a-f]{6}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
DATA_DIRS = {                      # folder: (extension, max bytes per file)
    'runs': ('.json', 256 * 1024),
    'outputs': ('.md', 4 * 1024 * 1024),
    'traces': ('.json.gz', 3 * 1024 * 1024),
    'exclusions': ('.json', 64 * 1024),
}
TRACE_INFLATED_MAX = 48 * 1024 * 1024
KEEP = {'.gitkeep'}
STATUSES = ('completed', 'failed', 'running')
KINDS = ('harness', 'provider', 'operator', 'duplicate')

# Required keys of runs/<id>.json and the types allowed. None means nullable.
RUN_SCHEMA = {
    'run_id': (str,), 'workflow': (str,), 'url_key': (str,), 'url': (str,), 'corpus_version': (str,),
    'page_sha256': (str,), 'prompt_sha256': (str,), 'glyph': (str,), 'flowdrop_version': (str,),
    'harness_version': (str,), 'model': (str,), 'rep': (int,), 'tag': (str,), 'ts': (str,),
    'launch_status': (str,), 'pipeline_status': (str,), 'failed_nodes': (list,), 'job_count': (int,),
    'llm_calls': (int,), 'models': (list,), 'input_tokens': (int,), 'output_tokens': (int,),
    'cached_tokens': (int,), 'cost_usd': (int, float), 'retries': (int,),
    'output_chars': (int, type(None)), 'nodes': (list,),
}
NON_NEGATIVE = ('rep', 'job_count', 'llm_calls', 'input_tokens', 'output_tokens', 'cached_tokens', 'cost_usd', 'retries')

# Secret-looking strings. Any hit fails; the corpus and the prompt contain none of these.
SECRETS = [
    (re.compile(rb'sk-ant-[A-Za-z0-9_-]{8,}'), 'Anthropic API key'),
    (re.compile(rb'sk-or-v?1?-?[A-Za-z0-9_-]{16,}'), 'OpenRouter API key'),
    (re.compile(rb'sk-proj-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9]{32,}'), 'OpenAI-style API key'),
    (re.compile(rb'AIza[0-9A-Za-z_-]{35}'), 'Google API key'),
    (re.compile(rb'AKIA[0-9A-Z]{16}'), 'AWS access key id'),
    (re.compile(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}'), 'GitHub token'),
    (re.compile(rb'xox[abprs]-[A-Za-z0-9-]{10,}'), 'Slack token'),
    (re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private key block'),
    (re.compile(rb'(?i)\b(?:authorization|x-api-key)\s*[:=]\s*["\']?(?:bearer\s+)?[A-Za-z0-9._~+/=-]{16,}'), 'authorization header with a credential'),
    (re.compile(rb'(?i)\b[A-Z0-9_]*(?:API_?KEY|SECRET|TOKEN|PASSWORD)\s*=\s*["\']?[A-Za-z0-9._~+/=-]{12,}'), 'KEY=value credential assignment'),
]
ACTIVE = [
    (re.compile(rb'(?i)<\s*(script|iframe|object|embed)\b'), 'active HTML element'),
    (re.compile(rb'(?i)javascript\s*:'), 'javascript: URL'),
    (re.compile(rb'(?i)\bon[a-z]{2,20}\s*='), 'inline event handler'),
]


class Report:
    def __init__(self):
        self.errors, self.warnings, self.counts = [], [], {}
        self.gh = bool(os.environ.get('GITHUB_ACTIONS'))

    def error(self, path, msg): self.errors.append((path, msg)); self._emit('error', path, msg)
    def warn(self, path, msg): self.warnings.append((path, msg)); self._emit('warning', path, msg)

    def _emit(self, level, path, msg):
        if self.gh: print(f'::{level} file={path}::{msg}' if path else f'::{level}::{msg}')
        else: print(f'{level.upper():7} {path + ": " if path else ""}{msg}')

    def summary(self, base, allow_code):
        lines = ['## Dataset gate', '']
        lines.append(f'{"**Failed**" if self.errors else "Passed"}: {len(self.errors)} error(s), {len(self.warnings)} warning(s).')
        lines.append('')
        lines += [f'- {k}: {v}' for k, v in self.counts.items()]
        if base: lines.append(f'- pull-request rules against `{base}`' + (' (code changes allowed)' if allow_code else ''))
        if self.errors:
            lines += ['', '| file | problem |', '|---|---|'] + [f'| `{p}` | {m} |' for p, m in self.errors[:200]]
            if len(self.errors) > 200: lines.append(f'| ... | {len(self.errors) - 200} more |')
        text = '\n'.join(lines) + '\n'
        gs = os.environ.get('GITHUB_STEP_SUMMARY')
        if gs:
            with open(gs, 'a', encoding='utf-8') as f: f.write(text)
        else:
            print('\n' + text)


# ------------------------------------------------------------------ enumeration

def git(root, *args, check=True):
    p = subprocess.run(['git', '-C', root, *args], capture_output=True)
    if check and p.returncode: raise RuntimeError(p.stderr.decode(errors='replace').strip() or f'git {args[0]} failed')
    return p.stdout


def in_git(root):
    try: return git(root, 'rev-parse', '--is-inside-work-tree').strip() == b'true'
    except Exception: return False


def tracked_modes(root):
    """{relpath: mode} for every path git tracks under the data folders."""
    out = {}
    raw = git(root, 'ls-files', '-s', '-z', '--', *DATA_DIRS)
    for rec in raw.split(b'\0'):
        if not rec: continue
        meta, path = rec.split(b'\t', 1)
        out[path.decode('utf-8', 'surrogateescape')] = meta.split()[0].decode()
    return out


def walk(root):
    """Every path (relative) present on disk under the data folders, including sub-folders."""
    for d in DATA_DIRS:
        top = os.path.join(root, d)
        if not os.path.isdir(top): continue
        for dp, dns, fns in os.walk(top):
            rel = os.path.relpath(dp, root)
            for name in dns: yield os.path.join(rel, name), 'dir'
            for name in fns: yield os.path.join(rel, name), 'file'


# ------------------------------------------------------------------ per-file checks

def scan_bytes(rep, path, data, active):
    if b'\0' in data: rep.error(path, 'contains a NUL byte; not a text file')
    try: data.decode('utf-8')
    except UnicodeDecodeError as e: rep.error(path, f'not valid UTF-8 ({e.reason} at byte {e.start})')
    for rx, what in SECRETS:
        m = rx.search(data)
        if m: rep.error(path, f'looks like a {what} at byte {m.start()}: {m.group(0)[:12].decode("ascii", "replace")}...')
    if active:
        for rx, what in ACTIVE:
            m = rx.search(data)
            if m: rep.error(path, f'{what} at byte {m.start()}: {m.group(0)[:40].decode("ascii", "replace")!r}')


def inflate(path, limit):
    """gzip -> bytes, refusing to produce more than limit bytes."""
    out, d = io.BytesIO(), zlib.decompressobj(16 + zlib.MAX_WBITS)
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1 << 16)
            if not chunk: break
            out.write(d.decompress(chunk, limit + 1 - out.tell()))
            if out.tell() > limit: raise ValueError(f'inflates past {limit} bytes')
            if d.unconsumed_tail:  # limit reached exactly
                raise ValueError(f'inflates past {limit} bytes')
    if not d.eof: raise ValueError('truncated or not a gzip stream')
    return out.getvalue()


def load_json_object(rep, path, data):
    try: obj = json.loads(data.decode('utf-8'))
    except Exception as e: rep.error(path, f'not valid JSON ({str(e)[:80]})'); return None
    if not isinstance(obj, dict): rep.error(path, 'JSON is not an object'); return None
    return obj


def check_run(rep, path, run_id, r, corpora):
    for k, types in RUN_SCHEMA.items():
        if k not in r: rep.error(path, f'missing key {k!r}'); continue
        v = r[k]
        if isinstance(v, bool) or not isinstance(v, types):
            rep.error(path, f'{k!r} is {type(v).__name__}, expected {"/".join(t.__name__ for t in types)}')
    if rep.errors and rep.errors[-1][0] == path: return
    if r['run_id'] != run_id: rep.error(path, f"run_id {r['run_id']!r} is not the filename")
    wf, key, rep_s = run_id.split('__')[:3]
    if r['workflow'] != wf: rep.error(path, f"workflow {r['workflow']!r} disagrees with filename ({wf})")
    if r['url_key'] != key: rep.error(path, f"url_key {r['url_key']!r} disagrees with filename ({key})")
    if r['rep'] != int(rep_s[1:]): rep.error(path, f"rep {r['rep']} disagrees with filename ({rep_s})")
    for k in ('page_sha256', 'prompt_sha256'):
        if not HEX64.match(r[k]): rep.error(path, f'{k} is not a sha256 hex digest')
    for k in NON_NEGATIVE:
        if r[k] < 0: rep.error(path, f'{k} is negative')
    if r['rep'] < 1: rep.error(path, 'rep is below 1')
    if r['output_chars'] is not None and r['output_chars'] < 0: rep.error(path, 'output_chars is negative')
    if r['pipeline_status'] not in STATUSES: rep.error(path, f"pipeline_status {r['pipeline_status']!r} not in {STATUSES}")
    if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', r['ts']): rep.error(path, f"ts {r['ts']!r} is not ISO 8601")
    m = corpora.get(r['corpus_version'])
    if m is None: rep.error(path, f"corpus_version {r['corpus_version']!r} has no folder under corpus/"); return
    page = m['pages'].get(r['url_key'])
    if page is None: rep.error(path, f"url_key {r['url_key']!r} is not a page of corpus {r['corpus_version']}")
    elif r['url'] != page['url']: rep.error(path, f"url {r['url']!r} is not the corpus page {page['url']}")
    elif r['page_sha256'] != page['sha256']: rep.warn(path, 'page_sha256 differs from the current manifest; the scorer will class this run stale')
    if r['prompt_sha256'] != m.get('prompt_sha256'): rep.warn(path, 'prompt_sha256 is not the current prompt; the scorer will class this run by its recorded task')


def check_exclusion(rep, path, run_id, r, run_ids):
    for k in ('run_id', 'kind', 'reason', 'by', 'ts'):
        if not isinstance(r.get(k), str) or not r[k].strip(): rep.error(path, f'missing or empty {k!r}')
    if rep.errors and rep.errors[-1][0] == path: return
    if r['run_id'] != run_id: rep.error(path, 'file is not named after its run_id')
    if r['kind'] not in KINDS: rep.error(path, f"unknown kind {r['kind']!r}; one of {KINDS}")
    if len(r['reason']) < 20: rep.error(path, 'reason too short to say what went wrong and what was done')
    if run_id not in run_ids: rep.error(path, f'no such run runs/{run_id}.json')


# ------------------------------------------------------------------ full scan

def load_corpora(rep, root):
    out = {}
    base = os.path.join(root, 'corpus')
    for v in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        mf = os.path.join(base, v, 'manifest.json')
        if os.path.isfile(mf):
            try: out[v] = json.load(open(mf, encoding='utf-8'))
            except Exception as e: rep.error(os.path.relpath(mf, root), f'unreadable manifest: {e}')
    if not out: rep.error('corpus', 'no corpus manifest found; runs cannot be verified')
    return out


def full_scan(rep, root):
    corpora = load_corpora(rep, root)
    modes = tracked_modes(root) if in_git(root) else None
    files = {d: {} for d in DATA_DIRS}          # dir -> run_id -> relpath
    seen = set()
    for rel, kind in walk(root):
        seen.add(rel)
        d, _, rest = rel.partition(os.sep)
        ext, cap = DATA_DIRS[d]
        if kind == 'dir': rep.error(rel, 'sub-folders are not allowed in the dataset'); continue
        if os.sep in rest: continue                       # reported through its folder
        if rest in KEEP: continue
        if rest.startswith('.'): rep.error(rel, 'dotfiles are not allowed in the dataset'); continue
        full = os.path.join(root, rel)
        if os.path.islink(full): rep.error(rel, 'symlink; only regular files are allowed'); continue
        if not os.path.isfile(full): rep.error(rel, 'not a regular file'); continue
        if modes is not None:
            mode = modes.get(rel)
            if mode is None: rep.warn(rel, 'not tracked by git; ignored by CI until committed')
            elif mode != '100644': rep.error(rel, f'git mode {mode}; data files must be 100644 (no executable bit, no symlink)')
        if not rest.endswith(ext): rep.error(rel, f'only {ext} files belong in {d}/'); continue
        run_id = rest[:-len(ext)]
        if not RUN_ID.match(run_id): rep.error(rel, 'filename is not <run_id>' + ext + ' with a well-formed run id'); continue
        size = os.path.getsize(full)
        if size > cap: rep.error(rel, f'{size} bytes exceeds the {cap} byte cap for {d}/'); continue
        if size == 0: rep.error(rel, 'empty file'); continue
        files[d][run_id] = rel
    if modes:
        for rel in modes:
            if rel not in seen: rep.error(rel, 'tracked by git but missing from the working tree')

    runs = {}
    for run_id, rel in sorted(files['runs'].items()):
        data = open(os.path.join(root, rel), 'rb').read()
        scan_bytes(rep, rel, data, active=False)
        r = load_json_object(rep, rel, data)
        if r is not None:
            check_run(rep, rel, run_id, r, corpora); runs[run_id] = r
    for run_id, rel in sorted(files['outputs'].items()):
        data = open(os.path.join(root, rel), 'rb').read()
        scan_bytes(rep, rel, data, active=True)
        r = runs.get(run_id)
        if r is None: rep.error(rel, f'no run for this output (runs/{run_id}.json is missing)')
        elif isinstance(r.get('output_chars'), int) and r['output_chars'] > 0:
            n = len(data.decode('utf-8', 'replace'))
            if abs(n - r['output_chars']) > max(64, r['output_chars'] // 20):
                rep.warn(rel, f'output is {n} chars, run recorded output_chars {r["output_chars"]}')
    for run_id, r in sorted(runs.items()):
        rel = files['runs'][run_id]
        has_out = run_id in files['outputs']
        if r.get('pipeline_status') == 'completed':
            if r.get('output_chars') and not has_out: rep.error(rel, f'completed run recorded {r["output_chars"]} output chars but outputs/{run_id}.md is missing')
            if not r.get('output_chars') and not has_out: rep.warn(rel, 'completed run produced no output; the scorer classes it loud')
        elif has_out: rep.warn(rel, f"{r.get('pipeline_status')} run has an output file; it will be graded")
    for run_id, rel in sorted(files['traces'].items()):
        try: data = inflate(os.path.join(root, rel), TRACE_INFLATED_MAX)
        except Exception as e: rep.error(rel, f'bad gzip: {e}'); continue
        scan_bytes(rep, rel, data, active=False)
        t = load_json_object(rep, rel, data)
        if t is None: continue
        if t.get('run_id') != run_id: rep.error(rel, f"trace run_id {t.get('run_id')!r} is not the filename")
        if run_id not in runs: rep.error(rel, f'no run for this trace (runs/{run_id}.json is missing)')
    for run_id, rel in sorted(files['exclusions'].items()):
        data = open(os.path.join(root, rel), 'rb').read()
        scan_bytes(rep, rel, data, active=False)
        r = load_json_object(rep, rel, data)
        if r is not None: check_exclusion(rep, rel, run_id, r, runs)
    rep.counts.update({f'{d}/': len(v) for d, v in files.items()})


# ------------------------------------------------------------------ pull-request rules

def pr_rules(rep, root, base, allow_code):
    try: raw = git(root, 'diff', '--name-status', '-z', '-M', f'{base}...HEAD')
    except RuntimeError as e: rep.error('', f'cannot diff against {base}: {e}'); return
    items = raw.split(b'\0')
    i, added, outside, broken = 0, 0, [], []
    while i < len(items) and items[i]:
        st = items[i].decode(); i += 1
        path = items[i].decode('utf-8', 'surrogateescape'); i += 1
        if st[0] in 'RC': path2 = items[i].decode('utf-8', 'surrogateescape'); i += 1
        else: path2 = None
        for p in (path, path2):
            if p is None: continue
            top = p.split('/', 1)[0]
            if top in DATA_DIRS:
                if st[0] == 'A': added += 1
                else: broken.append((p, st))
            else: outside.append((p, st))
    for p, st in broken:
        rep.error(p, f'existing dataset files are never modified, renamed or deleted (status {st}); withdraw a run through exclusions/ instead')
    if outside:
        msg = f'{len(outside)} changed path(s) outside the dataset folders'
        if allow_code: rep.warn('', msg + '; allowed for this pull request, a person reviews them')
        else:
            rep.error('', msg + '; a data pull request touches only runs/, outputs/, traces/ and exclusions/. A maintainer adds the `code-change` label after reviewing the code.')
            for p, st in outside[:100]: rep.error(p, f'outside the dataset ({st})')
    rep.counts['added dataset files'] = added
    rep.counts['changed paths outside the dataset'] = len(outside)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), help='repository root to scan')
    ap.add_argument('--base', help='git ref of the merge base; enables the pull-request rules')
    ap.add_argument('--allow-code', action='store_true', help='let changed paths outside the dataset pass (label `code-change`)')
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    rep = Report()
    full_scan(rep, root)
    if a.base: pr_rules(rep, root, a.base, a.allow_code)
    rep.summary(a.base, a.allow_code)
    print(f'{"FAIL" if rep.errors else "ok"}: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)')
    return 1 if rep.errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
