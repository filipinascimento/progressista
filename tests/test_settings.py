from __future__ import annotations

import importlib
import sys
from types import ModuleType


def _reload_settings_module() -> ModuleType:
    sys.modules.pop("progressista.settings", None)
    return importlib.import_module("progressista.settings")


def test_server_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("PROGRESSISTA_ALLOW_ORIGINS", "https://a.example, https://b.example ")
    monkeypatch.setenv("PROGRESSISTA_API_TOKENS", "alpha , beta,")
    monkeypatch.setenv("PROGRESSISTA_CLEANUP_INTERVAL", "7.5")

    settings_module = _reload_settings_module()
    settings = settings_module.ServerSettings()

    assert settings.allow_origins == ("https://a.example", "https://b.example")
    assert settings.api_tokens == ("alpha", "beta")
    assert settings.cleanup_interval == 7.5
    sys.modules.pop("progressista.settings", None)


def test_client_settings_defaults_can_be_overridden(monkeypatch) -> None:
    monkeypatch.setenv("PROGRESSISTA_SERVER_URL", "https://example/api")
    monkeypatch.setenv("PROGRESSISTA_PUSH_INTERVAL", "1.5")
    monkeypatch.setenv("PROGRESSISTA_REQUEST_TIMEOUT", "5.5")
    monkeypatch.setenv("PROGRESSISTA_API_TOKEN", "secret")

    settings_module = _reload_settings_module()
    settings = settings_module.ClientSettings()

    assert settings.server_url == "https://example/api"
    assert settings.push_interval == 1.5
    assert settings.request_timeout == 5.5
    assert settings.api_token == "secret"
    sys.modules.pop("progressista.settings", None)
