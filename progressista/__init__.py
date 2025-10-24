"""Progressista exposes a remote-friendly tqdm wrapper and FastAPI dashboard."""

from .client import RemoteTqdm, make_remote_tqdm
from .patch import install as install_patch
from .server import create_app, run_server

__all__ = ["RemoteTqdm", "make_remote_tqdm", "install_patch", "create_app", "run_server"]

__version__ = "0.1.0"
