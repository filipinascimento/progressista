"""Command line entry points for Progressista."""

from __future__ import annotations

import json
import runpy
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

import typer

from . import __version__
from .client import RemoteTqdm
from .patch import install as install_patch
from .server import run_server
from .settings import ClientSettings, ServerSettings

app = typer.Typer(add_completion=False, help="Remote progress dashboards for tqdm.")


@app.callback()
def _main() -> None:
    """Progressista CLI."""


@app.command()
def version() -> None:
    """Print the installed Progressista version."""

    typer.echo(__version__)


@app.command()
def show_config() -> None:
    """Print current server and client configuration."""

    typer.echo(
        json.dumps(
            {
                "server": ServerSettings().__dict__,
                "client": ClientSettings().__dict__,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command()
def serve(
    host: Optional[str] = typer.Option(
        None, help="Host interface to bind to. Overrides PROGRESSISTA_HOST."
    ),
    port: Optional[int] = typer.Option(
        None, help="Port to listen on. Overrides PROGRESSISTA_PORT."
    ),
    retention_seconds: Optional[float] = typer.Option(
        None, help="Retention window for completed tasks."
    ),
    cleanup_interval: Optional[float] = typer.Option(
        None, help="Background cleanup frequency in seconds."
    ),
    allow_origins: Optional[str] = typer.Option(
        None,
        help="Comma-separated list of allowed CORS origins. "
        "Overrides PROGRESSISTA_ALLOW_ORIGINS.",
    ),
) -> None:
    """Run the Progressista FastAPI server."""

    settings = ServerSettings()
    if host is not None:
        settings.host = host
    if port is not None:
        settings.port = port
    if retention_seconds is not None:
        settings.retention_seconds = retention_seconds
    if cleanup_interval is not None:
        settings.cleanup_interval = cleanup_interval
    if allow_origins is not None:
        settings.allow_origins = tuple(o.strip() for o in allow_origins.split(",") if o.strip())

    run_server(settings)


@app.command()
def demo(
    server_url: Optional[str] = typer.Option(
        None,
        help="Progress endpoint for the running server. "
        "Defaults to PROGRESSISTA_SERVER_URL or http://localhost:8000/progress.",
    ),
    bars: int = typer.Option(3, min=1, max=10, help="Number of simultaneous progress bars."),
    total: int = typer.Option(50, min=1, help="Total iterations for each bar."),
    delay: float = typer.Option(0.05, min=0.0, help="Delay between updates in seconds."),
    api_token: Optional[str] = typer.Option(
        None, help="Bearer token included as Authorization header on updates."
    ),
) -> None:
    """Send demonstration progress bars to a running server."""

    typer.echo("Starting demo workload...")
    headers = {"Authorization": f"Bearer {api_token}"} if api_token else None
    active_bars = [
        RemoteTqdm(
            total=total,
            desc=f"worker {i+1}",
            task_id=f"demo:worker:{i+1}",
            server_url=server_url,
            unit="it",
            headers=headers,
        )
        for i in range(bars)
    ]
    try:
        for _ in range(total):
            for bar in active_bars:
                bar.update(1)
            time.sleep(delay)
    finally:
        for bar in active_bars:
            bar.close()
    typer.echo("Demo workload finished.")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(
    ctx: typer.Context,
    target: str = typer.Argument(..., help="Script path or module name to execute."),
    module: bool = typer.Option(False, "--module", "-m", help="Treat target as a module name."),
    server_url: Optional[str] = typer.Option(None, help="Override server URL."),
    push_every: Optional[float] = typer.Option(None, help="Throttle interval in seconds."),
    request_timeout: Optional[float] = typer.Option(None, help="HTTP timeout in seconds."),
    unit: Optional[str] = typer.Option(None, help="Default unit override for all bars."),
    meta: Optional[str] = typer.Option(
        None, help="JSON object attached to every payload via RemoteTqdm(meta=...)."
    ),
    headers: Optional[str] = typer.Option(
        None, help="JSON object with HTTP headers (e.g. Authorization)."
    ),
    api_token: Optional[str] = typer.Option(
        None, help="Convenience flag to set an Authorization Bearer token."
    ),
) -> None:
    """Execute a script with Progressista's tqdm patch installed."""

    header_dict = _loads_json("headers", headers)
    if api_token:
        header_dict = header_dict or {}
        header_dict.setdefault("Authorization", f"Bearer {api_token}")

    defaults = _build_defaults(
        server_url=server_url,
        push_every=push_every,
        request_timeout=request_timeout,
        unit=unit,
        meta=_loads_json("meta", meta),
        headers=header_dict,
    )
    install_patch(**defaults)

    extra_args: List[str] = list(ctx.args)
    if module:
        sys.argv = [target, *extra_args]
        runpy.run_module(target, run_name="__main__", alter_sys=True)
    else:
        script_path = Path(target).expanduser().resolve()
        if not script_path.exists():
            raise typer.BadParameter(f"Script not found: {script_path}")
        sys.argv = [str(script_path), *extra_args]
        runpy.run_path(str(script_path), run_name="__main__")


def _loads_json(name: str, raw: Optional[str]) -> Optional[dict[str, Any]]:
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - user input path
        raise typer.BadParameter(f"Invalid JSON for {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise typer.BadParameter(f"{name} must be a JSON object.")
    return value


def _build_defaults(**items: Optional[object]) -> dict[str, object]:
    return {key: value for key, value in items.items() if value is not None}
