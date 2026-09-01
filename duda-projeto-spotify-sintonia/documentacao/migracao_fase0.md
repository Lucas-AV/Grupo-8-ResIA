# Migração da Fase 0

Origem analisada: `C:\Users\eduar\Documents\projeto-spotify-unb`.

Nenhum segredo, cache, build ou snapshot completo do legado foi copiado.

| Componente antigo | Classificação | Destino/decisão |
|---|---|---|
| CSS, layout, favicon e cards | REAPROVEITAR | Migrados e reorganizados em `frontend/`; dados exibidos são explicitamente ilustrativos. |
| `app/page.tsx` como orquestrador | REESCREVER | Não copiado. TODO em Orquestrador e frontend. |
| OAuth PKCE no navegador | REAPROVEITAR | Extraído para `frontend/lib/spotify/oauth.ts`. |
| Busca Spotify como recomendador | REESCREVER | Não copiada; causava resultados repetitivos e ignorava ML/contexto. |
| Importação parcial de perfil | REESCREVER | Não copiada; TODO de paginação e proveniência em Coleta Spotify. |
| Tipos de faixa e atributos | REAPROVEITAR | Portados para contratos Pydantic em `backend/modelos/`. |
| Normalização e adapter Kaggle | REAPROVEITAR | Portados para `backend/utilitarios/` com testes previstos. |
| Similaridade/scoring/explicação antigos | REESCREVER | Não copiados; estavam desconectados do runtime e sem calibração. |
| Conversa por regex e respostas fixas | REESCREVER | Não copiada; TODO nos agentes Orquestrador e Conversacional. |
| Structured output do LLM | REAPROVEITAR como conceito | Contrato `Interpretacao` preservado; chamada ao LLM ainda não implementada. |
| Threshold de confiança | REAPROVEITAR | Política de 90% em `confianca_hitl/politica.py`. |
| Schema/fila de revisão | REAPROVEITAR | Conceitos migrados para SQLite; ciclo de correção permanece TODO. |
| Segurança e pseudonimização | REAPROVEITAR como princípio | Documentada e representada no schema; implementação futura. |
| Clustering coletivo por gêneros | DESCARTAR do núcleo | Não copiado; não correspondia ao clustering de faixas por áudio. |
| D1, Drizzle e rotas Sites | DESCARTAR | Substituídos por estrutura Python + SQLite. |
| Test harness | REAPROVEITAR | Novos espaços de teste e casos básicos de migração. |
| Testes superficiais de recomendação | REESCREVER | TODO de testes de novidade, repetição e conversa multivolta. |
| `.next`, `.vinext`, `.wrangler`, `dist`, `node_modules` | DESCARTAR | Artefatos gerados não migrados. |
| `.env.local` | DESCARTAR | Segredos antigos não foram lidos nem copiados. |

## Diferença importante

O frontend atual não promete funcionalidades indisponíveis. O protótipo antigo afirmava evitar músicas conhecidas com base em uma amostra pequena; a nova interface marca seus exemplos como não reais até que o backend seja validado.

