"""Valida a estrutura mínima da demonstração do notebook."""

from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "analise_exploratoria.ipynb"
EXPECTED_HEADINGS = (
    "## Roteiro da demonstração",
    "## 1. Carregar o dataset",
    "## 10. Correlacoes entre popularidade, duracao e features de audio",
)


def validate_notebook(notebook_path: Path = NOTEBOOK) -> list[str]:
    """Retorna erros encontrados; uma lista vazia indica notebook pronto."""
    notebook = nbformat.read(notebook_path, as_version=4)
    errors: list[str] = []
    if not notebook.cells:
        return ["O notebook não possui células."]
    first_cell = notebook.cells[0]
    if first_cell.cell_type != "markdown" or "Análise exploratória" not in first_cell.source:
        errors.append("A abertura da demonstração não foi encontrada.")
    sources = "\n".join(cell.source for cell in notebook.cells)
    for heading in EXPECTED_HEADINGS:
        if heading not in sources:
            errors.append(f"Seção ausente: {heading}")
    if "sys.path.insert(0, str(PROJECT_ROOT / \"scripts\"))" not in sources:
        errors.append("O notebook deve localizar os scripts a partir da raiz do projeto.")
    if 'DATA_FILE = PROJECT_ROOT / "data" / "processed" / "dataset.csv"' not in sources:
        errors.append("O caminho do dataset não está definido a partir da raiz do projeto.")
    return errors


if __name__ == "__main__":
    problems = validate_notebook()
    if problems:
        raise SystemExit("\n".join(problems))
    print("Notebook validado com sucesso.")
