# Agent & Bot Registry

Last updated: 2026-05-26

## Active Agents

| Agent | Platform | Bot Username | Purpose | Model | Status |
|-------|----------|--------------|---------|-------|--------|
| **Hermes** | Discord + Telegram | `@JoejoejoebotJoejoejoebot` (first name: "Bottack") | General assistant, cron jobs, daily briefings | kimi-k2.6 via kimi-coding | ✅ Active |
| **Faulty** (OpenClaw) | Telegram | `@Macadellicshakurbot` | OpenClaw gateway agent | kimi/kimi-for-coding | ✅ Fixed 2026-05-26 |

## Dormant Agents

| Agent | Location | Status |
|-------|----------|--------|
| **Bingsby** | `~/.openclaw/agents/bingsby/` | 💤 Inactive |

## Configuration Files

### Hermes
- Config: `~/.hermes/config.yaml`
- Env: `~/.hermes/.env`
- Telegram token: `8635117148:AAGnCWv3UXy3Y7gVfjtBFlvJD5WHgE16G18`
- Telegram chat ID: `8608684707` (Petee's DM)

### OpenClaw / Faulty
- Config: `~/.openclaw/openclaw.json`
- Agent config: `~/.openclaw/agents/main/agent/agent.json`
- Auth profiles: `~/.openclaw/auth-profiles.json`
- Telegram token: `8563280408` (fingerprint: `92be32547b667c78`)
- Model: `kimi/kimi-for-coding` (primary), fallbacks include `openrouter/auto`, `ollama/gemma4:4b`

## Cron Jobs

| Job | Script | Output | Telegram |
|-----|--------|--------|----------|
| `pharrell-rocky-daily-briefing` | `~/homelab-data/dropbox/daily-briefing.sh` | `~/homelab-data/dropbox/briefings/daily-briefing-YYYY-MM-DD.md` | ✅ Sends to `@JoejoejoebotJoejoejoebot` |

## Known Issues & Fixes

### 2026-05-26: OpenClaw model stuck on `qwen/qwen3-coder:free`
- **Root cause:** `agents.defaults.model.primary` in OpenClaw config was set to `openrouter/qwen/qwen3-coder:free`
- **Fix:** `openclaw config set agents.defaults.model.primary "kimi/kimi-for-coding"` then restart gateway
- **Note:** Multiple config layers exist — `agents.defaults.model.primary`, `agents.list[0].model`, `agent.json`, `sessions.json`. The defaults config was the stale override.

### 2026-05-26: Daily briefing not sending to Telegram
- **Root cause:** Script checked for `TELEGRAM_CHAT_ID` but env var is `TELEGRAM_HOME_CHANNEL`
- **Fix:** Patched `daily-briefing.sh` lines 145, 148 to use `TELEGRAM_HOME_CHANNEL`

## Quick Commands

```bash
# Check OpenClaw gateway logs
openclaw logs --limit 50 --no-color

# Restart OpenClaw gateway
openclaw gateway stop && openclaw gateway start

# Check OpenClaw model config
openclaw config get agents.defaults.model

# Check Hermes config
cat ~/.hermes/config.yaml | head -20

# Test Telegram bot
curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | python3 -m json.tool
```
