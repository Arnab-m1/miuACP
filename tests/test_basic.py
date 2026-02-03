#!/usr/bin/env python3
"""
Basic tests for miuacp package.
"""

import pytest


def test_import():
    """Test that the package can be imported."""
    try:
        import miuacp
        assert miuacp is not None
    except ImportError as e:
        pytest.fail(f"Failed to import miuacp: {e}")


def test_version():
    """Test that the package has a version."""
    try:
        import miuacp
        assert hasattr(miuacp, '__version__')
        assert miuacp.__version__ == "1.0.0"
    except ImportError:
        pytest.skip("Package not available")


if __name__ == "__main__":
    pytest.main([__file__])
