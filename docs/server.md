# Server Guide

The Progressista server is a FastAPI application that accepts JSON progress
events and relays state changes to the browser dashboard over WebSockets.

## Running the server

```
progressista serve --host 0.0.0.0 --port 8000
```

Extra flags (or environment variables) let you tailor behaviour:

| Option | Environment | Default | Description |
| --- | --- | --- | --- |
| `--host` | `PROGRESSISTA_HOST` | `0.0.0.0` | Interface to bind. |
| `--port` | `PROGRESSISTA_PORT` | `8000` | Port to listen on. |
| — | `PROGRESSISTA_STORAGE_PATH` | (unset) | Absolute or relative path for persisted task snapshots. |
| `--retention-seconds` | `PROGRESSISTA_RETENTION_SECONDS` | `86400` | How long to keep closed tasks before purging. |
| `--cleanup-interval` | `PROGRESSISTA_CLEANUP_INTERVAL` | `5` | Seconds between cleanup runs. |
| `--allow-origins` | `PROGRESSISTA_ALLOW_ORIGINS` | (empty) | Comma separated CORS allow-list. |
| — | `PROGRESSISTA_STALE_SECONDS` | `0` | Mark active tasks as `stale` after this many idle seconds (`0` disables). |
| — | `PROGRESSISTA_MAX_TASK_AGE` | `0` | Drop tasks older than this many seconds regardless of status (`0` disables). |
| — | `PROGRESSISTA_API_TOKEN` | (empty) | Single bearer token accepted for writes and dashboard access. |
| — | `PROGRESSISTA_API_TOKENS` | (empty) | Comma separated set of valid bearer tokens (overrides `PROGRESSISTA_API_TOKEN`). |

Example with authentication via reverse proxy:

```
PROGRESSISTA_ALLOW_ORIGINS="https://dash.example.com" \
PROGRESSISTA_RETENTION_SECONDS=300 \
PROGRESSISTA_API_TOKEN="super-secret" \
progressista serve --host 127.0.0.1 --port 9000
```

Set `PROGRESSISTA_STORAGE_PATH` to a writable JSON file (for example
`/var/lib/progressista/state.json`) when you need dashboards to survive restarts.
Review [Configuration](configuration.md) for a complete list of server and
client knobs.

Expose the dashboard by fronting the server with nginx/Traefik/Caddy and proxy
both `/progress` and `/ws`.

## API surface

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/progress` | Accepts `ProgressEvent` payloads and updates task state. |
| `GET` | `/tasks` | Returns the full task snapshot as JSON. |
| `GET` | `/health` | Health probe with current task count. |
| `WS` | `/ws` | Pushes task snapshots after every update. |
| `GET` | `/static/index.html` | Default dashboard. |
| `DELETE` | `/tasks/{task_id}` | Remove a single task (requires token if configured). |
| `DELETE` | `/tasks?status=close` | Bulk remove matching tasks (`status` and `older_than` supported). |

`/progress` expects a JSON body with fields:

```json
{
  "task_id": "job-123",
  "desc": "Loading data",
  "total": 100,
  "n": 42,
  "unit": "it",
  "status": "update"
}
```

Missing values are preserved from the previous event, so the client can send
partial updates.

Use the bulk deletion endpoint to maintain hygiene in dashboards or scheduled
jobs. Example: `DELETE /tasks?status=stale&older_than=600` removes stale bars
that have been idle for over ten minutes.

## Deployment checklist

- ☁️ **Containerize** — package with `uvicorn` and run under gunicorn/uvicorn
  workers; set `workers > 1` only if you switch to an external state store.
- 🔒 **Security** — restrict access to `/progress` via network policies, proxy
  authentication, or simple shared secrets (e.g. check an `Authorization`
  header). Extend `progressista.server` to enforce custom logic.
- 🔄 **Durability** — by default, state is in-memory. Configure supervised
  restarts or adapt the code to write to Redis/Postgres when persistence matters.
- 📈 **Observability** — integrate with your metrics stack by adapting
  `progressista.server.broadcast` to emit counters or logs.
- 🧹 **Lifecycle tuning** — set `PROGRESSISTA_STALE_SECONDS` so idle tasks slide
  into a “stale” bucket in the UI; set `PROGRESSISTA_MAX_TASK_AGE` to purge
  ancient bars automatically.

## Security quick facts

- When tokens are configured the server rejects `/progress` requests without
  `Authorization: Bearer <token>`.
- WebSocket dashboard connections must include the same token either via the
  header or by loading the dashboard as `https://host/static/index.html?token=<token>`.
- Combine tokens with TLS termination and network guards from your chosen host.
