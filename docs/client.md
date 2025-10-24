# Client Guide

The `progressista.client.RemoteTqdm` class subclasses `tqdm` so it can be used as
a direct replacement. It mirrors the display configuration of your bars but also
pushes structured updates to the Progressista server.

## Basic usage

```python
from time import sleep
from progressista import RemoteTqdm

for _ in RemoteTqdm(range(200), desc="Ingesting", unit="records"):
    sleep(0.05)
```

`RemoteTqdm` accepts the same positional arguments as `tqdm`. Extra keyword
arguments control the remote behaviour:

| Parameter | Default | Description |
| --- | --- | --- |
| `server_url` | `PROGRESSISTA_SERVER_URL` or `http://localhost:8000/progress` | Where to POST updates. |
| `task_id` | Hostname + timestamp + object id | Unique identifier for this bar. |
| `push_every` | `PROGRESSISTA_PUSH_INTERVAL` or `0.25` | Minimum seconds between HTTP posts. |
| `unit` | Derived from `tqdm.unit` | Override display unit and remote payload. |
| `request_timeout` | `PROGRESSISTA_REQUEST_TIMEOUT` or `2.0` | HTTP timeout in seconds. |
| `meta` | `None` | Optional dictionary serialised alongside updates. |
| `headers` | Derived from environment defaults | Extra HTTP headers (e.g. bearer tokens). |

Updates are sent asynchronously via a background thread. The thread keeps the
latest payload and discards intermediate ones inside the throttle window so your
loops do not block.

## Integrating with multiprocessing

When multiple workers emit updates concurrently, give each one a stable
`task_id` that encodes their role:

```python
RemoteTqdm(total=10_000, task_id=f"run-{run_id}:rank-{rank}")
```

The dashboard sorts by `updated_at` so the most recently active tasks stay on
top.

## Retrofitting existing scripts

You can patch every `import tqdm` in a process without changing the source:

```bash
progressista run path/to/script.py -- --script-flags
progressista run -m package.module -- --module-flags
```

`progressista run` installs the monkey patch, forwards remaining arguments, and
executes the target script/module in-place so the original console or notebook
progress bars still render.

For long-lived environments (e.g. Jupyter, Airflow workers) add this to a
`sitecustomize.py` that lives on `PYTHONPATH`:

```python
from progressista.patch import install

install(server_url="https://progress.example.com/progress")
```

The patch covers `tqdm`, `tqdm.auto`, and notebook variants.

When the server enforces tokens, configure the client environment:

```bash
export PROGRESSISTA_API_TOKEN="super-secret"
progressista run script.py
```

The `RemoteTqdm` class uses `Authorization: Bearer ...` automatically; custom
headers can be passed as `RemoteTqdm(..., headers={"Authorization": "Bearer ..."})`.
For the browser dashboard, open `http://host/static/index.html?token=super-secret`
so the WebSocket connection can authenticate too.

## Managing stale or completed tasks

- When `PROGRESSISTA_STALE_SECONDS` is set, tasks with no activity slide into a
  “Needs Attention” column in the dashboard. Call `RemoteTqdm.close()` to move
  them into the completed list.
- Use the REST helpers for automation: `DELETE /tasks/{task_id}` removes a
  specific bar, while `DELETE /tasks?status=close` clears all completed items.
  Include your bearer token if auth is enabled.

## Error handling

Network failures are intentionally silent — `RemoteTqdm` swallows exceptions so
your job can continue even if the monitoring server is unreachable. Consider
adding your own observers (e.g. logging errors) by subclassing `RemoteTqdm` and
overriding `_post`.

## Custom payloads

Use the `meta` argument to attach additional context that the server and
dashboard preserve. For example:

```python
RemoteTqdm(total=500, desc="Embedding", meta={"model": "all-MiniLM", "run_id": run_id})
```

The JSON snapshot delivered to the dashboard will include this `meta` section,
which you can leverage in a custom UI.
