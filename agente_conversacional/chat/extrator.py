"""Ticket 2.2 — extracao da consulta estruturada via LLM, usada quando o
roteador (2.1) nao resolve a mensagem. Chamada unica ao LLM pedindo *so*
o JSON da consulta (secao 4.2 do pipeline), com timeout curto (usa o
timeout padrao de `chamar_llm`, ja configurado pra ~8s via
`LLM_TIMEOUT_SECONDS`) e parser tolerante a texto ao redor do JSON."""

import logging

from chat.historico_llm import historico_para_mensagens, truncar_historico
from chat.json_extrator import extrair_primeiro_json
from llm.client import chamar_llm
from llm.errors import LLMCallError

logger = logging.getLogger("agente.chat.extrator")

# v1 — versionar o nome se o schema/instrucoes mudarem, pra facilitar
# comparar respostas entre versoes de prompt durante os testes manuais.
SYSTEM_PROMPT_EXTRACAO_V1 = """Você é o módulo de extração de um agente de recomendação musical.
Sua única tarefa é ler a mensagem do usuário (e o histórico da conversa, se houver) e devolver
APENAS um objeto JSON, sem nenhum texto antes ou depois, com exatamente estas chaves:

{
  "genero": "string ou null",
  "energia": "baixa | media | alta | null",
  "valencia": "triste | neutro | feliz | null",
  "dancabilidade": "baixa | media | alta | null",
  "artista_referencia": "string ou null",
  "excluir_explicit": true ou false,
  "n_resultados": inteiro (padrão 10)
}

Regras:
- Nunca invente um valor para um campo que a mensagem não menciona — use null.
- "n_resultados" só deve ser diferente de 10 se o usuário pedir uma quantidade explícita.
- Não inclua nenhuma chave além dessas sete.
- Não escreva explicações, markdown ou comentários — só o objeto JSON.
"""


def extrair_consulta(mensagem, historico=()):
    """Devolve o dict bruto (ainda não validado — ver ticket 2.3) extraído
    pelo LLM a partir de `mensagem` e do `historico` truncado da sessão
    (ticket 2.8), ou `None` quando o LLM está indisponível, dá timeout ou
    não devolve nenhum JSON reconhecível. O pipeline trata `None` como
    "extração falhou" e cai no fallback total (ticket 2.7)."""
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT_EXTRACAO_V1}]
    mensagens.extend(historico_para_mensagens(truncar_historico(historico)))
    mensagens.append({"role": "user", "content": mensagem})

    try:
        resposta = chamar_llm(mensagens, formato_json=True)
    except LLMCallError as exc:
        logger.warning("extração via LLM falhou/indisponível: %s", exc)
        return None

    consulta = extrair_primeiro_json(resposta)
    if consulta is None:
        logger.warning("extração via LLM não devolveu JSON válido: %r", resposta)
        return None
    return consulta
