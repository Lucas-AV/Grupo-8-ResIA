"""Utilitario compartilhado pela extracao (2.2) e geracao (2.5): trunca o
historico da sessao antes de mandar pro LLM (ticket 2.8) e traduz as
mensagens de dominio (`sessions.models.Message`) para o formato
`{"role": ..., "content": ...}` que `chamar_llm` espera.

O historico completo da sessao continua disponivel via `GET
/chat/historico` (ticket 3.3) — só o que e enviado ao LLM e limitado, pra
nao estourar o context window do modelo local (edge case documentado na
secao 7 do pipeline)."""

LIMITE_HISTORICO_LLM = 6

_PAPEL_DOMINIO_PARA_LLM = {
    "usuario": "user",
    "agente": "assistant",
    "sistema": "system",
}


def truncar_historico(historico, limite=LIMITE_HISTORICO_LLM):
    """Mantem so as ultimas `limite` mensagens do historico."""
    historico = tuple(historico) if historico else ()
    if limite <= 0:
        return ()
    return historico[-limite:]


def historico_para_mensagens(historico):
    """Traduz `Message`s de dominio pro formato de mensagem de chat
    aceito por `chamar_llm` (lista de `{"role", "content"}`)."""
    return [
        {"role": _PAPEL_DOMINIO_PARA_LLM.get(mensagem.role, "user"), "content": mensagem.conteudo}
        for mensagem in historico
    ]
