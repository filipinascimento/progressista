import json

import pytest
from typer import BadParameter

from progressista.cli import _build_defaults, _loads_json


def test_build_defaults_filters_none_values() -> None:
    result = _build_defaults(alpha=1, beta=None, gamma="value")
    assert result == {"alpha": 1, "gamma": "value"}


def test_loads_json_parses_objects() -> None:
    payload = {"foo": "bar", "answer": 42}
    result = _loads_json("meta", json.dumps(payload))
    assert result == payload


def test_loads_json_requires_object_payload() -> None:
    with pytest.raises(BadParameter):
        _loads_json("meta", json.dumps(["not", "an", "object"]))


def test_loads_json_rejects_invalid_json() -> None:
    with pytest.raises(BadParameter):
        _loads_json("headers", "{not-valid}")
