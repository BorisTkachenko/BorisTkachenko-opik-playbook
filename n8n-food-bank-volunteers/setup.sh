#!/usr/bin/env bash
# Headless bootstrap — no browser needed:
#   1. works out where Opik's OTLP receiver is and starts n8n with the hooks baked in
#   2. claims the n8n instance (owner account) and mints an n8n API key
#   3. creates the OpenAI credential from $OPENAI_API_KEY (never written to a file)
#   4. imports workflow/volunteer-screening.json and activates it
# Requires docker, curl and python3. Keys come from your shell or the repo-root .env.
set -euo pipefail
cd "$(dirname "$0")"

N8N_URL="http://localhost:${N8N_PORT:-5678}"
OWNER_EMAIL="coordinator@example.com"     # local-only demo account
OWNER_PASSWORD="Pantry-demo-1"

# --- 0. Keys and the Opik endpoint -------------------------------------------
for f in ../.env .env; do [ -f "$f" ] && { set -a; . "$f"; set +a; }; done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (shell or repo-root .env)}"
OPIK_URL="${OPIK_URL_OVERRIDE:-http://localhost:5173/api/}"
OPIK_URL="${OPIK_URL%/}"
# Inside the container "localhost" is the container itself, so a self-hosted Opik on
# this machine is reached through host.docker.internal instead.
OPIK_URL="${OPIK_URL/localhost/host.docker.internal}"
OPIK_URL="${OPIK_URL/127.0.0.1/host.docker.internal}"
export OTLP_ENDPOINT="$OPIK_URL/v1/private/otel"
# Comet-Workspace picks the workspace, projectName the Opik project the traces land in.
# Opik Cloud also needs Authorization; a local self-hosted Opik does not.
OTLP_HEADERS="Comet-Workspace=${OPIK_WORKSPACE:-default},projectName=n8n-food-bank-volunteers"
[ -n "${OPIK_API_KEY:-}" ] && OTLP_HEADERS="Authorization=${OPIK_API_KEY},$OTLP_HEADERS"
export OTLP_HEADERS
echo "==> Opik OTLP endpoint (as seen from the container): $OTLP_ENDPOINT"

json() { python3 -c "import json,sys; d=json.load(sys.stdin); print(d$1)"; }

# --- 1. Start n8n ------------------------------------------------------------
echo "==> Building and starting n8n"
docker compose up -d --build

echo -n "==> Waiting for n8n"
for _ in $(seq 1 90); do
  curl -sf "$N8N_URL/healthz/readiness" >/dev/null 2>&1 && { echo " — up"; break; }
  echo -n "."; sleep 2
done
curl -sf "$N8N_URL/healthz/readiness" >/dev/null || { echo "n8n did not come up"; exit 1; }

# --- 2. Owner account and API key (REST, no browser) ----------------------------
# n8n ties the session cookie to a browser id, so every /rest call sends the same one.
COOKIES="$(mktemp)"; trap 'rm -f "$COOKIES"' EXIT
BROWSER_ID="setup-script"
SETUP_BODY=$(printf '{"email":"%s","firstName":"Pantry","lastName":"Coordinator","password":"%s"}' "$OWNER_EMAIL" "$OWNER_PASSWORD")
LOGIN_BODY=$(printf '{"emailOrLdapLoginId":"%s","password":"%s"}' "$OWNER_EMAIL" "$OWNER_PASSWORD")
AUTHED=""
for _ in $(seq 1 15); do
  # /rest can lag the health check on first boot. If the instance is already claimed, log in.
  if curl -sf -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
       -X POST "$N8N_URL/rest/owner/setup" -d "$SETUP_BODY" >/dev/null 2>&1; then AUTHED=yes; break; fi
  if curl -sf -c "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
       -X POST "$N8N_URL/rest/login" -d "$LOGIN_BODY" >/dev/null 2>&1; then AUTHED=yes; break; fi
  sleep 2
done
[ -n "$AUTHED" ] || { echo "could not authenticate against n8n"; exit 1; }

echo "==> Minting an n8n API key"
API_KEY=$(curl -sf -b "$COOKIES" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" \
  -X POST "$N8N_URL/rest/api-keys" \
  -d "{\"label\":\"setup-$(date +%s)\",\"expiresAt\":null,\"scopes\":[\"workflow:create\",\"workflow:read\",\"workflow:update\",\"workflow:delete\",\"workflow:list\",\"workflow:activate\",\"workflow:deactivate\",\"credential:create\",\"credential:delete\"]}" \
  | json "['data']['rawApiKey']")

api() { # method path [json-body]
  if [ -n "${3:-}" ]; then
    curl -sf -X "$1" "$N8N_URL/api/v1$2" -H "X-N8N-API-KEY: $API_KEY" -H 'Content-Type: application/json' -d "$3"
  else
    curl -sf -X "$1" "$N8N_URL/api/v1$2" -H "X-N8N-API-KEY: $API_KEY"
  fi
}

# --- 3. OpenAI credential (from the environment, never committed) ---------------
echo "==> Creating the OpenAI credential"
CRED_BODY=$(python3 -c 'import json,os; print(json.dumps({"name":"OpenAI (volunteer screening)","type":"openAiApi","data":{"apiKey":os.environ["OPENAI_API_KEY"]}}))')
CRED_ID=$(api POST /credentials "$CRED_BODY" | json "['id']")

# --- 4. Import and activate the workflow (replacing any earlier copy) ------------
api GET "/workflows?name=Volunteer%20screening" \
  | python3 -c "import json,sys; [print(w['id']) for w in json.load(sys.stdin).get('data',[])]" \
  | while read -r wid; do api DELETE "/workflows/$wid" >/dev/null; echo "    removed old workflow $wid"; done

echo "==> Importing workflow/volunteer-screening.json"
WF_BODY=$(python3 - "$CRED_ID" <<'PY'
import json, sys
wf = json.load(open("workflow/volunteer-screening.json"))
print(json.dumps(wf).replace("__OPENAI_CREDENTIAL_ID__", sys.argv[1]))
PY
)
WF_ID=$(api POST /workflows "$WF_BODY" | json "['id']")
api POST "/workflows/$WF_ID/activate" "" >/dev/null

echo
echo "Done. n8n UI: $N8N_URL  (login: $OWNER_EMAIL / $OWNER_PASSWORD)"
echo "Webhook:      $N8N_URL/webhook/volunteer-signup"
echo "Next:         ./demo.sh"
