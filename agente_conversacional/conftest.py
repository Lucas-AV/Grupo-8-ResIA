"""Expõe os módulos do agente sem conflitar com ``spotify_explorer``."""

import sys
from pathlib import Path


AGENT_DIRECTORY = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIRECTORY.parent
sys.path.insert(0, str(AGENT_DIRECTORY))
sys.path.insert(0, str(PROJECT_ROOT))
