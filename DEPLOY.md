# Danmarks Statistik MCP Server — Remote Deployment Guide

This is a remote-ready version of the Danmarks Statistik MCP server, configured for deployment as a hosted service that connects to **Claude.ai web version** via Integrations.

## What this does

The server exposes Danmarks Statistik's Statistikbank API as MCP tools. Once deployed and connected to Claude.ai, users can ask questions like:
- "Hvor mange mennesker bor der i København?"
- "Hvilken kommune har haft det største fald i indbyggere?"

## Architecture

```
Claude.ai (web) ──HTTPS──▶ Your hosted server ──HTTP──▶ api.statbank.dk
```

The server uses **Streamable HTTP** transport (the recommended MCP remote transport as of 2026). No authentication is needed for the DST API — it's publicly accessible.

---

## Quick start (local testing)

```bash
# Option A: Python directly
pip install -r requirements.txt
python server.py
# Server runs at http://localhost:8000/mcp

# Option B: Docker
docker compose up --build
# Server runs at http://localhost:8000/mcp
```

Verify it's running:
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

---

## Deploy to production

The server needs to be publicly accessible via HTTPS. Choose one of:

### Option 1: Railway (easiest)
1. Go to [railway.app](https://railway.app), create new project → Deploy from GitHub repo (`wdkmp/mcp-dst-remote`)
2. Railway auto-detects the Dockerfile — no config needed
3. The server automatically reads Railway's `$PORT` variable, so it just works
4. You get a public URL like `https://mcp-dst-xxxxx.up.railway.app`

### Option 2: Render
1. Go to [render.com](https://render.com), create new Web Service → connect repo (`wdkmp/mcp-dst-remote`)
2. Render auto-detects Docker — no config needed
3. The server automatically reads Render's `$PORT` variable, so it just works
4. You get a URL like `https://mcp-dst.onrender.com`

### Option 3: Fly.io
```bash
fly launch          # Creates fly.toml from Dockerfile
fly deploy          # Deploys
fly status          # Shows the public URL
```

### Option 4: Any VPS / cloud VM
```bash
docker compose up -d --build
```
Then put it behind a reverse proxy (nginx/caddy) with HTTPS.

---

## Connect to Claude.ai

Once deployed and you have a public HTTPS URL:

1. Go to [claude.ai](https://claude.ai) (requires Pro, Max, Team, or Enterprise plan)
2. Click your profile icon → **Settings**
3. Go to **Integrations** (in the left sidebar)
4. Click **Add Integration**
5. Enter the MCP server URL:
   - For Streamable HTTP: `https://your-domain.com/mcp`
   - For SSE (if using `MCP_TRANSPORT=sse`): `https://your-domain.com/sse`
6. Save — the Danmarks Statistik tools should now appear in Claude.ai

---

## Environment variables

| Variable        | Default             | Description                           |
|-----------------|---------------------|---------------------------------------|
| `PORT`          | `8000`              | Port to listen on (auto-set by Railway/Render/Fly.io) |
| `MCP_HOST`      | `0.0.0.0`           | Bind address                          |
| `MCP_TRANSPORT` | `streamable-http`   | Transport: `streamable-http` or `sse` |

---

## Available MCP tools

| Tool             | Description                                      |
|------------------|--------------------------------------------------|
| `get_subjects`   | Browse subject hierarchy (emner)                 |
| `get_tables`     | List available tables, optionally filtered       |
| `get_table_info` | Get metadata for a specific table (variables)    |
| `get_data`       | Fetch actual data from a table with filters      |

---

## Troubleshooting

- **Claude.ai can't connect:** Ensure the URL is HTTPS (not HTTP) and publicly accessible
- **Timeout errors:** DST API can be slow for large datasets — consider adding a longer timeout in the hosting platform
- **"Integration not available":** MCP integrations require a paid Claude.ai plan (Pro/Max/Team/Enterprise)
- **Transport issues:** If `streamable-http` doesn't work with your hosting setup, try `MCP_TRANSPORT=sse` — some platforms handle SSE more reliably
