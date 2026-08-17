#!/usr/bin/env bash
# Start the dashboard for front-end development: the Python backend plus the
# Vite dev server with hot reload.
#
# `hermes dashboard` serves the *built* bundle from hermes_cli/web_dist/, so
# edits under web/src/ do not show up there until you rebuild. For UI work you
# want this script instead — open the Vite URL it prints, not port 9119.
#
# How the two halves connect (see web/vite.config.ts):
#   - Vite proxies /api and /dashboard-plugins to $HERMES_DASHBOARD_URL.
#   - In production the backend injects a session token into index.html. Vite
#     serves its own index.html, so a dev-only plugin scrapes that token from
#     the running backend and re-injects it. The backend must therefore be up
#     before the browser loads the page, or every /api call 401s.
#
# Usage:
#   scripts/dev-dashboard.sh              # start backend if needed, then Vite
#   scripts/dev-dashboard.sh --port 9200  # use a different backend port
#   scripts/dev-dashboard.sh --check      # typecheck + test + lint, no servers
#
# If a backend is already listening this script reuses it and leaves it running
# on exit. Only a backend it started itself is stopped on Ctrl+C.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=9119
STARTED_BACKEND=""
BACKEND_LOG=""

die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '\033[36m▸\033[0m %s\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="${2:?--port needs a value}"; shift 2 ;;
    --check)
      cd "$REPO/web"
      info "running typecheck + tests + lint"
      exec npm run check
      ;;
    # Print the header block: every comment line after the shebang, stopping
    # at the first line that is not a comment. No hardcoded line numbers to
    # drift out of sync when the header is edited.
    -h|--help)
      awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
      exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

BACKEND="http://127.0.0.1:${PORT}"

command -v npm >/dev/null || die "npm not found — install Node.js first"
command -v hermes >/dev/null || die "hermes not on PATH — activate the venv"

# Dependencies are hoisted to the workspace root, so a populated web/node_modules
# is not the signal to check; vite living in the root .bin is.
if [[ ! -x "$REPO/node_modules/.bin/vite" ]]; then
  info "installing workspace dependencies (first run)"
  (cd "$REPO" && npm run install:web)
fi

backend_up() { curl -fsS -m 2 "$BACKEND" -H 'accept: text/html' 2>/dev/null | grep -q '__HERMES_SESSION_TOKEN__'; }

cleanup() {
  if [[ -n "$STARTED_BACKEND" ]] && kill -0 "$STARTED_BACKEND" 2>/dev/null; then
    info "stopping backend (pid $STARTED_BACKEND)"
    kill "$STARTED_BACKEND" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if backend_up; then
  info "reusing backend already on $BACKEND (left running on exit)"
else
  BACKEND_LOG="$(mktemp -t hermes-dev-backend.XXXXXX.log)"
  info "starting backend on $BACKEND  (log: $BACKEND_LOG)"
  # `serve` is the headless backend; `dashboard` would also open a browser at
  # the built bundle, which is the thing we are trying to bypass.
  (cd "$REPO" && hermes serve --port "$PORT" --skip-build) >"$BACKEND_LOG" 2>&1 &
  STARTED_BACKEND=$!

  for _ in $(seq 60); do
    backend_up && break
    kill -0 "$STARTED_BACKEND" 2>/dev/null || { cat "$BACKEND_LOG" >&2; die "backend exited during startup"; }
    sleep 0.5
  done
  backend_up || { tail -30 "$BACKEND_LOG" >&2; die "backend did not become ready in 30s"; }
  info "backend ready"
fi

info "starting Vite — open the URL below, not :$PORT"
cd "$REPO/web"
HERMES_DASHBOARD_URL="$BACKEND" exec npm run dev
