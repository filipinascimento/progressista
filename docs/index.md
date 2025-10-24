# Progressista

Progressista streams `tqdm` progress bars to a lightweight FastAPI gateway so that long‑running jobs can be monitored from any browser. Replace local bars with a drop‑in subclass, or wrap existing scripts with a CLI helper that patches imports on the fly.

## Features

- Remote-first `RemoteTqdm` implementation that mirrors the local bar while sending updates to a server
- FastAPI backend with a live WebSocket dashboard for active, stale, and completed tasks
- Typer-powered CLI with `serve`, `demo`, and `run` entry points
- Optional bearer-token authentication and configurable cleanup windows
- MkDocs documentation and GitHub Actions workflows ready for CI/CD

## Quick start

```bash
pip install progressista

# Start the FastAPI gateway
progressista serve --host 0.0.0.0 --port 8000

# Send sample bars
progressista demo --bars 3 --total 80
```

Or retrofit existing scripts without code changes:

```bash
progressista run your_script.py -- --arg value
```

## Development workflow

```bash
pip install -e .[dev]
make test        # pytest suite
make docs        # mkdocs build --strict
make version     # show VCS-derived version
```

The release pipeline relies on `scripts/get_version.py` and `scripts/sync_version.py` to keep `pyproject.toml` and `progressista/__init__.py` in sync with Git tags.

## Learn more

- [Architecture](architecture.md)
- [Server runtime](server.md)
- [Client integration](client.md)
- [Runbook](runbook.md)
- [Hosting ideas](hosting.md)
