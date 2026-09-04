"""Implementação real do `TurnProcessor` (`chat.contracts`) usado por
`POST /chat` (ticket 3.2 — o endpoint em si já existe e chama
`turn_processor.process(...)`; este módulo é o "motor" por trás dele).

Orquestra o turno de conversa seguindo exatamente a ordem de decisão da
seção 5 do pipeline (`docs/PIPELINE_AGENTE_PROPOSTA_B.md`):

    roteador (2.1) -> [extração via LLM (2.2) se o roteador não resolver]
    -> validação (2.3) -> busca determinística -> geração (2.5, com
    fallback pro template 2.4) -> auditoria mecânica (2.6) -> TurnResult

Ticket 2.7 (fallback total) vive aqui: quando o roteador não reconhece a
mensagem *e* a extração via LLM falha/está indisponível, o pipeline
responde com uma pergunta de esclarecimento por template sem nunca
chamar `buscar_recomendacoes` com uma consulta vazia/inexistente.
"""

import time

from chat import auditoria, extrator, gerador, observabilidade, roteador, template, validador
from recomendacao.busca import buscar_recomendacoes
from sessions.models import Track, TurnResult

class ChatPipeline:
    """Implementação concreta de `chat.contracts.TurnProcessor`."""

    def process(self, mensagem, contexto):
        inicio = time.monotonic()
        rota = roteador.rotear(mensagem)

        if rota is not None and rota.tipo == "saudacao":
            _registrar_turno(inicio, rota="saudacao", extracao="nao_necessaria", busca="nao_necessaria", geracao="template", auditoria="nao_necessaria", resultado="sucesso")
            return _resultado_sem_busca(template.saudacao())

        if rota is not None and rota.tipo == "fora_escopo":
            _registrar_turno(inicio, rota="fora_escopo", extracao="nao_necessaria", busca="nao_necessaria", geracao="template", auditoria="nao_necessaria", resultado="sucesso")
            return _resultado_sem_busca(template.fora_de_escopo())

        if rota is not None and rota.tipo == "consulta":
            origem = "roteador"
            consulta_bruta = rota.consulta
        else:
            consulta_bruta = extrator.extrair_consulta(mensagem, contexto.historico)
            if consulta_bruta is None:
                # Ticket 2.7 — fallback total: roteador não resolveu E a
                # extração via LLM falhou/está indisponível. Nunca chama
                # buscar_recomendacoes com consulta vazia/garbage.
                _registrar_turno(inicio, rota="nao_resolvida", extracao="falhou", busca="nao_executada", geracao="template", auditoria="nao_necessaria", resultado="fallback")
                return _resultado_sem_busca(template.esclarecimento())
            origem = "extracao_llm"

        try:
            consulta = validador.validar_consulta(consulta_bruta)
            resultado = buscar_recomendacoes(
                genero=consulta["genero"], energia=consulta["energia"], valencia=consulta["valencia"],
                dancabilidade=consulta["dancabilidade"], artista_referencia=consulta["artista_referencia"],
                excluir_explicit=consulta["excluir_explicit"], n_resultados=consulta["n_resultados"],
                perfil_usuario=contexto.perfil_usuario, faixas_ja_mostradas=contexto.faixas_ja_mostradas,
            )
        except Exception:
            _registrar_turno(inicio, rota=origem, extracao="nao_necessaria" if origem == "roteador" else "sucesso", busca="falhou", geracao="nao_executada", auditoria="nao_executada", resultado="falha")
            raise

        try:
            texto, citadas_brutas = gerador.gerar(mensagem, contexto.historico, resultado)
        except Exception:
            _registrar_turno(inicio, rota=origem, extracao="nao_necessaria" if origem == "roteador" else "sucesso", busca="sucesso", geracao="falhou", auditoria="nao_executada", resultado="falha")
            raise
        try:
            auditoria_resultado = auditoria.auditar_citacoes(citadas_brutas, resultado["faixas"])
        except Exception:
            _registrar_turno(inicio, rota=origem, extracao="nao_necessaria" if origem == "roteador" else "sucesso", busca="sucesso", geracao="sucesso", auditoria="falhou", resultado="falha")
            raise

        _registrar_turno(inicio, rota=origem, extracao="nao_necessaria" if origem == "roteador" else "sucesso", busca="sucesso", geracao="sucesso", auditoria="divergencia" if auditoria_resultado.divergentes else "sucesso", resultado="sucesso")

        return TurnResult(
            mensagem=texto,
            faixas=tuple(_para_track(faixa) for faixa in resultado["faixas"]),
            diversidade_generos=resultado["diversidade_generos"],
            cobertura_sessao=resultado["cobertura_sessao"],
            consulta_efetiva=resultado["consulta_efetiva"],
            faixas_citadas=auditoria_resultado.citadas_validas,
        )


def _para_track(faixa):
    return Track(
        track_id=faixa["track_id"],
        nome=faixa["nome"],
        artista=faixa["artista"],
        album=faixa["album"],
        genero=faixa["genero"],
    )


def _resultado_sem_busca(texto):
    """Resposta que não passou por `buscar_recomendacoes` (saudação,
    fora de escopo ou fallback total) — sem faixas, sem citações."""
    return TurnResult(
        mensagem=texto,
        faixas=(),
        diversidade_generos=0,
        cobertura_sessao=0.0,
        consulta_efetiva={},
        faixas_citadas=(),
    )


def _registrar_turno(inicio, **etapas):
    observabilidade.registrar_turno(**etapas, duracao_ms=(time.monotonic() - inicio) * 1000)
