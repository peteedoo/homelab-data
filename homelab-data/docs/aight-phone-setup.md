# Aight App ↔ OpenClaw Server Setup

**Server:** iamfaulty-mini (Mac mini M4)  
**Tailscale:** `iamfaulty-mini-1.tailc0ac22.ts.net` (100.72.92.77)  
**LAN IP:** `192.168.68.84` (for same-WiFi QR scan)  
**Gateway Port:** 18789  
**Gateway Bind:** `lan` (accepts Tailscale + local connections)  
**Tailscale Serve:** OFF (direct connection)  
**Last Updated:** 2026-05-21

---

## What Changed

- **Archived bingsby** BlueBubbles account → `~/.openclaw/archive/bingsby-bluebubbles.json`
- **Disabled BlueBubbles channel** entirely — no more SMS/iMessage routing
- **Cleared all bindings** — no automatic agent routing from channels
- **Switched to device-pair + aight-utils** — phone talks directly to OpenClaw over Tailscale

---

## How It Works Now

```
┌─────────────┐         ┌─────────────────────────────┐
│  Aight App  │◄──WS───►│  OpenClaw Gateway (mini)    │
│  (your iPhone)│        │  Port 18789, bind: lan      │
└─────────────┘         │  Tailscale: 100.72.92.77    │
                        └─────────────────────────────┘
```

- Phone connects via WebSocket to `ws://iamfaulty-mini-1.tailc0ac22.ts.net:18789`
- No BlueBubbles, no webhooks, no SMS relay
- Push notifications via aight-utils → push-relay (CF Worker) → APNs

---

## Phone Setup Steps

### 1. Install Aight App

Get it from the App Store (or TestFlight if beta).

### 2. Pair with Your Gateway

**Option A: Same WiFi (QR scan)**
- On the Mac mini, run:
  ```bash
  openclaw qr
  ```
- Scan the QR code from Aight onboarding
- Approve the device:
  ```bash
  openclaw devices approve <requestId>
  ```

**Option B: Tailscale (any network)**
- Open Aight
- Tap "Add Gateway" → "Enter Manually"
- **URL:** `ws://iamfaulty-mini-1.tailc0ac22.ts.net:18789`
- **Token:** `CXOYdjB92ddRBO140ENq7kFuMEQPQyhhsib8sHeefeo`
- Approve the device from the Mac mini (see Option A)

**Option C: Auto-discover (same WiFi only)**
- Open Aight
- Tap "Add Gateway"
- It should auto-discover `iamfaulty-mini` on the LAN

### 3. Enable Push Notifications

- In Aight: tap your gateway → "Enable Notifications"
- This registers your device token with the aight-utils plugin
- Verify: check `~/.openclaw/aight/devices.json` on the server

### 4. Verify Connection

In Aight, send a message to your `main` agent (Faulty). You should get a response.

---

## Server-Side Verification

```bash
# Check gateway is listening on all interfaces
lsof -i :18789

# Check Tailscale is up
tailscale status

# View registered devices
cat ~/.openclaw/aight/devices.json

# View Today items
cat ~/.openclaw/aight/items.json

# Restart OpenClaw if needed
openclaw restart
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cannot connect to gateway" | Is Tailscale connected on both devices? `tailscale status` |
| No push notifications | Check `devices.json` has your token. Re-enable in Aight settings. |
| Gateway not listening on LAN | Check `bind: lan` in config. Try `bind: 0.0.0.0` if needed. |
| Aight can't find gateway | Use manual URL entry with Tailscale DNS name |

---

## Security Notes

- Token auth is enabled (`mode: token`)
- `allowTailscale: true` — Tailscale IPs bypass some checks
- No BlueBubbles = no SMS/iMessage exposure
- Only devices you explicitly pair can connect
- devices.json and items.json are `0o700` (owner-only)

---

## Rollback

If you need to restore bingsby:

```bash
# Merge archive back (manual — review first)
cat ~/.openclaw/archive/bingsby-bluebubbles.json
```

Or restore from backup:

```bash
cp ~/.openclaw/openclaw.json.bak.20260521-132107 ~/.openclaw/openclaw.json
```
