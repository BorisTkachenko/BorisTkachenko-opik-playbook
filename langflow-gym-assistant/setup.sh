#!/usr/bin/env bash
# Start Langflow and create the "Gym front desk" flow. Needs docker and python3.
set -euo pipefail
cd "$(dirname "$0")"
for f in ../.env .env; do [ -f "$f" ] && { set -a; . "$f"; set +a; }; done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (shell or repo-root .env)}"
# Inside the container "localhost" is the container itself, so a self-hosted Opik on
# this machine is reached through host.docker.internal.
OPIK_URL="${OPIK_URL_OVERRIDE:-http://localhost:5173/api/}"
OPIK_URL="${OPIK_URL/localhost/host.docker.internal}"
export OPIK_URL_FOR_CONTAINER="${OPIK_URL/127.0.0.1/host.docker.internal}"
echo "==> Langflow will trace to Opik at $OPIK_URL_FOR_CONTAINER (project langflow-gym-assistant)"
docker compose up -d --build
python3 setup.py
