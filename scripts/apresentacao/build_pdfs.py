"""Monta PDFs 16:9 a partir das prévias PNG geradas para cada deck."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas


def build_pdf(input_dir: Path, output_path: Path) -> None:
    slides = sorted(input_dir.glob("slide-*.png"))
    if not slides:
        raise SystemExit(f"Nenhuma prévia encontrada em {input_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 13,333 × 7,5 pol. em pontos: a mesma proporção e o mesmo tamanho do PPTX.
    canvas = Canvas(str(output_path), pagesize=(960, 540), pageCompression=1)
    canvas.setTitle(output_path.stem)

    for slide in slides:
        with Image.open(slide) as image:
            image.load()
            canvas.drawImage(ImageReader(image), 0, 0, width=960, height=540)
        canvas.showPage()

    canvas.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pitch-preview", type=Path, required=True)
    parser.add_argument("--pitch-pdf", type=Path, required=True)
    parser.add_argument("--tecnica-preview", type=Path, required=True)
    parser.add_argument("--tecnica-pdf", type=Path, required=True)
    args = parser.parse_args()

    build_pdf(args.pitch_preview, args.pitch_pdf)
    build_pdf(args.tecnica_preview, args.tecnica_pdf)


if __name__ == "__main__":
    main()
