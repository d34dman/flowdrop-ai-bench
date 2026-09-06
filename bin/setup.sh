#!/bin/sh
# Installs the runner site. Run from anywhere in the checkout, after `ddev start` at the
# repo root (the DDEV project root is the repo; the Drupal docroot is runner/web).
#
#   sh bin/setup.sh
#
# Re-running reinstalls the site from runner/config/sync: stored pipelines are lost, but
# the ledger in runner/var/ and the committed runs/ and outputs/ are files and stay.
set -eu
cd "$(dirname "$0")/.."
[ -f .ddev/.env ] && grep -q ANTHROPIC_KEY .ddev/.env || {
  echo "Put your key in .ddev/.env first:  echo 'ANTHROPIC_KEY=sk-ant-...' >> .ddev/.env && ddev restart"; exit 1; }
ddev composer install --no-interaction
ddev drush site:install minimal -y --existing-config --account-name=admin
ddev drush cr
echo "Runner ready: $(ddev describe -j | python3 -c 'import json,sys; print(json.load(sys.stdin)["raw"]["primary_url"])')"
echo "Try:  ddev drush bench:run B1 claude-haiku-4-5-20251001 --pages=small --tag=$(whoami)-first"
