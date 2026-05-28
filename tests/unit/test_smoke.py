"""Phase 0 smoke tests — package import and version."""

import aiwerewolf


def test_version() -> None:
    assert aiwerewolf.__version__ == "0.1.0"


def test_package_importable() -> None:
    assert aiwerewolf.__doc__ is not None
