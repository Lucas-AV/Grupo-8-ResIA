"""Organiza o notebook de EDA para uma demonstracao guiada."""

from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "analise_exploratoria.ipynb"
OPENING = """# Análise exploratória — Spotify Tracks Dataset

Este notebook é uma demonstração guiada da análise exploratória que fundamenta o agente de recomendação de músicas. Execute as células de código na ordem, uma a uma, usando **Shift + Enter**. Cada seção mostra uma pergunta simples, o cálculo usado para respondê-la e o resultado visual.

> Para uma demonstração ao vivo, comece pela próxima célula e avance sem pular etapas. Não é necessário configurar nenhum serviço externo."""
AGENDA = """## Roteiro da demonstração

1. Preparar as bibliotecas e carregar a base.
2. Entender o tamanho e a qualidade dos dados.
3. Explorar artistas, álbuns e gêneros.
4. Comparar popularidade, energia, dançabilidade e escala musical.
5. Observar relações entre popularidade e características de áudio.

O notebook usa `data/processed/dataset.csv`, já versionado no projeto. Os scripts em `scripts/` geram os mesmos artefatos para o site e para a execução reproduzível em linha de comando."""
PATH_SETUP = """from pathlib import Path
import sys

PROJECT_ROOT = Path.cwd().resolve()
while not (PROJECT_ROOT / "data" / "processed" / "dataset.csv").exists():
    if PROJECT_ROOT.parent == PROJECT_ROOT:
        raise FileNotFoundError("Não foi possível localizar data/processed/dataset.csv.")
    PROJECT_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from chart_style import ACCENT, GRID, INK, INK_SECONDARY, LABEL_SIZE, TICK_SIZE, TITLE_SIZE, apply_style"""


def prepare_notebook(notebook_path: Path = NOTEBOOK) -> None:
    """Atualiza somente os textos e o import que suportam a demonstração."""
    notebook = nbformat.read(notebook_path, as_version=4)
    notebook.cells[0].source = OPENING
    if not any(cell.cell_type == "markdown" and "## Roteiro da demonstração" in cell.source for cell in notebook.cells):
        notebook.cells.insert(1, nbformat.v4.new_markdown_cell(AGENDA))
    setup_cell = next(cell for cell in notebook.cells if cell.cell_type == "code" and "chart_style import" in cell.source)
    import_line = next(line for line in setup_cell.source.splitlines() if "chart_style import" in line)
    setup_cell.source = setup_cell.source.replace(import_line, PATH_SETUP)
    setup_cell.source = setup_cell.source.replace('DATA_FILE = "data/processed/dataset.csv"', 'DATA_FILE = PROJECT_ROOT / "data" / "processed" / "dataset.csv"')
    nbformat.write(notebook, notebook_path)


if __name__ == "__main__":
    prepare_notebook()
    print(f"Notebook preparado: {NOTEBOOK.relative_to(ROOT)}")
