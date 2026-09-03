"""Ticket 2.4 — respostas por template determinístico, sem nenhuma
chamada de LLM. É a resposta padrão do MVP (item 1 da seção 11 do
pipeline) e o fallback permanente quando a geração via LLM (ticket 2.5)
está indisponível ou falha."""


def formatar_resultado(resultado):
    """Formata o resultado de `buscar_recomendacoes` em texto fixo —
    cobre o caso com faixas e o caso vazio (zero faixas encontradas) de
    forma diferenciada, sem depender de LLM."""
    faixas = resultado.get("faixas") or []
    if not faixas:
        return _sem_resultados()
    return _com_resultados(faixas)


def _com_resultados(faixas):
    linhas = [f"- {faixa['nome']} — {faixa['artista']} ({faixa['genero']})" for faixa in faixas]
    if len(faixas) == 1:
        intro = "Encontrei uma faixa pra você:"
    else:
        intro = f"Encontrei {len(faixas)} faixas pra você:"
    return intro + "\n" + "\n".join(linhas)


def _sem_resultados():
    return (
        "Não encontrei nenhuma faixa no nosso catálogo que batesse com esse pedido. "
        "Quer tentar outro gênero, outro artista ou descrever o humor de outro jeito?"
    )


def saudacao():
    """Resposta de boas-vindas pra saudação/small talk (caso de uso 9) —
    nunca aciona `buscar_recomendacoes`."""
    return (
        "Oi! Eu sou o agente de recomendação musical. Me conta que gênero, "
        "artista ou humor você quer ouvir hoje que eu busco umas sugestões."
    )


def fora_de_escopo():
    """Resposta pra pedido fora do escopo do agente (caso de uso 10) —
    ex.: pedir letra de música ou composição nova."""
    return (
        "Isso foge do que eu consigo fazer por aqui — eu só recomendo faixas "
        "do nosso catálogo, não componho música nova nem busco letras. "
        "Quer que eu sugira algo pra você ouvir?"
    )


def esclarecimento():
    """Pergunta de esclarecimento genérica pro fallback total (ticket
    2.7) — usada quando nem o roteador nem a extração via LLM conseguiram
    entender o pedido."""
    return (
        "Não entendi bem o que você quer ouvir — me diz um gênero específico, "
        "um artista de referência, ou como você quer se sentir (mais animado, "
        "mais calmo, mais feliz...) que eu busco algumas sugestões."
    )
