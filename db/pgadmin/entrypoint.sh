#!/bin/sh
# Start pgAdmin's original entrypoint, then inject the saved password
# so the browser connects to HirePilot DB without a password prompt.

/entrypoint.sh &
PGADMIN_PID=$!

# Run password injection in background (waits internally for DB readiness)
/venv/bin/python3 /pgadmin4/inject_password.py &

wait $PGADMIN_PID
