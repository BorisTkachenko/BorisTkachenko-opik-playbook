#!/usr/bin/env bash
# Start Langflow and create the "Gym front desk" flow. Needs docker and python3.
set -euo pipefail
cd "$(dirname "$0")"
for f in ../.env .env; do [ -f "$f" ] && { set -a; . "$f"; set +a; }; done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (shell or repo-root .env)}"
docker compose up -d
python3 setup.py
