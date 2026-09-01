"""Pytest config: expose scripts/ (bare imports like ``from chart_style import``)
and site/ (via each test file's own sys.path.insert) to the test suite."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
