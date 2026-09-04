"""Ticket 12.6 — sugestão de título/descrição de playlist via LLM, exibida
no modal de "Salvar no Spotify" (ticket 12.1/KAN-104) antes do usuário
confirmar. Chamada única ao LLM pedindo *só* o JSON da sugestão, mesmo
padrão de `chat/extrator.py` — nunca bloqueia a criação da playlist:
qualquer falha (LLM indisponível/timeout, JSON inválido, campo vazio)
degrada pro nome/descrição padrão já usados em `spotify_auth/playlist.py`.
"""

import logging

from chat.json_extrator import extrair_primeiro_json
from llm.client import chamar_llm
from llm.errors import LLMCallError

logger = logging.getLogger("agente.chat.playlist_sugestao")

# Mesmo default de spotify_auth/playlist.py — se o LLM falhar, o usuário vê
# exatamente o que já via antes desse ticket existir.
_NOME_PADRAO = "Recomendações ResIA"
_DESCRICAO_PADRAO = "Playlist gerada pelo agente conversacional do Grupo 8 ResIA."

SYSTEM_PROMPT_SUGESTAO_V1 = """Você sugere título e descrição pra uma playlist do Spotify, a partir da lista de faixas dela.
Devolva APENAS um objeto JSON, sem nenhum texto antes ou depois, com exatamente estas chaves:

{
  "titulo": "string curta, até 60 caracteres",
  "descricao": "string até 200 caracteres, tom casual"
}

Regras:
- Baseie-se nos gêneros/artistas das faixas listadas pra achar um tema em comum (ex.: "Pagode pra Domingo", "Rock Clássico Anos 80").
- Sem tema claro em comum, use algo genérico mas ainda específico ao contexto (ex.: "Minha Mistura ResIA").
- Não escreva explicações, markdown ou comentários — só o objeto JSON.
"""


def sugerir_titulo_descricao(faixas):
    """`faixas`: lista de dicts com pelo menos nome/artista/genero (mesmo
    schema de `TrackItem`). Devolve `{"titulo": str, "descricao": str}` —
    sempre um dict válido, mesmo se o LLM falhar ou `faixas` vier vazia."""
    if not faixas:
        return {"titulo": _NOME_PADRAO, "descricao": _DESCRICAO_PADRAO}

    linhas = "\n".join(
        f"- {faixa.get('nome', '?')} — {faixa.get('artista', '?')} ({faixa.get('genero', '?')})" for faixa in faixas
    )
    mensagens = [
        {"role": "system", "content": SYSTEM_PROMPT_SUGESTAO_V1},
        {"role": "user", "content": f"Faixas da playlist:\n{linhas}"},
    ]

    try:
        resposta = chamar_llm(mensagens, formato_json=True)
    except LLMCallError as exc:
        logger.warning("sugestão de título/descrição falhou/indisponível: %s", exc)
        return {"titulo": _NOME_PADRAO, "descricao": _DESCRICAO_PADRAO}

    sugestao = extrair_primeiro_json(resposta)
    if not isinstance(sugestao, dict):
        logger.warning("sugestão de título/descrição não devolveu JSON válido: %r", resposta)
        return {"titulo": _NOME_PADRAO, "descricao": _DESCRICAO_PADRAO}

    titulo = sugestao.get("titulo")
    descricao = sugestao.get("descricao")
    return {
        "titulo": titulo if isinstance(titulo, str) and titulo.strip() else _NOME_PADRAO,
        "descricao": descricao if isinstance(descricao, str) and descricao.strip() else _DESCRICAO_PADRAO,
    }
