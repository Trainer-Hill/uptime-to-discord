# uptime-to-discord

A lightweight, cron-based service that checks the health of your websites and sends downtime alerts directly to Discord via webhooks.  
Runs inside Docker with a configurable schedule and minimal setup.

---

## ✨ Features

- ✅ Monitor multiple URLs via environment variables or a simple file
- ✅ Dockerized with cron scheduling
- ✅ Sends clean Discord embeds with failure reasons & latency
- ✅ Silent when everything is healthy
- ✅ Lightweight (Python + cron)

---

## 🚀 Quick Start

### 1. Clone & Build

```bash
git clone https://github.com/YOURNAME/uptime-to-discord.git
cd uptime-to-discord
docker build -t uptime-to-discord .
````

### 2. Run with URLs file

Put your endpoints in `urls.txt` (one per line):

```txt
https://example.com/health
https://status.example.org/ping
```

Start the container:

```bash
docker run -d \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxx/yyy" \
  -e ENV_NAME="prod" \
  -e CRON_SCHEDULE="*/5 * * * *" \
  -v "$(pwd)/urls.txt:/app/urls.txt:ro" \
  --name uptime-to-discord uptime-to-discord
```

### 3. Or use environment variable

```bash
docker run -d \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxx/yyy" \
  -e ENV_NAME="staging" \
  -e HEALTHCHECK_URLS=$'https://example.com/health\nhttps://example.org/ping' \
  -e CRON_SCHEDULE="*/2 * * * *" \
  --name uptime-to-discord uptime-to-discord
```

---

## ⚙️ Configuration

| Variable              | Required | Default         | Description                                             |
| --------------------- | -------- | --------------- | ------------------------------------------------------- |
| `DISCORD_WEBHOOK_URL` | ✅        | –               | Discord webhook URL for sending alerts                  |
| `ENV_NAME`            | ❌        | `unknown`       | Label to identify the environment (prod, staging, etc.) |
| `HEALTHCHECK_URLS`    | ❌        | –               | List of URLs to check (newline/comma/space separated)   |
| `URLS_FILE`           | ❌        | `/app/urls.txt` | Path to file containing URLs (one per line)             |
| `CRON_SCHEDULE`       | ❌        | `*/5 * * * *`   | Cron expression for check frequency                     |
---

## 📝 Example Alert

When a failure is detected, the bot sends an embed like:

```text
🚨 URL Health Check: FAIL
2/5 endpoints failing in **prod**
Host: myserver · 2025-09-08 12:34:56 UTC
❌ example.com
https://example.com/health
• Reason: HTTP 500
• Latency: 245 ms
```

---

## 🛠 Development

Run locally with Python:

```bash
pip install -r requirements.txt
python monitor.py
```

---

## 📜 License

This project is licensed under the **MIT License**.
You are free to use, modify, and distribute it with minimal restrictions.

---
