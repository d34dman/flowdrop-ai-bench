#!/usr/bin/env python3
"""Write a study file. Standard library only.

    python3 scoring/study.py --id frontier-2026-09 --title "Frontier models, September 2026" \
        --blurb "Why these runs belong together, in a sentence or two." \
        --model claude-sonnet-5 --model claude-opus-5 --corpus v1
    python3 scoring/study.py --list

A study is a named, frozen scope: the set of filter values every page of the site applies
before the on-page filters, so a view can be shared as ?study=<id> instead of a long
query string. It lives in studies/<id>.json, next to the runs, and is contributed the same
way: a pull request that adds the file and nothing else passes the data-only gate.

Scope flags repeat: --model, --benchmark, --page, --tag, --corpus. Each is a filter id
from site/filters.json and every value must be one some run in the dataset has; the gate
(scoring/check.py) refuses a study naming a model nobody has run. Studies are append-only
like runs: a revised scope is a new dated id, so shared links keep their meaning.
"""
import argparse, getpass, json, os, re, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIES = os.path.join(ROOT, 'studies')
SCOPE_KEYS = ('model', 'benchmark', 'page', 'tag', 'corpus')
STUDY_ID = re.compile(r'^[a-z][a-z0-9-]{2,60}$')


def load():
    out = {}
    if os.path.isdir(STUDIES):
        for fn in sorted(os.listdir(STUDIES)):
            if fn.endswith('.json'): out[fn[:-5]] = json.load(open(os.path.join(STUDIES, fn), encoding='utf-8'))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='print every study')
    ap.add_argument('--id', help='slug, [a-z][a-z0-9-]{2,60}; date it (frontier-2026-09) so a later revision gets a new id')
    ap.add_argument('--title', help='at most 80 characters, shown in the study selector')
    ap.add_argument('--blurb', help='one or two sentences: what the study compares and why')
    ap.add_argument('--by', default=getpass.getuser(), help='who files it (default: your login)')
    for k in SCOPE_KEYS: ap.add_argument(f'--{k}', action='append', metavar='VALUE', help=f'a {k} value; repeat for several')
    a = ap.parse_args(argv)
    if a.list:
        for sid, s in load().items():
            print(f'{sid:32} {s["title"]}\n{"":32} ' + '; '.join(f'{k}: {", ".join(v)}' for k, v in s['scope'].items()))
        return 0
    if not (a.id and a.title and a.blurb): ap.error('--id, --title and --blurb are required (or --list)')
    if not STUDY_ID.match(a.id) or a.id == 'all': ap.error(f'id {a.id!r} is not a slug [a-z][a-z0-9-]{{2,60}} (and `all` is reserved)')
    scope = {k: getattr(a, k) for k in SCOPE_KEYS if getattr(a, k)}
    if not scope: ap.error('a study needs at least one scope flag (--model, --benchmark, --page, --tag, --corpus)')
    path = os.path.join(STUDIES, a.id + '.json')
    if os.path.exists(path): sys.exit(f'{os.path.relpath(path, ROOT)} exists; studies are append-only, pick a new id')
    rec = {'id': a.id, 'title': a.title, 'blurb': a.blurb, 'scope': scope, 'by': a.by,
           'ts': datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    os.makedirs(STUDIES, exist_ok=True)
    json.dump(rec, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(path, 'a').write('\n')
    print(f'wrote {os.path.relpath(path, ROOT)}; check it with: python3 scoring/check.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
