"""Utilities to monkey-patch tqdm modules with Progressista's remote bars."""

from __future__ import annotations

import importlib
from typing import Any, Dict, Iterable, Tuple, Type

from .client import RemoteTqdmMixin, make_remote_tqdm

PatchedTarget = Tuple[str, str]

_PATCHED: Dict[PatchedTarget, Type[Any]] = {}


def install(**defaults: Any) -> None:
    """Replace common tqdm entry points with remote-enabled subclasses."""

    targets: Iterable[PatchedTarget] = [
        ("tqdm", "tqdm"),
        ("tqdm.std", "tqdm"),
        ("tqdm.asyncio", "tqdm"),
    ]

    optional_targets: Iterable[PatchedTarget] = [
        ("tqdm.auto", "tqdm"),
        ("tqdm.autonotebook", "tqdm"),
        ("tqdm.notebook", "tqdm"),
    ]

    for target in list(targets) + list(optional_targets):
        module_name, attr = target
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        original = getattr(module, attr, None)
        if original is None or not isinstance(original, type):
            continue

        if isinstance(original, type) and issubclass(original, RemoteTqdmMixin):
            # Already patched; update defaults instead.
            if defaults:
                _update_defaults(original, defaults)
            continue

        remote_cls = make_remote_tqdm(original, **defaults)
        setattr(module, attr, remote_cls)
        _PATCHED.setdefault(target, original)

    # Keep handy aliases on the root tqdm package coherent after patching.
    try:
        base_module = importlib.import_module("tqdm")
    except ImportError:
        return
    for name in ("tqdm",):
        if hasattr(base_module, name):
            obj = getattr(base_module, name)
            if isinstance(obj, type) and issubclass(obj, RemoteTqdmMixin):
                setattr(base_module, name, obj)


def uninstall() -> None:
    """Restore the original tqdm classes."""

    for (module_name, attr), original in list(_PATCHED.items()):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        setattr(module, attr, original)
    _PATCHED.clear()


def _update_defaults(remote_cls: Type[Any], defaults: Dict[str, Any]) -> None:
    if not defaults:
        return
    current = getattr(remote_cls, "_remote_defaults", {})
    updated = {**current, **defaults}
    setattr(remote_cls, "_remote_defaults", updated)


__all__ = ["install", "uninstall"]
