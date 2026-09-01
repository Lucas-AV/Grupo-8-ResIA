# Backend

O backend Python concentra as regras de negócio e expõe a API HTTP em `backend/api.py`.
O frontend não armazena tokens Spotify, não treina clusters e não decide a confiança.

## Camadas

- `agentes/`: coordenação por responsabilidade.
- `integracoes/spotify/`: OAuth, chamadas autorizadas, catálogo local de atributos e modo demo.
- `nucleo_ml/`: artefatos e algoritmos de clustering (Fase 4).
- `modelos/`: contratos compartilhados.
- `persistencia/`: futura camada SQLite.
- `configuracao/`: variáveis de ambiente tipadas.

## Executar a API

1. Copie `.env.example` para `.env` e mantenha `SPOTIFY_MODO=demo` para uma demonstração sem credenciais.
2. Ative o ambiente virtual e execute `python -m uvicorn backend.api:app --reload --port 8000`.
3. Acesse `http://127.0.0.1:8000/docs` para experimentar os endpoints.

O modo `real` exige as credenciais e a URL de retorno cadastradas no painel do Spotify. Os tokens ficam somente na memória do processo, associados a um cookie HTTP-only; nunca são enviados ao LLM nem gravados em logs.
