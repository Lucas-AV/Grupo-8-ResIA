# Meu Perfil — dados de conta Spotify

## Problema

A aba "Meu Perfil" (painel lateral, `agente_conversacional/frontend/index.html:353-362`) não retorna nada útil após o login. `renderProfilePanel()` (`app.js:1349-1378`) chama `buscarPerfil(sessionId)` → `GET /perfil?session_id=...`, rota que não existe em nenhum router do backend. Toda chamada cai no `.catch`, mostrando "Não foi possível carregar o perfil agora."

## Escopo

Repurpose o painel "Meu Perfil" para exibir **dados de conta do Spotify** do usuário logado (nome, avatar, seguidores, país, plano, link externo), não o vetor de gosto musical (fora de escopo — pertence a KAN-46/47, que já tem worktree próprio e desatualizado; não duplicar).

## Fonte de dados

`GET /explorer/me?session_id=...` (`spotify_auth/explorer_routes.py:199-202`), já existente e já usado no header (`buscarPerfilSpotify`, `app.js:384-397`) e na aba "Explorar → Meus dados" (`components/explorer.js:351-400`, ticket 13.10). Proxy verbatim do `GET /v1/me` do Spotify — sem endpoint novo.

Campos usados: `display_name`, `images[0].url`, `followers.total`, `country`, `product`, `external_urls.spotify`. Escopo OAuth atual (`spotify_auth/config.py:10-15`) não pede `user-read-email`, então `email` normalmente vem ausente — tratado como opcional, nunca como erro.

## Fluxo

1. `renderProfilePanel()` chama `verificarStatusSpotify(currentSessionId)` (já existe, `app.js:359-374`).
2. Não conectado → estado vazio em texto, apontando pro botão "Conectar Spotify" já existente no header (decisão de implementação: evita duplicar um CTA clicável dentro do painel — ver plano).
3. Conectado → `fetch('${API_BASE_URL}/explorer/me?session_id=...')`.
   - `401` (`spotify_nao_autenticado`) → mesmo estado do passo 2 (fail-safe, sessão pode ter expirado entre o check e o fetch).
   - Erro de rede/outro status → `renderPanelMessage(..., 'panel-state-error')`, mesmo padrão dos outros painéis.
4. Sucesso → renderiza cartão de conta: avatar (fallback iniciais se sem imagem), nome, seguidores, país, plano (`product` traduzido: `premium`→"Premium", `free`→"Gratuito", outro→valor bruto), link "Ver no Spotify" (`external_urls.spotify`, `target="_blank" rel="noopener"`).

## Fora de escopo

- Vetor de gosto musical / centroide (KAN-46/47).
- Qualquer mudança em `spotify_auth/routes.py` (`login_start`/`callback`) — outra sessão está mexendo lá (redirect_uri dinâmico); tocar nesses métodos geraria conflito de merge.
- Novo endpoint de backend.
- Mudanças em `spotify_explorer/` (ferramenta de dev separada).

## Arquivos tocados

- `agente_conversacional/frontend/app.js` — reescreve `renderProfilePanel()`; `buscarPerfil()`/rota `/perfil` removida do fluxo (função fica órfã — remover se não houver outro chamador).
- `agente_conversacional/frontend/index.html` — kicker do painel (`"Personalização"` → texto condizente com conta, ex. `"Sua conta"`), linha 356.
- `agente_conversacional/frontend/style.css` — classes novas/reaproveitadas para o cartão de conta (inspirado em `.explorer-me-profile`, já existente em `components/explorer.js:369-375`).

## Testes

Sem suíte de testes de frontend automatizada no projeto (confirmado — nenhum `.test.js`/jest/vitest em `frontend/`). Validação manual: abrir app, conectar Spotify, abrir "Meu Perfil", conferir dados; deslogar/sessão sem token, conferir CTA de conexão; simular erro de rede (offline) e conferir estado de erro.
