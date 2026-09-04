"""Executa o notebook em memória e falha ao encontrar uma célula com erro."""

from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_notebook_demo import NOTEBOOK, ROOT, validate_notebook


def run_notebook() -> None:
    """Executa o notebook a partir da raiz, sem sobrescrever o arquivo."""
    problems = validate_notebook()
    if problems:
        raise ValueError("Notebook inválido:\n" + "\n".join(problems))
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=300,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute(cwd=str(ROOT))


if __name__ == "__main__":
    run_notebook()
    print("Notebook executado com sucesso, sem modificar o arquivo versionado.")
