"""Project config discovery tests."""

from pathlib import Path

import pytest

from rusjango.config import find_project_root, load_rusjango_config


def test_find_examples_hello() -> None:
    hello = Path(__file__).resolve().parents[3] / "examples" / "hello"
    if not hello.is_dir():
        pytest.skip("examples/hello not present")
    root = find_project_root(hello)
    assert root == hello.resolve()
    cfg = load_rusjango_config(root)
    assert cfg["app"] == "main:app"
