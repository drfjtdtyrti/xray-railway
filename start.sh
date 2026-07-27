#!/bin/bash
set -e

PORT=${PORT:-8080}

echo "[+] Port: $PORT"
echo "[+] Substituting nginx config..."
envsubst '$PORT' < /etc/nginx/nginx.conf.tmpl > /etc/nginx/nginx.conf

echo "[+] Starting Xray..."
xray -config /etc/xray/config.json &
XRAY_PID=$!

echo "[+] Starting Stats API..."
python3 /app/stats_api.py &
STATS_PID=$!

echo "[+] Waiting for services..."
sleep 2

# Sanity check
if ! kill -0 $XRAY_PID 2>/dev/null; then
    echo "[!] Xray died — check config.json"
    exit 1
fi

echo "[+] Xray PID: $XRAY_PID"
echo "[+] Stats API PID: $STATS_PID"
echo "[+] Starting nginx on :$PORT"

nginx -g 'daemon off;'
