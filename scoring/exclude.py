#!/usr/bin/env python3
"""Withdraw runs from grading without touching the dataset. Standard library only.

    python3 scoring/exclude.py --kind harness --reason "why" <run_id-prefix> [<run_id-prefix> ...]
    python3 scoring/exclude.py --list

Writes one exclusions/<run_id>.json per run. The run files in runs/ and outputs/ are
append-only and stay as they are; the scorer reads exclusions/ and classes each named run
`excluded`, kept in the CSVs with its reason but left out of every graded count, exactly
like a `stale` run. Kinds:

  harness    the runner, its config or FlowDrop itself broke the run (a timeout, a bug)
  provider   the model API failed for reasons of its own (outage, rate limit)
  operator   the run was launched wrong (wrong model, wrong page, aborted by hand)
  duplicate  a rerun superseded it and both would double-count a cell

A prefix must match exactly one run. Filing the same run twice is refused.
"""
import getpass, json, os, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS, EXCL = os.path.join(ROOT, 'runs'), os.path.join(ROOT, 'exclusions')
KINDS = ('harness', 'provider', 'operator', 'duplicate')
FIELDS = ('run_id', 'kind', 'reason', 'by', 'ts')


def load():
    """{run_id: record} for every file in exclusions/."""
    out = {}
    if not os.path.isdir(EXCL): return out
    for fn in sorted(os.listdir(EXCL)):
        if fn.endswith('.json'):
            r = json.load(open(os.path.join(EXCL, fn), encoding='utf-8')); out[r['run_id']] = r
    return out


def main(argv):
    if '--list' in argv:
        for r in load().values(): print(f"{r['kind']:10} {r['run_id']}\n           {r['reason']}")
        return 0
    if '--kind' not in argv or '--reason' not in argv:
        print(__doc__); return 2
    kind = argv[argv.index('--kind') + 1]; reason = argv[argv.index('--reason') + 1].strip()
    if kind not in KINDS: print(f'kind must be one of {", ".join(KINDS)}'); return 2
    if len(reason) < 20: print('reason must say what went wrong and what was done about it (>= 20 chars)'); return 2
    prefixes = [a for i, a in enumerate(argv) if not a.startswith('--') and argv[i - 1] not in ('--kind', '--reason')]
    if not prefixes: print('name at least one run'); return 2
    runs = sorted(fn[:-5] for fn in os.listdir(RUNS) if fn.endswith('.json'))
    have = load(); by = os.environ.get('BENCH_BY') or getpass.getuser(); ts = datetime.now(timezone.utc).isoformat(timespec='seconds')
    os.makedirs(EXCL, exist_ok=True); bad = 0
    for p in prefixes:
        m = [r for r in runs if r.startswith(p)]
        if len(m) != 1: print(f'{p}: matches {len(m)} runs, need exactly 1'); bad += 1; continue
        if m[0] in have: print(f'{m[0]}: already excluded ({have[m[0]]["kind"]})'); bad += 1; continue
        rec = dict(run_id=m[0], kind=kind, reason=reason, by=by, ts=ts)
        json.dump(rec, open(os.path.join(EXCL, m[0] + '.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print(f'excluded {m[0]}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
