#!/bin/bash
set -euo pipefail

MODE="${1:-list}"

if [ "${MODE}" = "dry-run" ]; then
  MODE="list"
fi

if [ "${MODE}" != "list" ] && [ "${MODE}" != "clean" ] && [ "${MODE}" != "legacy-report" ]; then
  echo "Usage: $0 [list|clean|dry-run|legacy-report]" >&2
  exit 1
fi

patterns=(
  "status/verify_1.json"
  "status/verify_2.json"
  "status/verify_1.canon.json"
  "status/verify_2.canon.json"
  "status/by_run/verify_1.*.json"
  "status/by_run/verify_2.*.json"
)

echo "Status artifact cleanup mode: ${MODE}"
MATCH_COUNT=0
ACTION_COUNT=0

for pattern in "${patterns[@]}"; do
  shopt -s nullglob
  matches=($pattern)
  shopt -u nullglob
  if [ ${#matches[@]} -eq 0 ]; then
    continue
  fi
  for path in "${matches[@]}"; do
    if [ ! -e "$path" ]; then
      continue
    fi
    MATCH_COUNT=$((MATCH_COUNT + 1))
    if [ "${MODE}" = "clean" ]; then
      rm -f "$path"
      echo "removed $path"
      ACTION_COUNT=$((ACTION_COUNT + 1))
    else
      echo "$path"
      ACTION_COUNT=$((ACTION_COUNT + 1))
    fi
  done
done

echo "summary mode=${MODE} matches=${MATCH_COUNT} actions=${ACTION_COUNT}"

python3 - <<'PY' "${MODE}"
import json
import sys
from pathlib import Path

mode = sys.argv[1]
artifacts = sorted(Path("status/by_run").glob("verify_*.json"))
legacy = []
for path in artifacts:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    if payload.get("provenance", {}).get("status") is not None:
        legacy.append(path)

if mode == "legacy-report":
    for path in legacy:
        print(path)

print(f"legacy_provenance_status_count={len(legacy)}")
PY
