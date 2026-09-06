import sys
import os

# Add legal-core directory to sys.path for backend.* imports
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)
