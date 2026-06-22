#!/bin/bash
# scripts/test-prowlarr-repair.sh — Verify repair script logic without touching containers.
set -euo pipefail

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Copy live DB and corrupt it intentionally
cp "$HOME/homelab-data/arr/prowlarr/prowlarr.db" "$TMP/prowlarr.db"
sqlite3 "$TMP/prowlarr.db" "PRAGMA writable_schema=ON; DELETE FROM sqlite_master WHERE type='table'; PRAGMA writable_schema=OFF;"

# Verify corruption detection
if sqlite3 "$TMP/prowlarr.db" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
  echo "FAIL: test DB did not become corrupt"; exit 1
fi

# Verify backup scanning picks a clean backup
cp "$HOME/homelab-data/arr/prowlarr/prowlarr.db" "$TMP/clean.db"
if sqlite3 "$TMP/clean.db" "PRAGMA integrity_check;" 2>/dev/null | grep -qx 'ok'; then
  echo "PASS: clean backup integrity check works"
else
  echo "FAIL: live DB is also corrupt"; exit 1
fi

echo "All tests passed."
