"""Parser tolerante a texto ao redor do JSON devolvido pelo LLM — extrai o
primeiro bloco `{...}` valido de uma resposta antes de desistir (ticket
2.2; reaproveitado pela geracao, ticket 2.5, que tambem pede JSON pro
LLM). Cobre o edge case "LLM devolve texto ao redor do JSON em vez de so
o JSON" (secao 7 do pipeline)."""

import json


def extrair_primeiro_json(texto):
    """Devolve o primeiro objeto JSON (`dict`) valido encontrado em
    `texto`, tentando decodificar a partir de cada ocorrencia de `{`. Se
    nenhum bloco valido for encontrado (ou `texto` nao for string),
    devolve None — o chamador trata isso como falha da etapa."""
    if not isinstance(texto, str):
        return None

    decoder = json.JSONDecoder()
    for indice, caractere in enumerate(texto):
        if caractere != "{":
            continue
        try:
            objeto, _ = decoder.raw_decode(texto, indice)
        except ValueError:
            continue
        if isinstance(objeto, dict):
            return objeto
    return None
