def test_basic():
    """Basic test to verify pytest configuration works."""
    assert 1 + 1 == 2

def test_imports():
    """Test that imports work."""
    import sys
    assert sys.version_info.major >= 3
