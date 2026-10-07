#!/usr/bin/env bash
# Reproduces INC-001 (incidents/INC-001-edi-processing-failure.md) on a local copy:
#   1. start 1.3.0 with the 1.2.0 defect switched back on and the 1.2.0 pool size (5)
#   2. a partner resends an already announced shipment several times -> connections leak
#   3. a normal manifest now ends up PENDING: the symptom operations reported
#   4. restart without the defect (the 1.2.1 fix) -> the spooled message is recovered
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
BASE="http://127.0.0.1:$PORT"
PID=""
trap '[[ -n "$PID" ]] && kill "$PID" 2>/dev/null; rm -rf "$WORK"' EXIT

start() {  # start <leak 0|1> <spool interval seconds>
  (cd "$ROOT/service" && PORTFLOW_DB="$WORK/inc.db" PORTFLOW_SPOOL_DIR="$WORK/spool" \
    PORTFLOW_POOL_SIZE=5 PORTFLOW_POOL_TIMEOUT=0.5 PORTFLOW_RETRY_BACKOFF=0.2 PORTFLOW_SPOOL_INTERVAL="$2" \
    PORTFLOW_FAULT_LEAK_ON_ERROR="$1" exec python3 -m portflow serve --port "$PORT" >>"$WORK/service.log" 2>&1) &
  PID=$!
  for _ in $(seq 1 50); do curl -fs "$BASE/health" >/dev/null 2>&1 && break; sleep 0.1; done
}
manifest() {  # manifest <messageRef> <shipmentId>
  python3 - "$ROOT/integrations/sample-vehicle-import.json" "$1" "$2" <<'EOF'
import json, sys
p = json.load(open(sys.argv[1])); p["messageRef"], p["shipmentId"] = sys.argv[2], sys.argv[3]
print(json.dumps(p))
EOF
}
post() { curl -s -H 'Content-Type: application/json' -d "$1" "$BASE/api/v1/vehicle-manifests" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])'; }
health() {
  curl -s "$BASE/health" | python3 -c 'import json, sys
h = json.load(sys.stdin)
print("health=%s database=%s pool=%s/%s free backlog=%s" % (h["status"], h["database"], h["pool"]["available"], h["pool"]["size"], h["pendingBacklog"]))'
}

echo "== 1. Service with the 1.2.0 defect, pool size 5"
start 1 3600  # spool worker effectively off, so the log stays readable
echo "first announcement           -> $(post "$(manifest MSG-1 SHIP-A)")"
for n in 2 3 4 5 6; do
  echo "resend of SHIP-A (MSG-$n)     -> $(post "$(manifest "MSG-$n" SHIP-A)")"
done
echo "   $(health)"

echo "== 2. A normal manifest now"
echo "new shipment SHIP-B          -> $(post "$(manifest MSG-7 SHIP-B)")"
echo "   $(health)"

echo "== 3. Service log (what second-line support sees)"
# everything logged for the last message (SHIP-B)
awk '/MESSAGE_RECEIVED/ {buf=""} {buf = buf "   " $0 "\n"} END {printf "%s", buf}' "$WORK/service.log"

echo "== 4. Restart with the fix (1.2.1 behaviour): the backlog drains"
kill "$PID"; wait "$PID" 2>/dev/null || true
start 0 1
sleep 2.5
echo "   $(health)"
grep -E "MESSAGE_RECOVERED" "$WORK/service.log" | sed "s/^/   /" || echo "   (nothing recovered)"
