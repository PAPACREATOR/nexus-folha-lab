#!/usr/bin/env bash
set -euo pipefail
# The app is localhost-only and never executes Nexus actions.
if (echo >/dev/tcp/127.0.0.1/8765) >/dev/null 2>&1; then
  echo "Folha already listening on localhost:8765"
  exit 0
fi
nohup python -m folha_lab.server >/tmp/nexus-folha-lab.log 2>&1 </dev/null &
echo "Folha started locally. Codespaces forwards port 8765 privately."
