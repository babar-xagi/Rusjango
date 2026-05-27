"""Smoke tests for the Python package."""


def test_version() -> None:
    import rusjango

    assert rusjango.__version__
