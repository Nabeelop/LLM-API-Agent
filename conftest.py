"""conftest.py — Makes the project root importable in pytest.

Adds the project root to sys.path so that ``import app`` and
``import rag`` work from within the tests/ directory without
needing an editable install.
"""

import sys
import os

# Insert project root at the front of the path
sys.path.insert(0, os.path.dirname(__file__))
