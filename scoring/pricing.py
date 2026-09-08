"""Prices a run from its token counts against scoring/pricing.json. Standard library only.

    python3 scoring/pricing.py                 # every priced model, and any run the table cannot price

The table is the bench's own list-price ledger (see the _comment in pricing.json). The row
for a run is the one with the latest effective_from on or before the run's ts. A run with
tokens and no row is an error: the scorer stops and the dataset gate fails, so a new model
cannot enter the dataset unpriced.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, 'scoring', 'pricing.json')


def load(path=TABLE):
    rows = json.load(open(path, encoding='utf-8'))['rows']
    by = {}
    for r in rows: by.setdefault(r['model'], []).append(r)
    for v in by.values(): v.sort(key=lambda r: r['effective_from'])
    return by


def row_for(table, model, ts):
    """The pricing row in effect for `model` at ISO timestamp `ts`, or None."""
    day = (ts or '')[:10]
    hit = None
    for r in table.get(model, []):
        if r['effective_from'] <= day: hit = r
    return hit


def price(table, run):
    """(cost_usd, row) for one run record. cost 0 and row None when the run made no call."""
    tokens = (run.get('input_tokens') or 0) + (run.get('output_tokens') or 0) + (run.get('cached_tokens') or 0)
    models = run.get('models') or []
    if not tokens: return 0.0, None
    if len(models) != 1:
        raise LookupError(f"{run.get('run_id')}: {len(models)} models answered; run-level tokens cannot be priced per model")
    row = row_for(table, models[0], run.get('ts'))
    if row is None:
        raise LookupError(f"{run.get('run_id')}: no price for {models[0]} at {(run.get('ts') or '?')[:10]} in scoring/pricing.json")
    cost = ((run.get('input_tokens') or 0) * row['input']
            + (run.get('cached_tokens') or 0) * (row.get('cache_read') or 0)
            + (run.get('output_tokens') or 0) * row['output']) / 1e6
    return round(cost, 6), row


def main():
    table = load()
    print(f"{'model':36} {'provider':11} {'in':>7} {'out':>7} {'cache':>7}  from        source")
    for m in sorted(table):
        for r in table[m]:
            print(f"{m:36} {r['provider']:11} {r['input']:>7} {r['output']:>7} {r.get('cache_read') or 0:>7}  {r['effective_from']}  {r['source']}")
    runs = os.path.join(ROOT, 'runs'); bad = 0
    for fn in sorted(os.listdir(runs)):
        if not fn.endswith('.json'): continue
        try: price(table, json.load(open(os.path.join(runs, fn), encoding='utf-8')))
        except LookupError as e: print('ERROR', e); bad += 1
    print(f'\n{bad} run(s) the table cannot price' if bad else '\nevery run priced')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
