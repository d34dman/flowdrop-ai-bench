#!/bin/sh
# Thin wrapper around `drush bench:run`, kept for muscle memory from the old
# scratchpad/bench/run_cell.sh. All the actual logic lives in the
# flowdrop_ai_bench module's bench:* Drush commands.
#
# Usage: run_cell.sh <cells> <model> [pages] [reps] [tag]
#   cells  comma list of B0..B9 (or raw workflow ids)   e.g. B5  or  B8,B9
#   model  bare model id                                e.g. claude-sonnet-5
#   pages  comma list of small,medium,large              default: small,medium,large
#   reps   repetitions                                   default: 1
#   tag    ledger tag written to runs.jsonl               default: <cells>-<model>
set -eu
CELLS=${1:?cells}; MODEL=${2:?model}; PAGES=${3:-small,medium,large}; REPS=${4:-1}; TAG=${5:-}

set -- bench:run "$CELLS" "$MODEL" --pages="$PAGES" --reps="$REPS"
if [ -n "$TAG" ]; then
  set -- "$@" --tag="$TAG"
fi

exec ddev drush "$@"
