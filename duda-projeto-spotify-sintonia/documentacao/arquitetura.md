# Arquitetura inicial

O projeto separa interface, coordenação, dados, ML, integrações e controle de qualidade.

```text
Frontend Next.js
      │ contratos HTTP futuros
      ▼
Backend Python / Orquestrador
      ├── agentes de domínio
      ├── integração Spotify
      ├── núcleo ML
      ├── SQLite
      └── confiança e revisão humana
```

## Regras

- O frontend apresenta dados; não decide recomendação ou confiança.
- O LLM não calcula clustering, ranking ou score de confiança.
- Somente Orquestrador e Conversacional poderão usar LLM.
- Tokens, histórico bruto e vetores privados não são enviados ao LLM.
- Toda saída passa pelo agente de confiança.
- O notebook é a fonte reproduzível do ETL, treinamento, hipóteses e métricas acadêmicas.

TODO: os endpoints FastAPI serão definidos apenas quando os contratos e fluxos forem implementados na Fase 3.

