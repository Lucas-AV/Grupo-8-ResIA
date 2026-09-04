"""Ticket 2.5 — segunda chamada ao LLM: transforma o resultado de
`buscar_recomendacoes` numa resposta em linguagem natural, citando só as
faixas realmente retornadas. Se o LLM falhar, der timeout, ou não
devolver um JSON utilizável, cai pro template determinístico (ticket
2.4) sem quebrar o turno — essa função nunca levanta exceção."""

import json
import logging

from chat import template
from chat.historico_llm import historico_para_mensagens, truncar_historico
from chat.json_extrator import extrair_primeiro_json
from llm.client import chamar_llm
from llm.errors import LLMCallError

logger = logging.getLogger("agente.chat.gerador")

# v1 — versionar o nome se as instruções/formato de saída mudarem.
SYSTEM_PROMPT_GERACAO_V1 = """Você é o módulo de geração de um agente de recomendação musical.
Você recebe a mensagem do usuário e uma lista de faixas já escolhidas por um mecanismo de busca
determinístico — não é sua tarefa escolher faixas, só apresentá-las de forma natural em português.

Regras estritas:
- Cite APENAS faixas que estejam na lista de faixas fornecida. Nunca cite, sugira ou invente uma
  faixa, artista ou álbum que não esteja nessa lista, mesmo que o usuário peça diretamente.
- Se a lista de faixas estiver vazia, explique que não foi encontrado nada com esse pedido no
  catálogo e sugira tentar outro gênero, artista ou humor — sem inventar nenhuma faixa.
- Devolva APENAS um objeto JSON, sem texto antes ou depois, exatamente neste formato:
  {"texto": "<sua resposta em texto>", "faixas_citadas": ["<track_id citado>", "..."]}
- "faixas_citadas" deve conter só os valores do campo "track_id" das faixas fornecidas que você
  realmente mencionou no texto — nunca um id que não esteja na lista fornecida.
"""


def gerar(mensagem, historico, resultado):
    """Devolve `(texto, faixas_citadas)`. Nunca levanta exceção — qualquer
    falha da etapa de geração degrada pro template determinístico (2.4)."""
    faixas = resultado.get("faixas") or []
    if not faixas:
        # Resultado vazio é um caso de uso legítimo (seção 6) — o template
        # já cobre esse texto de forma determinística, sem risco de o LLM
        # "inventar" uma faixa pra preencher uma lista vazia.
        return _fallback_template(resultado)

    mensagens = _montar_mensagens(mensagem, historico, faixas)

    try:
        resposta = chamar_llm(mensagens, formato_json=True)
    except LLMCallError as exc:
        logger.warning("geração via LLM falhou/indisponível, caindo pro template: %s", exc)
        return _fallback_template(resultado)

    corpo = extrair_primeiro_json(resposta)
    texto = corpo.get("texto") if isinstance(corpo, dict) else None
    if not isinstance(texto, str) or not texto.strip():
        logger.warning("geração via LLM não devolveu JSON utilizável, caindo pro template: %r", resposta)
        return _fallback_template(resultado)

    citadas_brutas = corpo.get("faixas_citadas")
    if isinstance(citadas_brutas, list):
        citadas = tuple(item for item in citadas_brutas if isinstance(item, str))
    else:
        citadas = ()

    return texto, citadas


def _montar_mensagens(mensagem, historico, faixas):
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT_GERACAO_V1}]
    mensagens.extend(historico_para_mensagens(truncar_historico(historico)))
    mensagens.append(
        {
            "role": "user",
            "content": (
                f"Mensagem do usuário: {mensagem}\n\n"
                f"Faixas disponíveis (JSON, só pode citar o que estiver aqui): "
                f"{json.dumps(faixas, ensure_ascii=False)}"
            ),
        }
    )
    return mensagens


def _fallback_template(resultado):
    texto = template.formatar_resultado(resultado)
    citadas = tuple(faixa["track_id"] for faixa in resultado.get("faixas") or [])
    return texto, citadas
