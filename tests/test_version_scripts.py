from __future__ import annotations

import re
import sys
import types

from scripts import get_version as version_script


def test_fallback_version_prefers_pyproject(monkeypatch) -> None:
    expected = version_script._version_from_pyproject()
    assert expected is not None

    monkeypatch.setattr(version_script, "_version_from_package", lambda: None)

    assert version_script._fallback_version() == expected


def test_fallback_version_uses_package_when_pyproject_missing(monkeypatch) -> None:
    from progressista import __version__ as package_version

    monkeypatch.setattr(version_script, "_version_from_pyproject", lambda: None)

    assert version_script._fallback_version() == package_version


def test_detect_version_handles_setuptools_failure(monkeypatch, capsys) -> None:
    expected = version_script._fallback_version()

    module = types.SimpleNamespace()

    def failing_get_version(*args, **kwargs):
        raise RuntimeError("boom")

    module.get_version = failing_get_version  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "setuptools_scm", module)

    result = version_script.detect_version()
    captured = capsys.readouterr()

    assert result == expected
    assert re.search(r"falling back", captured.err, re.IGNORECASE)
