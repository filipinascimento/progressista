"""Progressista exposes a remote-friendly tqdm wrapper and FastAPI dashboard."""

__version__ = "0.2.1"

try:  # pragma: no cover - metadata import is environment dependent
    from importlib import metadata as _metadata
except ImportError:  # pragma: no cover - Python < 3.8 not supported
    _metadata = None  # type: ignore[assignment]
else:
    try:
        __version__ = _metadata.version("progressista")
    except _metadata.PackageNotFoundError:
        pass


from .client import RemoteTqdm, make_remote_tqdm
from .patch import install as install_patch
from .server import create_app, run_server

__all__ = ["RemoteTqdm", "make_remote_tqdm", "install_patch", "create_app", "run_server"]
