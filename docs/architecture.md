# Progressista Architecture

Progressista is intentionally small: a lightweight FastAPI application stores
progress state in memory and broadcasts updates to connected dashboards over a
WebSocket. Python workers use a `tqdm` subclass (`RemoteTqdm`) that mirrors the
progress updates they would normally render in the console.

```
┌────────────┐      HTTP POST       ┌──────────────────┐   websocket    ┌───────────┐
│ RemoteTqdm │ ───────────────────▶ │ FastAPI /progress│ ──────────────▶ │ Dashboard │
└────────────┘                      └──────────────────┘                └───────────┘
        ▲                                  │
        │                                  ▼
        └───────────── in-memory task state ──────────────┐
                                                          │
                                                     cleanup loop
```

## Key components

- **Client (`progressista.client.RemoteTqdm`)** — wraps every `update()` and
  `close()` call to enqueue JSON payloads. A background thread batches and
  throttles HTTP POST requests to the server.
- **Patching utilities (`progressista.patch`)** — optional monkey patch for
  existing code bases so every `tqdm` import becomes remote-aware without source
  changes.

- **Server (`progressista.server`)** — implements the `/progress` endpoint and a
  `/ws` WebSocket. The server maintains a dictionary of tasks keyed by `task_id`
  and broadcasts the latest snapshot after every update. A background cleanup
  loop removes completed tasks after the configured retention window, marks idle
  items as `stale`, and respects optional max-age policies.

- **Dashboard (`progressista/static/index.html`)** — a static HTML/JS front-end
  that listens to WebSocket messages, surfaces active/stale/completed columns,
  and exposes discard controls for quick triage.

## Data model

Every event posted by the client follows the `ProgressEvent` schema:

```json
{
  "task_id": "etl:stage-1",
  "desc": "Processing batch 1",
  "n": 12,
  "total": 100,
  "unit": "it",
  "status": "update",
  "timestamp": 1710078346.585749,
  "meta": {
    "job_id": "run-42"
  }
}
```

The server keeps a normalized task representation that includes derived fields
such as `updated_at` and `created_at`. Connected dashboards receive the entire
`{"tasks": {...}}` snapshot whenever anything changes.

## Lifecycle

1. `RemoteTqdm` starts and sends a `status="start"` event.
2. Each call to `update()` adds to a queue. The worker thread collapses events so
   that it only sends the latest state every `push_every` seconds.
3. The FastAPI `/progress` endpoint persists the task and the server broadcasts
   the updated snapshot to WebSocket clients.
4. When `close()` runs, a final `status="close"` event is emitted. Completed
   tasks stay visible for `retention_seconds` before cleanup.
5. Cleanup removes closed tasks and triggers another broadcast, so dashboards
   drop them from the UI automatically.

## Extensibility options

- **Durability** — swap the in-memory dictionary with Redis by adjusting
  `progressista.server`. The rest of the code expects a mapping-like interface.
- **Auth** — add FastAPI dependencies that check headers (e.g. bearer tokens) or
  source IP addresses before accepting `/progress` events.
- **Metrics** — expose Prometheus metrics or push aggregated progress to an
  observability stack by hooking into the same broadcast logic.
- **Custom UI** — build your own SPA and point it at `/ws`; or read `/tasks`
  periodically if WebSockets are not available.
