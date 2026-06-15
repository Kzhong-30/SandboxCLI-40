import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    try:
        config.addinivalue_line("markers", "asyncio: mark async test")
    except Exception:
        pass
