# Progressista

Progressista is a tiny “push gateway” for progress bars. Swap your existing `tqdm`
instances with a drop-in subclass that streams progress updates to a FastAPI
server. The server keeps tasks in memory and serves a live HTML dashboard over
WebSocket so you can monitor many worker bars from a single browser tab.

> **Why?** When long-running experiments or ETL jobs run on remote machines you
> often lose the nice `tqdm` progress output. Progressista lets you restore that
> feedback loop without SSH-ing into every node.

## Features

- ⚡️ Drop-in `RemoteTqdm` replacement for `tqdm`.
- 🌐 Live dashboard powered by FastAPI and WebSockets.
- 🧰 Simple CLI: `progressista serve` and `progressista demo`.
- 🪄 Seamless retrofits via `progressista run` or `sitecustomize` patching.
- 🔧 Configurable server URL via CLI flags or environment variables.
- 🗂️ Dashboard buckets for active/stale/completed tasks with one-click cleanup.
- 🔐 Optional CORS allow-list for remote dashboards.
- 🧹 Automatic cleanup of completed tasks with configurable retention.

## Quick start

```bash
# 1. Install locally (requires Python 3.9+)
pip install -e .

# 2. Run the server
progressista serve --host 0.0.0.0 --port 8000

# 3. Open the dashboard
open http://localhost:8000/static/index.html

# 4. Send progress from Python code
python - <<'PY'
from time import sleep
from progressista import RemoteTqdm

for _ in RemoteTqdm(range(100), desc="Demo workload"):
    sleep(0.05)
PY
```

Or use the built-in demo generator:

```bash
progressista demo --bars 4 --total 80 --delay 0.1
```

## Using `RemoteTqdm`

```python
from time import sleep
from progressista import RemoteTqdm

# Point to your server (defaults to http://localhost:8000/progress)
for _ in RemoteTqdm(range(100), desc="ETL: stage 1", unit="it"):
    sleep(0.05)
```

Multiple bars? Just give each one a `task_id`:

```python
workers = [
    RemoteTqdm(total=50, desc=f"worker {i}", task_id=f"job-x:worker-{i}")
    for i in range(3)
]

for _ in range(50):
    for bar in workers:
        bar.update(1)
    sleep(0.05)

for bar in workers:
    bar.close()
```

## Use without modifying existing scripts

- Run any script through Progressista without touching its source:

  ```bash
  progressista run your_script.py -- --arg1 value
  progressista run -m package.module -- --flag
  progressista run your_script.py --server-url https://example.com/progress -- --arg
  ```

  All imports of `tqdm` (including `from tqdm.auto import tqdm`) become remote-aware, while the original terminal or notebook rendering stays intact.

- Need this automatically? Drop the following `sitecustomize.py` on your `PYTHONPATH`:

  ```python
  from progressista.patch import install

  install()  # accepts server_url=..., headers=..., etc.
  ```

  Python imports `sitecustomize` before your program starts, so every script inherits the patch.

## Dashboard controls

- Active tasks stay in the main lane. When a bar stops reporting for more than
  `PROGRESSISTA_STALE_SECONDS` (if set), it moves to the **Needs Attention** pile.
- Closed bars land under **Completed** and only the most recent six stay visible
  so the list stays compact.
- Use the toolbar to clear all completed or stale tasks, or discard individual
  cards via the button on each tile. All actions replicate instantly across
  connected browsers.

## Configuration

Progressista reads optional environment variables so you can configure it in
Docker images, systemd units, or cloud runners:

| Variable | Description | Default |
| --- | --- | --- |
| `PROGRESSISTA_HOST` | Interface for the server to bind | `0.0.0.0` |
| `PROGRESSISTA_PORT` | Port used by `progressista serve` | `8000` |
| `PROGRESSISTA_ALLOW_ORIGINS` | Comma-separated CORS origins | disabled |
| `PROGRESSISTA_RETENTION_SECONDS` | Keep closed tasks visible for (s) | `120` |
| `PROGRESSISTA_CLEANUP_INTERVAL` | Cleanup frequency (s) | `5` |
| `PROGRESSISTA_SERVER_URL` | Default client post URL | `http://localhost:8000/progress` |
| `PROGRESSISTA_PUSH_INTERVAL` | Client throttle window in seconds | `0.25` |
| `PROGRESSISTA_REQUEST_TIMEOUT` | HTTP timeout in seconds | `2.0` |
| `PROGRESSISTA_API_TOKEN` | Shared bearer token for server & client | unset |
| `PROGRESSISTA_API_TOKENS` | Comma-separated list of valid tokens | unset |
| `PROGRESSISTA_STALE_SECONDS` | Mark tasks as `stale` after this many idle seconds (`0` disables) | `0` |
| `PROGRESSISTA_MAX_TASK_AGE` | Automatically discard tasks older than this many seconds (`0` disables) | `0` |

All CLI options override the corresponding environment variable for the current
invocation.

## Packaging

- `progressista.server` exposes `create_app` (FastAPI factory) and `run_server`
  utility if you want to embed the app elsewhere.
- `progressista.client.RemoteTqdm` gives programmatic access to the client.
- `progressista.cli` provides the Typer-based commands used by the entry point.
- Version strings live in `progressista/__init__.py` and are managed by Hatch
  (`[tool.hatch.version]`). Use `make sync-version TAG=vX.Y.Z` before tagging a release.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make test
make docs
make version  # prints the git-derived version
```

## Documentation

Additional docs live in [`docs/`](docs/):

- MkDocs site: https://filipinascimento.github.io/progressista/
- Run `make docs-serve` for a live preview (`mkdocs serve`).
- [`docs/architecture.md`](docs/architecture.md) — system design and data flow.
- [`docs/server.md`](docs/server.md) — FastAPI endpoints and configuration.
- [`docs/client.md`](docs/client.md) — client API and integration notes.
- [`docs/runbook.md`](docs/runbook.md) — deployment tips and troubleshooting.
- [`docs/hosting.md`](docs/hosting.md) — free-tier hosting options and deployment tips.

## Security

- Set a shared token on both server and clients:

  ```bash
  export PROGRESSISTA_API_TOKEN="super-secret"
  progressista serve
  ```

  Clients pick it up automatically (via environment variable) or you can pass it explicitly:

  ```bash
  PROGRESSISTA_API_TOKEN=super-secret python your_script.py
  # or
  progressista run script.py --api-token super-secret
  ```

- Requests must include an `Authorization: Bearer ...` header; open the dashboard as `http://host/static/index.html?token=super-secret` so the WebSocket connection inherits the same key.

- Want per-user credentials? Set `PROGRESSISTA_API_TOKENS="alpha,beta"` on the server and hand out individual strings.

## License

MIT — see [LICENSE](LICENSE).
