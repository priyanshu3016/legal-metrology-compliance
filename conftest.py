import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))

# Person 5 AI engine (flat imports like "from analyzer import ...")
_ai = os.path.join(_root, "ai-engine")
if _ai not in sys.path:
    sys.path.insert(0, _ai)

# Person 6 Legal engine (absolute imports like "from backend.compliance...")
_legal = os.path.join(_root, "rules-engine", "legal-core")
if _legal not in sys.path:
    sys.path.insert(0, _legal)
