#!/bin/bash
set -e
cd "$(dirname "$0")"

# Auto-detect host IP for the Docker network
# On macOS, host.docker.internal doesn't resolve in custom bridge networks
# We find the host's IP on the docker0 bridge or fallback to the gateway IP
GATEWAY_HOST=""

# Try to get the host IP from the docker network gateway
if command -v docker >/dev/null 2>&1; then
  GATEWAY_HOST=$(docker network inspect bridge --format='{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null || true)
fi

# Fallback: try to infer from route or interface
if [[ -z "$GATEWAY_HOST" ]]; then
  # macOS: get the IP of the primary interface
  GATEWAY_HOST=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
fi

# Last resort: use localhost and hope for port forwarding
if [[ -z "$GATEWAY_HOST" ]]; then
  GATEWAY_HOST="host.docker.internal"
  echo "[redeploy] WARNING: Could not auto-detect host IP. Falling back to host.docker.internal"
  echo "[redeploy] If the dashboard can't reach the gateway, set GATEWAY_HOST manually:"
  echo "[redeploy]   GATEWAY_HOST=192.168.x.x ./redeploy.sh"
else
  echo "[redeploy] Auto-detected host IP: $GATEWAY_HOST"
fi

echo "[redeploy] Building image..."
docker build --no-cache -t openclaw-hq:latest .

echo "[redeploy] Recreating container..."
docker stop dashboard 2>/dev/null || true
docker rm dashboard 2>/dev/null || true
docker run -d \
  --name dashboard \
  --restart unless-stopped \
  -p 3004:3004 \
  -v /Users/peteedoo/homelab-data/dashboard:/data \
  -v /Users/peteedoo/.openclaw/openclaw.json:/openclaw.json:ro \
  -v /Users/peteedoo/.openclaw/identity/device.json:/openclaw-identity.json:ro \
  -v /Users/peteedoo/.openclaw/agents/main/sessions:/openclaw-sessions:ro \
  -v /Users/peteedoo/.openclaw/tasks:/openclaw-tasks \
  -v /Users/peteedoo/.openclaw/workspace/memory:/openclaw-memory:ro \
  -e OPENCLAW_CONFIG=/openclaw.json \
  -e OPENCLAW_IDENTITY=/openclaw-identity.json \
  -e OPENCLAW_SESSIONS_DIR=/openclaw-sessions \
  -e OPENCLAW_TASKS_DB=/openclaw-tasks/runs.sqlite \
  -e OPENCLAW_MEMORY_DIR=/openclaw-memory \
  -e DATA_DIR=/data \
  -e PORT=3004 \
  -e NODE_ENV=production \
  -e GATEWAY_HOST="$GATEWAY_HOST" \
  --network proxy \
  --platform linux/arm64 \
  openclaw-hq:latest

echo "[redeploy] Done. Container logs:"
sleep 2 && docker logs dashboard --tail 5
