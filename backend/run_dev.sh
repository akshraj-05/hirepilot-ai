#!/usr/bin/env bash
# Run API from the backend directory so `app` imports correctly.
# --reload-dir limits the file watcher to this package (avoids PermissionError when
# watchfiles scans unrelated dirs under $HOME).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 4000 \
  --reload \
  --reload-dir "${PWD}/app"
