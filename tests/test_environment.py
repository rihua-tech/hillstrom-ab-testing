"""Fast checks for the pinned Phase 1.0 development environment."""

import sys
from importlib import import_module, metadata

import pytest

PINNED_PACKAGES = {
    "numpy": "2.3.5",
    "pandas": "2.3.3",
    "pytest": "8.4.2",
    "ruff": "0.14.14",
    "scipy": "1.16.3",
    "statsmodels": "0.14.6",
}
SCIENTIFIC_MODULES = ("numpy", "pandas", "scipy", "statsmodels")


def test_python_version_is_pinned() -> None:
    """Keep local development and CI on the frozen Python minor version."""
    assert sys.version_info[:3] == (3, 12, 10)


@pytest.mark.parametrize("package, expected", PINNED_PACKAGES.items())
def test_dependency_version_is_pinned(package: str, expected: str) -> None:
    """Confirm that the environment matches the reviewed dependency pins."""
    assert metadata.version(package) == expected


@pytest.mark.parametrize("module_name", SCIENTIFIC_MODULES)
def test_scientific_dependency_imports(module_name: str) -> None:
    """Catch missing or binary-incompatible scientific dependencies quickly."""
    assert import_module(module_name) is not None
