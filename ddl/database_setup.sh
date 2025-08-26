#!/usr/bin/env bash
# run_import_with_http.sh
# Starts a local HTTP server to serve import files, runs a CockroachDB SQL script,
# then cleans up the server.

set -Eeuo pipefail

# --- Tunables (override via env) ---------------------------------------------
PORT="${PORT:-3000}"
BIND="${BIND:-${HOSTNAME:-0.0.0.0}}"        # interface to bind the HTTP server
ADVERTISE_HOST="${ADVERTISE_HOST:-$BIND}"   # what goes in the SQL URLs
SERVE_DIR="${SERVE_DIR:-./demo_data}"   # ← default to demo_data now
CRDB_SQL_FILE="${CRDB_SQL_FILE:-setup_script_02.sql}"

# Host to probe for readiness. If binding all interfaces, hit localhost.
CHECK_HOST="${CHECK_HOST:-}"
if [[ -z "$CHECK_HOST" ]]; then
  if [[ "$BIND" == "0.0.0.0" || "$BIND" == "::" ]]; then
    CHECK_HOST="127.0.0.1"
  else
    CHECK_HOST="$BIND"
  fi
fi

# --- Helpers -----------------------------------------------------------------
need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 127; }; }
log()  { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

need python3
need cockroach

[[ -f "$CRDB_SQL_FILE" ]] || { echo "SQL file not found: $CRDB_SQL_FILE" >&2; exit 1; }
[[ -d "$SERVE_DIR" ]]      || { echo "Serve dir not found: $SERVE_DIR" >&2; exit 1; }

# --- Start HTTP server -------------------------------------------------------
pushd "$SERVE_DIR" >/dev/null
log "Starting http.server on ${BIND}:${PORT} (serving $(pwd))"
python3 -m http.server --bind "$BIND" "$PORT" >"/tmp/http_server_${PORT}.log" 2>&1 &
HTTP_PID=$!

cleanup() {
  log "Shutting down http.server (pid ${HTTP_PID})"
  kill "$HTTP_PID" 2>/dev/null || true
  wait "$HTTP_PID" 2>/dev/null || true
  popd >/dev/null || true
}
trap cleanup EXIT

# --- Wait until the port is listening ----------------------------------------
for _ in {1..50}; do
  # /dev/tcp works in bash; avoids requiring nc/curl
  if (echo >"/dev/tcp/${CHECK_HOST}/${PORT}") >/dev/null 2>&1; then
    log "http.server is up"
    break
  fi
  sleep 0.2
done

# --- Rewrite SQL to use current host/port ------------------------------------
# Replace any numeric IP at :3000 with http://$ADVERTISE_HOST:$PORT/
# (Adjust the pattern if your source SQL may have hostnames instead of numeric IPs.)
# Create a temp SQL file and ensure it's cleaned up
TMP_SQL="$(mktemp -t dbsetup.XXXXXX.sql)"
cleanup() { rm -f "$TMP_SQL"; }
trap cleanup EXIT

log "Rewriting ${CRDB_SQL_FILE} to use http://${ADVERTISE_HOST}:${PORT}/ ..."
# Repoint all CSV URLs to the current node:port
sed -E "s#http://[^:'\"]+:${PORT}/#http://${ADVERTISE_HOST}:${PORT}/#g" \
  "../${CRDB_SQL_FILE}" > "NEW_${CRDB_SQL_FILE}"



# --- Run the Cockroach SQL script -------------------------------------------
log "Running cockroach sql (file: NEW_${CRDB_SQL_FILE})"
cockroach sql -f "../setup_script_00.sql"   # pre-import setup
cockroach sql -f "../setup_script_01.sql"   # pre-import setup
cockroach sql -f "NEW_${CRDB_SQL_FILE}"
cockroach sql -f "../setup_script_03.sql"   # pre-import setup

log "Import script finished successfully."
