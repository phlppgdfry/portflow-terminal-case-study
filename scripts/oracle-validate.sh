#!/usr/bin/env bash
# Runs database/*.sql against Oracle Database Free in Docker and fails on any SQL error.
# Used by CI. Locally: needs Docker; the first pull is about 1 GB.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="portflow-oracle"
IMAGE="gvenzl/oracle-free:23-slim-faststart"

if ! docker ps --format '{{.Names}}' | grep -qx "$NAME"; then
  docker run -d --name "$NAME" -e ORACLE_PASSWORD=ci_system \
    -e APP_USER=portflow -e APP_USER_PASSWORD=portflow \
    -v "$ROOT/database:/sql:ro" "$IMAGE" >/dev/null
fi

echo "Waiting for Oracle to accept connections..."
for _ in $(seq 1 60); do
  docker exec "$NAME" healthcheck.sh >/dev/null 2>&1 && break
  sleep 5
done
docker exec "$NAME" healthcheck.sh >/dev/null

run() {  # run <connect string>  (script on stdin)
  docker exec -i "$NAME" sqlplus -s -L "$1"
}

echo "== Schema, sample data and diagnostic queries as the application user"
run "portflow/portflow@//localhost/FREEPDB1" <<'EOF'
WHENEVER SQLERROR EXIT SQL.SQLCODE
WHENEVER OSERROR EXIT FAILURE
SET FEEDBACK ON
@/sql/schema.sql
@/sql/sample-data.sql
@/sql/diagnostic-queries.sql
EXIT
EOF

echo "== DBA session checks"
run "system/ci_system@//localhost/FREEPDB1" <<'EOF'
WHENEVER SQLERROR EXIT SQL.SQLCODE
@/sql/dba-session-checks.sql
EXIT
EOF

echo "Oracle validation passed."
