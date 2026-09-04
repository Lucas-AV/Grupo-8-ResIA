# Meu Perfil — Dados de Conta Spotify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer a aba "Meu Perfil" exibir os dados de conta do Spotify do usuário logado (nome, avatar, seguidores, país, plano, link externo) em vez de tentar (e falhar) carregar um vetor de gosto musical de uma rota inexistente.

**Architecture:** `renderProfilePanel()` em `agente_conversacional/frontend/app.js` passa a checar `verificarStatusSpotify()` e, se conectado, buscar `GET /explorer/me` (endpoint já existente, sem mudança de backend) e renderizar os campos relevantes. Sem conexão ou erro, mostra estado vazio/erro reaproveitando `renderPanelMessage`.

**Tech Stack:** JS vanilla (sem framework/bundler), FastAPI (backend, inalterado). Sem suíte de testes automatizada no frontend — verificação manual via `serve.ps1` + backend local.

**Não fazer:** não mexer em `spotify_auth/routes.py` (`login_start`/`callback` — outra sessão está com mudanças em andamento ali, redirect_uri dinâmico); não implementar o vetor de gosto (KAN-46/47); não criar endpoint novo.

---

### Task 1: CSS — estilos para o cartão de conta

**Files:**
- Modify: `agente_conversacional/frontend/style.css` (adicionar após a regra `.playlist-link:hover`, linha 1905)

- [ ] **Step 1: Adicionar as classes novas**

Inserir logo após a linha 1905 (`.playlist-link:hover { text-decoration: underline; }`):

```css

/* Painel "Meu Perfil" — dados de conta Spotify (reaproveita .explorer-me-profile/
   .explorer-me-avatar de components/explorer.js, ticket 13.10) */
.profile-account-avatar-fallback {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface-elevated);
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}
.profile-account-meta {
  display: grid;
  gap: 10px;
  padding: 18px 0;
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 16px;
}
.profile-account-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.profile-account-row span {
  color: var(--text-secondary);
  font-size: 0.8rem;
}
.profile-account-row strong {
  color: var(--text-primary);
  font-size: 0.8rem;
}
```

- [ ] **Step 2: Commit**

```bash
git add agente_conversacional/frontend/style.css
git commit -m "style(agente): adiciona classes do cartao de conta no painel Meu Perfil"
```

---

### Task 2: JS — reescrever `renderProfilePanel()`

**Files:**
- Modify: `agente_conversacional/frontend/app.js:1349-1378` (função `renderProfilePanel`)
- Modify: `agente_conversacional/frontend/app.js:267-269` (remover `buscarPerfil`, órfã após a troca)

- [ ] **Step 1: Confirmar que `buscarPerfil` não é usada em mais nenhum lugar**

Run: `grep -rn "buscarPerfil(" agente_conversacional/frontend/`
Expected: só a ocorrência dentro de `renderProfilePanel` (será removida no próximo passo) e a definição da função em si.

- [ ] **Step 2: Remover a função `buscarPerfil` (linhas 267-269) e sua exportação**

Remover o bloco:

```javascript
async function buscarPerfil(sessionId) {
  return buscarJson(`/perfil?session_id=${encodeURIComponent(sessionId)}`);
}
```

Depois localizar o objeto de exports perto do fim do arquivo (`grep -n "buscarPerfil,"`) e remover a linha `buscarPerfil,` de dentro dele (mantendo `buscarPerfilSpotify,` intacto — são funções diferentes).

- [ ] **Step 3: Substituir `renderProfilePanel()` (linhas 1349-1378)**

Trocar a função inteira por:

```javascript
function renderProfilePanel() {
  const content = panelDefinitions.profile.content;
  renderPanelMessage(content, 'Carregando sua conta...', 'panel-state-loading');

  verificarStatusSpotify(currentSessionId).then((conectado) => {
    if (!conectado) {
      renderPanelMessage(
        content,
        'Conecte sua conta do Spotify (botão "Conectar Spotify" no topo) para ver seus dados aqui.',
        'panel-state-empty'
      );
      return;
    }

    fetch(`${API_BASE_URL}/explorer/me?session_id=${encodeURIComponent(currentSessionId)}`)
      .then((response) => {
        if (response.status === 401) {
          renderPanelMessage(
            content,
            'Conecte sua conta do Spotify (botão "Conectar Spotify" no topo) para ver seus dados aqui.',
            'panel-state-empty'
          );
          return null;
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((conta) => {
        if (!conta) return;
        renderContaSpotify(content, conta);
      })
      .catch((error) => {
        console.warn('Falha ao carregar dados da conta Spotify:', error);
        renderPanelMessage(content, 'Não foi possível carregar sua conta agora.', 'panel-state-error');
      });
  });
}

const PRODUTO_SPOTIFY_LABEL = { premium: 'Premium', free: 'Gratuito' };

function renderContaSpotify(content, conta) {
  const avatarUrl = conta.images && conta.images[0] && conta.images[0].url;
  const nome = conta.display_name || 'Você';
  const avatarHtml = avatarUrl
    ? `<img src="${escapeHtml(avatarUrl)}" alt="" class="explorer-me-avatar">`
    : `<div class="profile-account-avatar-fallback">${escapeHtml(nome.trim().charAt(0).toUpperCase() || '?')}</div>`;
  const seguidores = conta.followers && typeof conta.followers.total === 'number'
    ? `${conta.followers.total} seguidores`
    : '';
  const plano = conta.product ? (PRODUTO_SPOTIFY_LABEL[conta.product] || conta.product) : null;
  const linkExterno = conta.external_urls && conta.external_urls.spotify;

  content.innerHTML = `
    <section class="profile-summary">
      <span class="panel-kicker">Sua conta Spotify</span>
    </section>
    <div class="explorer-me-profile">
      ${avatarHtml}
      <div>
        <strong>${escapeHtml(nome)}</strong>
        ${seguidores ? `<span>${escapeHtml(seguidores)}</span>` : ''}
      </div>
    </div>
    <div class="profile-account-meta">
      ${conta.country ? `<div class="profile-account-row"><span>País</span><strong>${escapeHtml(conta.country)}</strong></div>` : ''}
      ${plano ? `<div class="profile-account-row"><span>Plano</span><strong>${escapeHtml(plano)}</strong></div>` : ''}
    </div>
    ${linkExterno ? `<a href="${escapeHtml(linkExterno)}" target="_blank" rel="noopener noreferrer" class="playlist-link">Ver perfil no Spotify ↗</a>` : ''}
  `;
}
```

Notas de implementação:
- `escapeHtml` e `renderPanelMessage` já existem no arquivo — não redefinir.
- `verificarStatusSpotify` e `currentSessionId` já existem — não redefinir.
- `PRODUTO_SPOTIFY_LABEL` fica em module scope (fora da função), do lado de fora, no mesmo nível de outras constantes do arquivo — colocar logo acima de `renderContaSpotify`.

- [ ] **Step 4: Commit**

```bash
git add agente_conversacional/frontend/app.js
git commit -m "fix(agente): aba Meu Perfil mostra dados de conta Spotify em vez de rota /perfil inexistente"
```

---

### Task 3: HTML — ajustar o texto do painel

**Files:**
- Modify: `agente_conversacional/frontend/index.html:353-362`

- [ ] **Step 1: Trocar o kicker**

Em `index.html:356`, trocar:

```html
        <span class="panel-kicker">Personalização</span>
```

por:

```html
        <span class="panel-kicker">Sua conta</span>
```

(O `<h2>` `Meu Perfil` na linha seguinte não muda — é o nome da aba, continua correto.)

- [ ] **Step 2: Commit**

```bash
git add agente_conversacional/frontend/index.html
git commit -m "chore(agente): atualiza rotulo do painel Meu Perfil para refletir dados de conta"
```

---

### Task 4: Verificação manual (sem suíte automatizada de frontend)

**Files:** nenhum (só validação)

- [ ] **Step 1: Subir o backend**

Run: `cd agente_conversacional && uvicorn app:app --reload`
Expected: servidor sobe em `http://127.0.0.1:8000` sem erro (precisa de `.env` com `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` válidos, ver `.env.example`).

- [ ] **Step 2: Subir o frontend**

Run: `cd agente_conversacional/frontend && .\serve.ps1`
Expected: serve em `http://127.0.0.1:8080`.

- [ ] **Step 3: Verificar estado "não conectado"**

Abrir `http://127.0.0.1:8080` numa aba anônima (sem sessão Spotify prévia), clicar no botão de perfil (ícone de pessoa no header, `#btn-profile-panel`).
Expected: painel "Meu Perfil" abre mostrando a mensagem "Conecte sua conta do Spotify (botão "Conectar Spotify" no topo) para ver seus dados aqui." — sem erro no console.

- [ ] **Step 4: Verificar estado conectado**

Clicar em "Conectar Spotify", completar o OAuth. Depois de conectado, abrir "Meu Perfil" de novo.
Expected: mostra avatar (ou inicial, se a conta não tiver foto pública), nome, seguidores (se houver), país, plano, e link "Ver perfil no Spotify ↗" que abre `open.spotify.com` numa nova aba.

- [ ] **Step 5: Verificar estado de erro de rede**

Com a conta conectada, parar o backend (`Ctrl+C` no uvicorn) e reabrir o painel "Meu Perfil" (ou fechar e abrir de novo pra forçar novo fetch).
Expected: mostra "Não foi possível carregar sua conta agora." (classe `panel-state-error`), sem quebrar o resto da UI.

- [ ] **Step 6: Conferir que o vetor de gosto antigo não aparece em nenhum lugar residual**

Run: `grep -rn "vetor_features_normalizado\|perfil_usuario\|renderMetricHistory" agente_conversacional/frontend/app.js`
Expected: `renderMetricHistory` continua existindo (usada em outro lugar — não remover), mas não é mais chamada dentro de `renderProfilePanel`/`renderContaSpotify`. Se `renderMetricHistory` não for chamada em nenhum outro lugar do arquivo, é código morto — não remover neste plano (fora de escopo; anotar para o dev revisar depois).
