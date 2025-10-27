# Configuration Reference

Progressista reads environment variables at startup so you can tune behaviour
without touching code. The tables below list every supported knob together with
its default taken from `progressista.settings`.

## Server environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `PROGRESSISTA_HOST` | `0.0.0.0` | Interface the FastAPI server binds to. |
| `PROGRESSISTA_PORT` | `8000` | TCP port for incoming HTTP/WebSocket traffic. |
| `PROGRESSISTA_STORAGE_PATH` | (unset) | JSON file used to persist task snapshots across restarts. Leave unset to keep state in-memory only. |
| `PROGRESSISTA_CLEANUP_INTERVAL` | `5.0` | Seconds between housekeeping runs that evict closed or expired tasks. |
| `PROGRESSISTA_RETENTION_SECONDS` | `86400.0` | How long closed tasks stay visible before being deleted automatically. |
| `PROGRESSISTA_STALE_SECONDS` | `0.0` | Mark active tasks as `stale` after this many idle seconds; `0` disables the feature. |
| `PROGRESSISTA_MAX_TASK_AGE` | `0.0` | Drop tasks older than this many seconds regardless of status; `0` keeps them indefinitely. |
| `PROGRESSISTA_ALLOW_ORIGINS` | (empty) | Optional comma-separated list of origins allowed via CORS. |
| `PROGRESSISTA_API_TOKEN` | (empty) | Single bearer token accepted for `/progress`, `/tasks`, and `/ws`. |
| `PROGRESSISTA_API_TOKENS` | (empty) | Comma-separated set of bearer tokens. When set it overrides `PROGRESSISTA_API_TOKEN`. |

## Client environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `PROGRESSISTA_SERVER_URL` | `http://localhost:8000/progress` | Endpoint that receives progress payloads from `RemoteTqdm`. |
| `PROGRESSISTA_PUSH_INTERVAL` | `0.25` | Minimum seconds between HTTP posts made by `RemoteTqdm`. |
| `PROGRESSISTA_REQUEST_TIMEOUT` | `2.0` | Timeout in seconds for client HTTP requests. |
| `PROGRESSISTA_API_TOKEN` | (empty) | Optional bearer token attached to outbound requests; must match the server configuration. |

The CLI mirrors these settings with options (for example,
`progressista serve --host 127.0.0.1`) and command-line values override the
environment for that invocation. For reproducible deployments capture the
desired values in `.env` files, systemd units, or container manifests and point
`PROGRESSISTA_STORAGE_PATH` at a persistent volume if dashboard state must
survive restarts.
