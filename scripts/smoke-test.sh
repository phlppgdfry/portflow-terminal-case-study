#!/usr/bin/env bash
# Post-deployment smoke test (docs/08-release-plan.md, step S1-S6).
# Usage: scripts/smoke-test.sh [base-url]
# Without a URL it starts a throwaway service on a free port and stops it afterwards.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${1:-}"
PID=""

cleanup() { [[ -n "$PID" ]] && kill "$PID" 2>/dev/null || true; [[ -n "${WORK:-}" ]] && rm -rf "$WORK"; }
trap cleanup EXIT

if [[ -z "$BASE" ]]; then
  WORK="$(mktemp -d)"
  PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
  (cd "$ROOT/service" && PORTFLOW_DB="$WORK/smoke.db" PORTFLOW_SPOOL_DIR="$WORK/spool" \
    exec python3 -m portflow serve --port "$PORT" >"$WORK/service.log" 2>&1) &
  PID=$!
  BASE="http://127.0.0.1:$PORT"
  for _ in $(seq 1 50); do curl -fs "$BASE/health" >/dev/null 2>&1 && break; sleep 0.1; done
fi

pass() { printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; exit 1; }
REF="SMOKE-$(date +%s)"

echo "Smoke test against $BASE"

health="$(curl -fs "$BASE/health")" || fail "S1 health endpoint unreachable"
grep -q '"database": "UP"' <<<"$health" && pass "S1 service up, database reachable" || fail "S1 database not UP: $health"

body="$(python3 - "$ROOT/integrations/sample-vehicle-import.json" "$REF" <<'EOF'
import json, sys
p = json.load(open(sys.argv[1])); p["messageRef"] = sys.argv[2]; p["shipmentId"] = sys.argv[2]
print(json.dumps(p))
EOF
)"
code="$(curl -s -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -d "$body" "$BASE/api/v1/vehicle-manifests")"
[[ "$code" == 201 ]] && pass "S2 REST manifest accepted" || fail "S2 REST manifest returned HTTP $code"

edi="$(sed "s/000125/${REF: -6}/g; s/HRN-2026-00125/$REF/" "$ROOT/integrations/sample-edi-message.edi")"
code="$(curl -s -o /dev/null -w '%{http_code}' -H 'Content-Type: text/plain' --data-binary "$edi" "$BASE/api/v1/edi-messages")"
[[ "$code" == 201 ]] && pass "S3 EDI manifest accepted" || fail "S3 EDI manifest returned HTTP $code"

curl -fs "$BASE/api/v1/shipments?limit=500" | grep -q "\"$REF\"" && pass "S4 shipment stored in database" || fail "S4 shipment $REF not found"

code="$(curl -s -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -d "$body" "$BASE/api/v1/vehicle-manifests")"
[[ "$code" == 200 ]] && pass "S5 resend recognised as duplicate" || fail "S5 duplicate returned HTTP $code"

curl -fs "$BASE/ops" | grep -q "PortFlow" && pass "S6 operations page loads" || fail "S6 operations page"

echo "Smoke test passed."
