import sys
import os
import pytest

# Add ai-engine directory to sys.path for flat imports
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

@pytest.fixture(autouse=True)
def _ai_engine_cwd(monkeypatch):
    """Ensure tests in ai-engine execute with ai-engine as CWD for relative sample paths."""
    monkeypatch.chdir(_dir)
