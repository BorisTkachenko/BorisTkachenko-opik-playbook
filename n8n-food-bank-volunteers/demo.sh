#!/usr/bin/env bash
# POST every sign-up in data/applicants.json to the webhook and print the screening.
# Each request is one workflow execution, and therefore one trace in Opik.
set -euo pipefail
cd "$(dirname "$0")"
WEBHOOK="${WEBHOOK:-http://localhost:${N8N_PORT:-5678}/webhook/volunteer-signup}"

python3 -c 'import json; [print(json.dumps(a)) for a in json.load(open("data/applicants.json"))]' |
while IFS= read -r applicant; do
  name=$(printf '%s' "$applicant" | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])')
  echo "── $name"
  ok=""
  # The webhook registers a few seconds after activation, so retry for ~30s.
  for _ in $(seq 1 15); do
    if out=$(curl -sf -X POST "$WEBHOOK" -H 'Content-Type: application/json' -d "$applicant"); then
      printf '%s\n' "$out" | python3 -m json.tool; ok=yes; break
    fi
    sleep 2
  done
  [ -n "$ok" ] || { echo "webhook did not answer at $WEBHOOK — did setup.sh finish?" >&2; exit 1; }
done
echo
echo "Open the n8n-food-bank-volunteers project in Opik: one trace per sign-up above."
