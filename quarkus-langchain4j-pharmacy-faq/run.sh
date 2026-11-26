#!/usr/bin/env bash
# Build the app, boot it, ask the scripted questions over HTTP, stop it. Exit 0 on success.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:$PATH"

# Load keys from the repo-root .env (walking up) and a local .env, if present.
dir="$PWD"
while [[ "$dir" != "/" ]]; do
  if [[ -f "$dir/.env" ]]; then set -a; source "$dir/.env"; set +a; break; fi
  dir="$(dirname "$dir")"
done
[[ -f .env ]] && { set -a; source .env; set +a; }
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (see .env.example)}"

# Point the OTLP exporter at the same Opik the SDKs use (OPIK_URL_OVERRIDE ends in /api/).
if [[ -n "${OPIK_URL_OVERRIDE:-}" ]]; then
  export OPIK_OTEL_ENDPOINT="${OPIK_OTEL_ENDPOINT:-${OPIK_URL_OVERRIDE%/}/v1/private/otel}"
fi

PORT="${PHARMACY_PORT:-5581}"
export PHARMACY_PORT="$PORT"

mvn -q -DskipTests package

java -jar target/quarkus-app/quarkus-run.jar > target/app.log 2>&1 &
APP_PID=$!
trap 'kill "$APP_PID" 2>/dev/null || true; wait "$APP_PID" 2>/dev/null || true' EXIT

# Wait until Quarkus reports it is listening (the leaflets are indexed before that).
for _ in $(seq 1 90); do
  grep -q "Listening on" target/app.log && break
  kill -0 "$APP_PID" 2>/dev/null || { cat target/app.log; exit 1; }
  sleep 1
done
grep -q "Listening on" target/app.log || { cat target/app.log; exit 1; }

while IFS= read -r q; do
  [[ -z "$q" ]] && continue
  echo "Q: $q"
  echo "A: $(curl -sf --get --data-urlencode "q=$q" "http://localhost:$PORT/ask")"
  echo
done < questions.txt
