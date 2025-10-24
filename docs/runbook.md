# Runbook & Troubleshooting

## Common operations

- **Start locally**: `progressista serve`
- **View dashboard**: open `http://HOST:PORT/static/index.html`
- **Tail logs**: run the server with `uvicorn --log-level debug progressista.server:create_app`
- **Send test data**: `progressista demo --bars 2 --total 20`
- **Retrofit scripts**: `progressista run script.py -- --flags`
- **Require tokens**: `PROGRESSISTA_API_TOKEN=secret progressista serve`
- **Mark stale**: `PROGRESSISTA_STALE_SECONDS=300 progressista serve`
- **Auto-expire anything**: `PROGRESSISTA_MAX_TASK_AGE=3600 progressista serve`

## Monitoring checklist

- Monitor CPU/memory of the process; each task is a small dictionary and the
  cleanup loop prevents unbounded growth once jobs finish.
- The `/health` endpoint returns a simple JSON payload with the number of active
  tasks — probe it from load balancers or uptime checks.
- If you expose the dashboard publicly, enable TLS and authenticate clients via
  a reverse proxy; Progressista deliberately omits built-in auth to stay simple.

## Troubleshooting

| Symptom | Suggestion |
| --- | --- |
| Dashboard shows “Disconnected” | Ensure `/ws` is reachable (proxy websockets correctly). |
| Tasks never appear | Verify the client `server_url` matches `/progress` and that the server logs requests. |
| Tasks linger forever | Adjust `PROGRESSISTA_RETENTION_SECONDS`, set `PROGRESSISTA_MAX_TASK_AGE`, or call `DELETE /tasks?status=close`. |
| High request volume | Increase `push_every` to reduce POST frequency. |
| Mixed environments (HTTP/HTTPS) | Serve behind TLS so that the dashboard can establish a secure WebSocket (`wss://`). |
| 401 Unauthorized | Ensure clients send `Authorization: Bearer <token>` or open the dashboard with `?token=` query. |

## Extending safely

- Add middleware or dependencies in `progressista.server.create_app` to enforce
  authentication or request validation.
- Swap the in-memory store for Redis by replacing the dictionary with a
  lightweight repository class. Broadcast the same payload shape to keep the UI
  happy.
- Integrate with job schedulers by wrapping `RemoteTqdm` and attaching metadata
  (e.g. job IDs, node names) via the `meta` argument.

## Support matrix

| Component | Version |
| --- | --- |
| Python | 3.9+ |
| FastAPI | 0.110+ |
| browsers | Latest Chrome, Firefox, Safari, Edge (tested on evergreen releases) |

## FAQ

**Does it work without WebSockets?**  
Yes — poll `/tasks` periodically if you cannot maintain a WebSocket. The
dashboard implementation is in plain JS so you can extend or replace it easily.

**Can I persist state across restarts?**  
Not yet. The simplest integration point is the shared `broadcast` helper in
`progressista.server`; replace the dictionary with your datastore.

**How do I secure it?**  
Run behind VPN, add network ACLs, or apply FastAPI dependencies that validate an
API token on incoming requests.
