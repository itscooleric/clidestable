#!/bin/bash
set -e

# Start Flask on internal port 7691 (Caddy proxies from 7690)
echo "clidestable: starting Flask on :7691"
clidestable serve --port 7691 --log-dir /data &
FLASK_PID=$!

# Give Flask a moment to start
sleep 1

# Start Caddy as the single external proxy on :7690
echo "clidestable: starting Caddy proxy on :7690"
caddy run --config /app/Caddyfile &
CADDY_PID=$!

echo "clidestable: ready — dashboard + stalls on :7690"

# Wait for either process to exit
wait -n $FLASK_PID $CADDY_PID
EXIT_CODE=$?
echo "clidestable: process exited ($EXIT_CODE), shutting down"
kill $FLASK_PID $CADDY_PID 2>/dev/null
exit $EXIT_CODE
