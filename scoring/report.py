#!/usr/bin/env python3
"""Markdown report of how the runs a branch adds were scored. Standard library only.

    python3 scoring/score.py && python3 scoring/report.py --base origin/main

Lists the runs added since the base ref (git diff, runs/ folder) and prints, per model, the
outcome counts the scorer gave them, then one line per run. CI appends it to the job summary
of every pull request, so a contributor sees their scores without building the site.
"""
import argparse, collections, csv, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ['correct', 'degraded', 'silent', 'format', 'loud', 'control', 'stale', 'excluded']


def added_runs(base):
    raw = subprocess.check_output(['git', '-C', ROOT, 'diff', '--name-only', '--diff-filter=A', f'{base}...HEAD', '--', 'runs'])
    return {os.path.basename(p)[:-5] for p in raw.decode().split() if p.endswith('.json')}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', required=True)
    a = ap.parse_args(argv)
    ids = added_runs(a.base)
    path = os.path.join(ROOT, 'data', 'scores.csv')
    if not os.path.exists(path): sys.exit('data/scores.csv missing; run scoring/score.py first')
    rows = [r for r in csv.DictReader(open(path, encoding='utf-8')) if r['run_id'] in ids]
    print('## Scores for the runs this pull request adds\n')
    if not rows:
        print('No new runs.' if not ids else f'{len(ids)} new run file(s), none scored.'); return 0
    per = collections.defaultdict(collections.Counter)
    for r in rows: per[r['model_family']][r['outcome']] += 1
    cols = [o for o in ORDER if any(c[o] for c in per.values())]
    print('| model | runs | ' + ' | '.join(cols) + ' |'); print('|---|---|' + '---|' * len(cols))
    for m, c in sorted(per.items()):
        n = sum(c.values()); print(f'| {m} | {n} | ' + ' | '.join(str(c[o]) if c[o] else '' for o in cols) + ' |')
    print('\n<details><summary>Every run</summary>\n\n| run | model | outcome | recall | precision | fidelity |\n|---|---|---|---|---|---|')
    for r in sorted(rows, key=lambda r: r['run_id']):
        print(f"| `{r['run_id']}` | {r['model_family']} | {r['outcome']} | {r['recall']} | {r['precision']} | {r['fidelity']} |")
    print('\n</details>')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
