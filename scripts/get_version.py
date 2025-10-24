#!/usr/bin/env python3
"""Return the project version derived from Git tags via setuptools-scm.

The script prints the detected version to stdout so it can be reused in
Meson configuration, release tooling, or other automation.
"""

from __future__ import annotations

import re
from pathlib import Path
import sys

FALLBACK_VERSION = "0.0.0"
REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"


def detect_version() -> str:
    """Return the version from VCS tags, falling back if unavailable."""
    try:
        from setuptools_scm import get_version
    except ModuleNotFoundError:
        return _fallback_version()

    try:
        return get_version(root=str(REPO_ROOT), fallback_version=FALLBACK_VERSION)
    except Exception as exc:  # pragma: no cover - best effort logging for tooling
        print(f"[get_version] falling back to {FALLBACK_VERSION}: {exc}", file=sys.stderr)
        return _fallback_version()


def _fallback_version() -> str:
    version = _version_from_pyproject()
    if version:
        return version
    version = _version_from_package()
    if version:
        return version
    return FALLBACK_VERSION


def _version_from_pyproject() -> str | None:
    if not PYPROJECT.exists():
        return None

    text = PYPROJECT.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if match:
        return match.group(1)

    section = _extract_hatch_version_section(text)
    if section is None:
        return None

    path, pattern = section
    if path is None:
        return None
    return _version_from_file(REPO_ROOT / path, pattern)


def _version_from_package() -> str | None:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from progressista import __version__  # type: ignore
    except Exception:
        return None
    finally:
        try:
            sys.path.remove(str(REPO_ROOT))
        except ValueError:
            pass
    return __version__


def _extract_hatch_version_section(text: str) -> tuple[str | None, str | None] | None:
    match = re.search(
        r"(?ms)^\[tool\.hatch\.version\]\s*(?P<body>.*?)(?=^\[|\Z)", text + "\n", flags=0
    )
    if not match:
        return None
    body = match.group("body")
    path_match = re.search(r'^\s*path\s*=\s*"([^"]+)"', body, flags=re.MULTILINE)
    pattern_match = re.search(r'^\s*pattern\s*=\s*"([^"]+)"', body, flags=re.MULTILINE)
    path = path_match.group(1) if path_match else None
    pattern = pattern_match.group(1) if pattern_match else None
    return path, pattern


def _version_from_file(path: Path, pattern: str | None) -> str | None:
    if not path.exists():
        return None
    text = path.read_text()
    if pattern:
        regex = re.compile(pattern, flags=re.MULTILINE)
    else:
        regex = re.compile(
            r'(?m)^(?:__version__|VERSION)\s*=\s*["\'](?P<version>[^"\']+)["\']'
        )
    match = regex.search(text)
    if not match:
        return None
    if "version" in match.groupdict():
        return match.group("version")
    raise RuntimeError("Configured version pattern must contain a 'version' group.")


def main() -> int:
    print(detect_version())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
