#!/usr/bin/env bash
set -euo pipefail

TITLE=${1:-}
if [[ -z "$TITLE" ]]; then
  echo "Usage: $0 \"Title of decision\"" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEC_DIR="$ROOT/decisions"
IDX_FILE="$ROOT/index/adr_index.jsonl"
TEMPLATE="$DEC_DIR/ADR_TEMPLATE.md"

DATE_YYYYMMDD=$(date +%Y%m%d)
DATE_ISO=$(date +%F)

# Find next NNN
NNN=1
while true; do
  ADR_ID=$(printf "ADR-%s-%03d" "$DATE_YYYYMMDD" "$NNN")
  SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g')
  OUT="$DEC_DIR/${ADR_ID}-${SLUG}.md"
  if [[ ! -f "$OUT" ]]; then
    break
  fi
  NNN=$((NNN+1))
done

cp "$TEMPLATE" "$OUT"
# Basic substitutions
sed -i \
  -e "s/ADR-YYYYMMDD-NNN/${ADR_ID}/g" \
  -e "s/<Title>/${TITLE}/g" \
  -e "s/YYYY-MM-DD/${DATE_ISO}/g" \
  "$OUT"

# Hash for index
HASH=$(sha256sum "$OUT" | awk '{print $1}')

# Append minimal index entry (owners/tags can be edited later)
cat >> "$IDX_FILE" <<EOF
{"adr_id":"${ADR_ID}","title":"${TITLE}","status":"Proposed","date":"${DATE_ISO}","owners":[],"tags":[],"path":"knowledge/decisions/$(basename "$OUT")","evidence":[],"artifact_links":[],"hash":"${HASH}","created_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF

echo "$OUT"
