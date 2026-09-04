"""Checagem rápida, sem rede, dos artefatos do Épico 13.

Uso: python scripts/check_epic13.py
"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "agente_conversacional" / "spotify_auth" / "catalog.py",
    ROOT / "agente_conversacional" / "spotify_auth" / "pairing.py",
    ROOT / "agente_conversacional" / "spotify_auth" / "routes.py",
]
REQUIRED_FRONTEND = ["spotifyHub.js", "components/trackCard.js"]


def main() -> None:
    for file in FILES:
        ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
    frontend = ROOT / "agente_conversacional" / "frontend"
    missing = [path for path in REQUIRED_FRONTEND if not (frontend / path).is_file()]
    if missing:
        raise SystemExit(f"artefatos frontend ausentes: {', '.join(missing)}")
    routes = FILES[-1].read_text(encoding="utf-8")
    for route in ('/spotify/search', '/spotify/recommendations', '/auth/qr'):
        if route not in routes:
            raise SystemExit(f"rota obrigatória ausente: {route}")
    print("Épico 13: estrutura e sintaxe Python validadas.")


if __name__ == "__main__":
    main()
