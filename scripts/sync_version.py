#!/usr/bin/env python3
"""Synchronise project metadata files with the VCS-derived version."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
MESON_BUILD = ROOT / "meson.build"
PACKAGE_INIT = ROOT / "progressista" / "__init__.py"

sys.path.insert(0, str(ROOT / "scripts"))
from get_version import detect_version, FALLBACK_VERSION  # noqa: E402


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument(
        "--version",
        help="Override the detected version (leading 'v' is stripped automatically).",
    )
    return parser.parse_args(argv)


def _normalise(version: str) -> str:
    return version[1:] if version.startswith("v") else version


def _replace_once(path: Path, pattern: str, repl: str) -> None:
    regex = re.compile(pattern, flags=re.MULTILINE)
    original = path.read_text()
    updated, count = regex.subn(repl, original)
    if count != 1:
        raise RuntimeError(f"Could not update version in {path}: expected 1 match, got {count}")
    path.write_text(updated)


def _extract_hatch_version_section(text: str) -> tuple[str | None, str | None]:
    match = re.search(
        r"(?ms)^\[tool\.hatch\.version\]\s*(?P<body>.*?)(?=^\[|\Z)", text + "\n", flags=0
    )
    if not match:
        return (None, None)
    body = match.group("body")
    path_match = re.search(r'^\s*path\s*=\s*"([^"]+)"', body, flags=re.MULTILINE)
    pattern_match = re.search(r'^\s*pattern\s*=\s*"([^"]+)"', body, flags=re.MULTILINE)
    path = path_match.group(1) if path_match else None
    pattern = pattern_match.group(1) if pattern_match else None
    return (path, pattern)


def _replace_version_in_file(path: Path, version: str, pattern: str | None) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Version file not found: {path}")

    if pattern:
        regex = re.compile(pattern, flags=re.MULTILINE)
    else:
        regex = re.compile(
            r'(?m)^(?:__version__|VERSION)\s*=\s*["\'](?P<version>[^"\']+)["\']'
        )

    original = path.read_text()
    matches = list(regex.finditer(original))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected a single version assignment in {path} "
            f"using pattern {regex.pattern!r}, found {len(matches)}"
        )
    match = matches[0]
    if "version" not in match.groupdict():
        raise RuntimeError("Configured version pattern must contain a 'version' group.")
    start = match.start("version")
    end = match.end("version")
    updated = original[:start] + version + original[end:]
    path.write_text(updated)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    if args.version:
        version = _normalise(args.version)
    else:
        version = detect_version()
        if version == FALLBACK_VERSION:
            print(
                "[sync_version] Warning: using fallback version. Provide --version or create tags.",
                file=sys.stderr,
            )

    pyproject_text = PYPROJECT.read_text()
    if re.search(r'^(version\s*=\s*)"[^"]+"', pyproject_text, flags=re.MULTILINE):
        _replace_once(
            PYPROJECT,
            r'^(version\s*=\s*)"[^"]+"',
            rf'\1"{version}"',
        )

    hatch_path, hatch_pattern = _extract_hatch_version_section(pyproject_text)
    version_path = ROOT / Path(hatch_path) if hatch_path else PACKAGE_INIT
    _replace_version_in_file(version_path, version, hatch_pattern)

    if MESON_BUILD.exists():
        _replace_once(
            MESON_BUILD,
            r"^(\s*version:\s*)'[^']+'",
            rf"\1'{version}'",
        )
    print(f"Updated project version to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
