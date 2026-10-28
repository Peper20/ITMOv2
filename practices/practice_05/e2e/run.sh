#!/bin/sh
# Сквозные проверки на временной БД: ./run.sh recurring.mjs [каталог для скриншотов]
set -eu
cd "$(dirname "$0")"
[ -d node_modules ] || npm install --silent
TMP=$(mktemp -d)
PORT=8765 DB_PATH="$TMP/e2e.db" python3 ../project/backend/server.py >"$TMP/server.log" 2>&1 &
SRV=$!
trap 'kill $SRV; rm -rf "$TMP"' EXIT
sleep 1.5
node "$1" http://127.0.0.1:8765 "${2:-$TMP}"
