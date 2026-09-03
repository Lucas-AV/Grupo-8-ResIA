# Spotify API Explorer — Migração do Frontend pra Vue.js

**Data:** 2026-09-01
**Branch:** `feature/spotify-api-explorer` (continuação do PR #4, ainda não mergeado)

## Objetivo

Substituir o frontend vanilla JS (`templates/index.html` + `static/app.js` +
`static/style.css`, construídas nas Tasks 9-11 do spec original) por uma
Single Page Application em Vue 3, com Vite como build tool. Migração de
tecnologia pura — **sem** mudança de escopo funcional: as mesmas 5 abas
(Search, Track & Audio, Artist, Recommendations, Meus dados), os mesmos
campos, o mesmo comportamento observável, incluindo o tratamento de erro
de rede/JSON inválido já corrigido em revisões anteriores.

O backend Flask (`app.py`, `spotify_client.py`, `user_auth.py`) e todos os
18 endpoints `/api/*`, `/login`, `/callback`, `/logout` continuam
exatamente como estão — essa migração não altera nenhuma lógica de
negócio, só a camada de apresentação e 3 pontos pequenos de integração
descritos abaixo.

## Por que Vite (com npm) em vez de Vue via CDN

Decisão explícita do usuário: quer o setup padrão da comunidade Vue
(single-file components `.vue`, build step com Vite), mesmo que isso
introduza Node/npm como toolchain novo num repositório hoje 100% Python.
Trade-off aceito conscientemente — não é a opção mais simples possível,
mas é a mais alinhada ao ecossistema Vue e à forma como o usuário quer
manter esse código no futuro.

## Fluxo de desenvolvimento

Dois modos suportados:

1. **Dev com hot-reload** (uso ativo, editando o frontend):
   `npm run dev` sobe o Vite em `http://127.0.0.1:5173` com hot-reload;
   `python app.py` continua rodando o Flask em `http://127.0.0.1:5000`.
   O Vite proxeia `/api/*`, `/login`, `/logout`, `/callback` pro Flask —
   o navegador acessa só `:5173`, nunca precisa saber que o backend está
   em outra porta.
2. **Build único** (só rodar/testar, sem mexer no frontend):
   `npm run build` gera os arquivos estáticos, e `python app.py` sozinho
   já serve tudo (API + frontend) em `:5000`. É o modo equivalente ao que
   existia antes da migração (1 comando, 1 porta).

## Integração com o backend (as 3 mudanças no Flask)

### 1. `index()` serve o build do Vite

`vite.config.js` builda para `spotify_explorer/static/frontend/`
(dentro da pasta `static/` que o Flask já serve automaticamente, com
`base: '/static/frontend/'` pra as URLs internas dos assets baterem). A
rota `/` deixa de usar `render_template` com Jinja e passa a ler o
arquivo `static/frontend/index.html` construído pelo Vite e devolvê-lo
como está.

**Caso de borda:** se `static/frontend/index.html` não existir ainda
(checkout limpo, antes do primeiro `npm run build` — inclusive em CI/
`pytest`, que não roda `npm`), a rota devolve uma página simples com
status 200 explicando "rode `npm run build` primeiro", em vez de
quebrar. Isso mantém `test_index_returns_200` passando sem alteração.

### 2. Nova rota `GET /api/config`

Substitui o `{% if missing_credentials %}` do template Jinja antigo.
Devolve `{"missing_credentials": bool}` — `true` quando
`SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` não estão configurados. O
Vue chama essa rota ao montar e mostra o banner de aviso se necessário.

### 3. `/callback` redireciona pra `FRONTEND_URL` (nova config, default `/`)

Hoje o `/callback` redireciona pra `url_for("index")` (a própria rota
Flask). Como agora o app pode estar rodando em `:5173` (modo dev) ou
servido pelo próprio Flask em `/` (modo build), o destino do redirect
vira configurável via `FRONTEND_URL` no `.env` (novo, default `"/"` —
mesmo comportamento de hoje quando não configurado). O `auth_error`
continua sendo passado como query param na URL de redirect, e o Vue lê
`window.location.search` ao montar em vez de receber via Jinja.

Com o default `"/"`, os testes existentes de `/callback`
(`test_callback_exchanges_code_and_redirects_home`,
`test_callback_with_spotify_error_redirects_with_auth_error`, etc.)
continuam passando sem nenhuma alteração — só muda o comportamento
observável quando `FRONTEND_URL` é explicitamente setado (uso: rodar
`npm run dev` com `FRONTEND_URL=http://127.0.0.1:5173` no `.env`).

`/login` e `/logout` continuam rotas Flask normais, sem mudança nenhuma
— o proxy do Vite (modo dev) ou a mesma origem (modo build) faz o link
relativo `<a href="/login">` funcionar nos dois casos.

`SPOTIFY_REDIRECT_URI` **não muda** — continua
`http://127.0.0.1:5000/callback` nos dois modos, porque é sempre o
Flask (porta fixa 5000) que recebe o redirect do OAuth da Spotify, nunca
o Vite. Não precisa reconfigurar nada no Spotify Developer Dashboard.

## Estrutura de arquivos

```
spotify_explorer/
  app.py                    # 3 mudanças pequenas (acima); resto igual
  spotify_client.py          # inalterado
  user_auth.py                # inalterado
  test_*.py                    # inalterados, exceto: 1 novo teste pro
                                 # /api/config, 1 novo teste pro redirect
                                 # do /callback respeitando FRONTEND_URL
  requirements.txt              # inalterado
  .env.example                   # + FRONTEND_URL=
  README.md                       # atualizado: setup do frontend (npm
                                    # install, npm run dev vs npm run build)
  frontend/                        # NOVO projeto Vite
    package.json
    package-lock.json                # commitado
    vite.config.js
    index.html                        # entry HTML do Vite (não é mais
                                        # servido pelo Flask via Jinja)
    src/
      main.js                          # createApp(App).mount('#app')
      App.vue                           # header, banners, nav de abas,
                                          # monta a aba ativa
      style.css                          # migrado de static/style.css
      composables/
        useApi.js                         # equivalente a fetchJSON/
                                            # callEndpoint: distingue
                                            # falha de rede de resposta
                                            # não-JSON, mesma semântica
                                            # já corrigida no app.js atual
        useAuthStatus.js                   # estado reativo compartilhado
                                            # (logado?/perfil), usado no
                                            # header e na aba Meus dados
      components/
        JsonViewer.vue                      # renderizador recursivo
                                              # colapsável (substitui
                                              # renderValue/renderContainer)
      tabs/
        SearchTab.vue
        TrackTab.vue
        ArtistTab.vue
        RecommendationsTab.vue
        MeusDadosTab.vue

  templates/index.html        # REMOVIDO
  static/app.js                # REMOVIDO
  static/style.css              # REMOVIDO
  static/frontend/               # gerado pelo `npm run build`,
                                   # gitignored (como site/dist/)
```

Raiz do repo — `.gitignore` ganha:
```
spotify_explorer/frontend/node_modules/
spotify_explorer/static/frontend/
```

## Sem gerenciamento de estado global nem roteamento

`Pinia` e `vue-router` **não** entram — YAGNI. O app é 5 abas dentro de
uma página só (nunca muda de URL por aba, igual hoje), e o único estado
compartilhado entre componentes é "usuário logado?", que cabe
tranquilamente num composable simples (`useAuthStatus.js`, um objeto
`reactive()` exportado) sem precisar de uma lib de estado.

## Sem testes JS (Vitest)

Consistente com a convenção já estabelecida nas Tasks 9-11 do spec
original: frontend verificado estruturalmente (build passa sem erro,
`npm run build` gera os arquivos esperados) e manualmente pelo usuário
com credenciais reais — não por uma suíte automatizada de testes JS. Se
o grupo quiser adicionar Vitest depois, é um step separado, fora de
escopo aqui.

## Componentes e responsabilidades

- **`App.vue`** — layout raiz: header (nome do usuário logado, se houver),
  banner de credenciais faltando (via `/api/config`), banner de
  `auth_error` (via query string), navegação das 5 abas, renderiza a aba
  ativa.
- **`useApi.js`** — expõe uma função `callApi(url, options)` que faz
  `fetch`, distingue falha de rede (`status: 0`, mensagem "Erro de
  rede") de resposta HTTP real com corpo não-JSON (mostra o status real
  + "não é JSON válido"), e devolve `{ok, status, data}` — espelhando o
  par `fetchJSON`/`callEndpoint` que já existe em `app.js`.
- **`useAuthStatus.js`** — `reactive({loggedIn: false, profile: null})` +
  função `refresh()` que chama `GET /api/me` via `useApi`, atualiza o
  estado, e trata falha de rede/JSON exatamente como o `loadUserStatus`
  atual (cai pro estado deslogado silenciosamente — é uma checagem de
  status em background, não uma ação do usuário). `App.vue` chama
  `refresh()` uma vez no `onMounted`, igual o `loadUserStatus()` que
  hoje roda no `DOMContentLoaded`.
- **`JsonViewer.vue`** — recebe uma prop `data` (qualquer JSON), renderiza
  recursivamente como `<details>`/`<summary>` colapsáveis, idêntico ao
  `renderValue`/`renderContainer` atual — inclusive o cuidado de nunca
  usar `v-html`/interpolação insegura (texto de tracks/playlists vem da
  API da Spotify, pode conter qualquer coisa).
- **`SearchTab.vue` / `TrackTab.vue` / `ArtistTab.vue` /
  `RecommendationsTab.vue`** — um componente por aba, replicando
  exatamente os campos e chamadas de `initSearchForm`/`initTrackForm`/
  `initArtistForm`/`initRecommendationsForm` do `app.js` atual
  (`Track`/`Artist` seguem fazendo múltiplas chamadas em paralelo e
  agregando o resultado num só `JsonViewer`, com o status refletindo o
  pior resultado entre as chamadas — mesmo comportamento pós-fix atual).
- **`MeusDadosTab.vue`** — usa `useAuthStatus`, mostra botão de login se
  deslogado, ou top tracks/artists (3 janelas de tempo) + curtidas +
  tocadas recentemente se logado — replica `initTopForm`/
  `initSavedTracksButton`/`initRecentlyPlayedButton`.

## Fora de escopo

- Qualquer mudança visual/UX além da migração 1:1 (usuário escolheu
  paridade de features, não polimento)
- Pinia, vue-router, Vitest
- Deploy — continua ferramenta local
- Mudança em qualquer rota `/api/*` existente ou na lógica de
  `spotify_client.py`/`user_auth.py`
