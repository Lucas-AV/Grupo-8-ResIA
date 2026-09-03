"""Garante que o comando documentado do Uvicorn seja carregável."""

import os
import subprocess
import sys
from pathlib import Path


AGENT_DIRECTORY = Path(__file__).resolve().parent


def test_documented_uvicorn_entrypoint_loads_without_test_paths():
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from uvicorn.importer import import_from_string; "
            "app = import_from_string('app:app'); "
            "assert app.title == 'Agente Conversacional'",
        ],
        cwd=AGENT_DIRECTORY,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
