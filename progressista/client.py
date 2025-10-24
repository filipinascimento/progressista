"""Remote tqdm subclass that sends progress updates to the Progressista server."""

from __future__ import annotations

import copy
import queue
import socket
import threading
import time
from typing import Any, Dict, Iterable, Optional, Type, TypeVar, cast

import requests
from tqdm import tqdm

from .settings import ClientSettings

class RemoteTqdmMixin:
    """Mixin that injects remote progress emission into tqdm-compatible classes."""

    _remote_defaults: Dict[str, Any] = {}
    _is_progressista_remote = True

    def __init__(
        self,
        iterable: Optional[Iterable[Any]] = None,
        *args: Any,
        server_url: Optional[str] = None,
        task_id: Optional[str] = None,
        push_every: Optional[float] = None,
        unit: Optional[str] = None,
        request_timeout: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        defaults = dict(getattr(self.__class__, "_remote_defaults", {}) or {})
        settings = ClientSettings()

        server_default = defaults.get("server_url")
        self._server_url = (
            server_url
            if server_url is not None
            else server_default if server_default is not None else settings.server_url
        )

        push_default = defaults.get("push_every", settings.push_interval)
        self._push_every = push_every if push_every is not None else push_default
        if self._push_every is None:
            self._push_every = settings.push_interval
        self._push_every = float(self._push_every)

        timeout_default = defaults.get("request_timeout", settings.request_timeout)
        self._request_timeout = (
            request_timeout if request_timeout is not None else timeout_default
        )
        if self._request_timeout is None:
            self._request_timeout = settings.request_timeout
        self._request_timeout = float(self._request_timeout)

        task_default = defaults.get("task_id")
        self._task_id = task_id if task_id is not None else task_default
        if self._task_id is None:
            self._task_id = self._default_task_id()

        unit_default = defaults.get("unit")
        self._unit_override = unit if unit is not None else unit_default

        meta_default = defaults.get("meta")
        self._meta = copy.deepcopy(meta_default) if meta is None and meta_default is not None else meta

        headers_default = defaults.get("headers")
        self._headers = (
            copy.deepcopy(headers_default)
            if headers is None and headers_default is not None
            else headers
        )
        if self._headers is None and settings.api_token:
            self._headers = {"Authorization": f"Bearer {settings.api_token}"}

        self._settings = settings
        self._stop_event = threading.Event()
        self._queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()

        super().__init__(iterable, *args, **kwargs)  # type: ignore[misc]

        self._start_worker()
        self._emit(
            status="start",
            n=self.n,
            total=self.total,
            desc=self.desc,
            unit=self._unit_override or getattr(self, "unit", None),
        )

    # --------------------------------------------------------------------- util
    def _default_task_id(self) -> str:
        hostname = socket.gethostname()
        return f"{hostname}:{int(time.time())}:{id(self)}"

    def _post(self, payload: Dict[str, Any]) -> None:
        try:
            requests.post(
                cast(str, self._server_url),
                json=payload,
                timeout=cast(float, self._request_timeout),
                headers=self._headers,
            )
        except Exception:
            # Silent failure; server availability should not break progress loops.
            pass

    def _worker(self) -> None:
        last_push = 0.0
        buffered: Dict[str, Any] | None = None

        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.1)
                buffered = item
            except queue.Empty:
                item = None

            now = time.time()
            if buffered and (now - last_push >= cast(float, self._push_every)):
                self._post(buffered)
                last_push = now
                buffered = None

        # Drain the remaining buffer on shutdown.
        if buffered:
            self._post(buffered)
        # Flush rest of the queue so close() pushes last events.
        while True:
            try:
                pending = self._queue.get_nowait()
            except queue.Empty:
                break
            self._post(pending)

    def _start_worker(self) -> None:
        thread = threading.Thread(target=self._worker, name="RemoteTqdmPusher", daemon=True)
        thread.start()
        self._thread = thread

    def _emit(self, **payload: Any) -> None:
        payload.setdefault("task_id", self._task_id)
        payload.setdefault("timestamp", time.time())
        if "unit" not in payload and self._unit_override:
            payload["unit"] = self._unit_override
        if self._meta is not None and "meta" not in payload:
            payload["meta"] = self._meta
        self._queue.put(payload)

    # ------------------------------------------------------------------ tqdm API
    def update(self, n: int = 1) -> None:  # type: ignore[override]
        super().update(n)
        self._emit(status="update", n=self.n, total=self.total, desc=self.desc)

    def set_description(self, desc: Optional[str] = None, refresh: bool = True) -> None:
        super().set_description(desc, refresh)
        self._emit(status="update", n=self.n, total=self.total, desc=self.desc)

    def close(self) -> None:  # type: ignore[override]
        if getattr(self, "_closed", False):
            return
        try:
            super().close()
        finally:
            self._emit(status="close", n=self.n, total=self.total, desc=self.desc)
            self._stop_event.set()
            if hasattr(self, "_thread"):
                self._thread.join(timeout=cast(float, self._request_timeout))


BaseTqdmType = TypeVar("BaseTqdmType", bound=tqdm)


def make_remote_tqdm(
    base_cls: Type[BaseTqdmType],
    **defaults: Any,
) -> Type[BaseTqdmType]:
    """Create a remote-enabled subclass for the provided tqdm base class."""

    attrs: Dict[str, Any] = {
        "__module__": __name__,
        "_remote_defaults": dict(defaults),
    }
    return cast(
        Type[BaseTqdmType],
        type(f"Remote{base_cls.__name__}", (RemoteTqdmMixin, base_cls), attrs),
    )


RemoteTqdm = make_remote_tqdm(tqdm)


__all__ = ["RemoteTqdm", "RemoteTqdmMixin", "make_remote_tqdm"]
