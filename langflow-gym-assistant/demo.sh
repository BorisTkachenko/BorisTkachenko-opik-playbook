#!/usr/bin/env bash
# Play the scripted member conversations against the flow.
set -euo pipefail
cd "$(dirname "$0")"
python3 demo.py
