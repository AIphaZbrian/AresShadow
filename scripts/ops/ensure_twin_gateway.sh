#!/usr/bin/env bash
set -euo pipefail

PORT="${TWIN_GATEWAY_PORT:-18801}"
PIDFILE="${TWIN_GATEWAY_PIDFILE:-/tmp/openclaw/gateway-twin.pid}"
OUTFILE="${TWIN_GATEWAY_OUTFILE:-/tmp/openclaw/gateway-twin-${PORT}.out}"

is_alive() {
  local pid="$1"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  # Basic sanity: must look like openclaw gateway process
  ps -p "$pid" -o comm= 2>/dev/null | grep -q "openclaw" || return 1
}

start_gateway() {
  nohup openclaw --profile twin gateway run --bind loopback --port "$PORT" >"$OUTFILE" 2>&1 &
  local pid="$!"
  echo "$pid" > "$PIDFILE"
  echo "started pid=$pid port=$PORT"
}

if [[ -f "$PIDFILE" ]]; then
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if is_alive "$pid"; then
    exit 0
  fi
fi

# If we reach here, no valid running pid was found.
start_gateway
