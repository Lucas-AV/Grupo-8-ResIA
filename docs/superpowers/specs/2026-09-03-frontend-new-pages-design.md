# Novas páginas do frontend do agente_conversacional

## Contexto

`agente_conversacional/frontend/` é hoje um SPA de arquivo único (`index.html`,
sem framework/bundler): tela de chat + painel overlay "Explorar Spotify"
(Épico 13) + modal de login por QR code (13.13). Não existem páginas
dedicadas para perfil, histórico navegável, configurações, transparência ou
onboarding — o que existe hoje (perfil de gosto, diversidade/cobertura,
consentimento) fica só em log de backend ou em texto inline pequeno no chat.

Escopo: **apenas** `agente_conversacional/frontend/` — nunca
`spotify_explorer/frontend/` (ferramenta de dev, ver
[[feedback_epico4_frontend_isolation]]).

## Padrão de navegação

Todas as páginas novas seguem o padrão já usado pelo Explorer: um botão no
header abre um painel overlay sobre o chat, sem SPA router e sem reload —
consistente com o restante do código (HTML/CSS/JS puro). Nenhuma página
introduz roteamento client-side ou URL própria.

## Épico A — Personalização & Insights

Expõe ao usuário dados que o backend já calcula mas hoje só existem em log
interno ou texto inline no chat.

### A.1 — Meu Perfil
Painel com o perfil de gosto (`recomendacao/perfil.py:calcular_perfil_usuario`)
e o histórico de diversidade/cobertura das recomendações da sessão.

**Depende de backend novo:** hoje `calcular_perfil_usuario` só roda
internamente no fluxo OAuth (`spotify_auth/routes.py`, blend 70/30 na busca)
e nunca é devolvido ao cliente. Precisa de um `GET /perfil?session_id=...`
que rode o mesmo cálculo e devolva o vetor de features normalizado (ou
`null` se não houver histórico casado) para o frontend exibir.

### A.2 — Minhas Conversas
Painel listando o histórico completo de turnos da sessão de forma
navegável (hoje só rola inline no chat). Reusa `GET /chat/historico`
(já existe, Épico 3/4.6) — sem backend novo.

### A.3 — Descobertas
Painel de gêneros/artistas novos ao longo da sessão, derivado dos campos
`diversidade_generos`/`cobertura_sessao` já devolvidos por `POST /chat`
(Épico 6/KAN-11). Sem backend novo — acumula client-side a partir das
respostas já recebidas, mesmo padrão de `faixasMostradasSessao` em `app.js`.

## Épico B — Gestão & Transparência

### B.1 — Configurações
Painel de preferências: excluir faixas explícitas por padrão (hoje é
parâmetro de busca sem controle de UI), tema (centraliza o toggle que hoje
vive isolado no header). Client-side only, `localStorage` — sem backend novo.

### B.2 — Como Funciona
Painel explicando os sinais de ranking (popularidade como um sinal entre
outros, já mencionado em `criarResumoDiversidadeECobertura`) e a política de
privacidade — hoje documentada só em
`agente_conversacional/docs/KAN-11_ETICA_E_OBSERVABILIDADE.md`, nunca
exposta ao usuário final da aplicação.

### B.3 — Minhas Playlists (ResIA)
Painel listando as playlists criadas via "Salvar no Spotify"
(`POST /playlist/criar`), diferenciando das demais playlists que aparecem
no Explorer (`GET /explorer/me/playlists`, que lista todas as playlists da
conta, não só as geradas pelo ResIA). Client-side only — grava
id/nome/link da playlist no `localStorage` no momento em que
`handleSalvarSpotify` recebe sucesso; sem persistência server-side (evita
escopo novo de storage no backend).

## Épico C — Entrada e Onboarding

### C.1 — Boas-vindas / Conectar
Tela de entrada unificando as duas formas de login com Spotify que hoje
são botões soltos e sem contexto no header: redirect (`GET /auth/login`,
4.4) e QR code (`GET /auth/qr`, 13.13). Explica o que cada opção libera
(Explorer, personalização via perfil, salvar playlist) antes do usuário
escolher.

### C.2 — Onboarding guiado
Tour curto para o usuário novo, expandindo o `#hero-empty-state` atual
(4.12, só chips de sugestão) com poucos passos mostrando o chat, os cards
de faixa e o botão do Explorer. Aparece só na primeira visita, controlado
por flag em `localStorage` (mesmo padrão de `getStoredTheme`/
`saveStoredTheme` já usado pro tema).

## Fora de escopo

- Roteamento client-side / URLs próprias por página.
- Qualquer mudança em `spotify_explorer/` (dev tool, isolado do produto).
- Persistência server-side de playlists criadas (B.3 é client-side).
- Internacionalização (todas as páginas em pt-BR, como o resto do produto).

## Testes

Cada painel novo segue o padrão já usado por `trackCard.js`/`explorer.js`:
`node --check` no arquivo do componente + teste manual no navegador (o
projeto não tem testes de frontend automatizados hoje, só `node --check`
de sintaxe — ver `test_spotify_routes.py`/`test_chat_endpoint.py` para os
testes automatizados existentes, que cobrem só backend). A.1 (`GET
/perfil`) precisa de teste de backend novo, mesmo padrão de
`test_spotify_routes.py`.
