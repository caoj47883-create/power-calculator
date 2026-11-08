#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SRC="../app/assets"
DST="PowerLedger/Resources/web"
for file in index.html styles.css app.js model.js; do
  cp "$SRC/$file" "$DST/$file"
  echo "synced $file"
done
