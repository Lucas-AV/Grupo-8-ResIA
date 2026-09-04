/**
 * app.js — Controlador Principal da Interface de Chat (Ticket 4.1)
 * Grupo 8 ResIA — Agente Conversacional de Recomendação Musical
 * Identidade Visual Spotify + Referências UI (Convora, Knotes, Absorva+)
 */

// ==========================================
// 1. Módulo de Sessão e Persistência
// ==========================================
const SESSION_STORAGE_KEY = 'resia_chat_session_id';
const HISTORY_STORAGE_PREFIX = 'resia_chat_history_';
const SETTINGS_STORAGE_KEY = 'resia_settings';
const PLAYLISTS_STORAGE_KEY = 'resia_created_playlists';

function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

function setCookie(name, value, days = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function getSessionId() {
  let sessionId = null;
  try {
    sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  } catch (e) {
    console.warn('Falha ao ler localStorage:', e);
  }

  if (!sessionId) {
    sessionId = getCookie(SESSION_STORAGE_KEY);
  }

  if (!sessionId) {
    sessionId = generateUUID();
    saveSessionId(sessionId);
  }

  return sessionId;
}

function saveSessionId(sessionId) {
  if (!sessionId) return;
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  } catch (e) {
    console.warn('Falha ao salvar no localStorage:', e);
  }
  try {
    setCookie(SESSION_STORAGE_KEY, sessionId, 7);
  } catch (e) {
    console.warn('Falha ao salvar no cookie:', e);
  }
}

function resetSession() {
  const newSessionId = generateUUID();
  saveSessionId(newSessionId);
  return newSessionId;
}

function saveChatHistory(sessionId, messages) {
  if (!sessionId) return;
  try {
    localStorage.setItem(HISTORY_STORAGE_PREFIX + sessionId, JSON.stringify(messages));
  } catch (e) {
    console.warn('Falha ao salvar histórico no localStorage:', e);
  }
}

function loadChatHistory(sessionId) {
  if (!sessionId) return [];
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_PREFIX + sessionId);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.warn('Falha ao carregar histórico do localStorage:', e);
    return [];
  }
}

// ==========================================
// 2. Módulo de API e Catálogo Demo
// ==========================================
const API_BASE_URL =
  window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
    ? ''
    : 'http://127.0.0.1:8000';

const OFFLINE_CATALOGO = {
  pagode: [
    { track_id: '3n3Ppam7vgaVa1iaRUc9Lp', nome: 'Deixa Acontecer', artista: 'Grupo Revelação', album: 'Ao Vivo', genero: 'pagode' },
    { track_id: '2OzhsB92lF4N4Ynxy7P9hP', nome: 'Pé Na Areia', artista: 'Diogo Nogueira', album: 'Munduê', genero: 'pagode' },
    { track_id: '5gB82p5T9z7Xw8Q7F1oE7B', nome: 'Falta Você', artista: 'Thiaguinho', album: 'Meu Nome É Thiago André', genero: 'pagode' },
  ],
  rock: [
    { track_id: '08mG3Y1vljYA6bvNXEsOh9', nome: "Sweet Child O' Mine", artista: "Guns N' Roses", album: 'Appetite For Destruction', genero: 'rock' },
    { track_id: '2VxeLyX666F8uXCJ0dZF8B', nome: "Livin' On A Prayer", artista: 'Bon Jovi', album: 'Slippery When Wet', genero: 'rock' },
    { track_id: '7w8OXQ8oo6b5gPshx842Xk', nome: 'Back In Black', artista: 'AC/DC', album: 'Back In Black', genero: 'rock' },
  ],
  chill: [
    { track_id: '3U4isOIWM3VvDubwSI3y7a', nome: 'Weightless', artista: 'Marconi Union', album: 'Weightless (Vol. 2)', genero: 'chill' },
    { track_id: '4GfK1A2GZJvD1YwV61y6hA', nome: 'Sunset Lover', artista: 'Petit Biscuit', album: 'Presence', genero: 'chill' },
    { track_id: '1A7F0J3F5F4h8C4G7x1A2B', nome: 'Coffee', artista: 'beabadoobee', album: 'Loveworm', genero: 'chill' },
  ],
  pop: [
    { track_id: '0VjIjW4GlUZAMYd2vXMi3b', nome: 'Blinding Lights', artista: 'The Weeknd', album: 'After Hours', genero: 'pop' },
    { track_id: '4Dvkj6JhhA12EX05fT7y2e', nome: 'As It Was', artista: 'Harry Styles', album: "Harry's House", genero: 'pop' },
    { track_id: '1BxfuPKGuaTgP7aM0XbdMe', nome: 'Levitating', artista: 'Dua Lipa', album: 'Future Nostalgia', genero: 'pop' },
  ],
  mpb: [
    { track_id: '4d1X9F8j4h2k8f1g3h5j6k', nome: 'Oceano', artista: 'Djavan', album: 'Djavan', genero: 'mpb' },
    { track_id: '5h2j8k1l4f6g7h8j9k0l1m', nome: 'Aquarela', artista: 'Toquinho', album: 'Aquarela', genero: 'mpb' },
    { track_id: '6k3l9m2n5g7h8j9k0l1m2n', nome: 'Como Nossos Pais', artista: 'Elis Regina', album: 'Falso Brilhante', genero: 'mpb' },
  ]
};

function resolverMockLocal(sessionId, mensagem) {
  const msg = mensagem.toLowerCase();
  let faixas = [];
  let texto = '';
  let genero = 'misto';

  if (msg.includes('pagode') || msg.includes('samba') || msg.includes('churrasco')) {
    faixas = OFFLINE_CATALOGO.pagode;
    texto = 'Selecionei clássicos do pagode com energia lá em cima para animar o seu churrasco!';
    genero = 'pagode';
  } else if (msg.includes('rock') || msg.includes('80') || msg.includes('guitarra')) {
    faixas = OFFLINE_CATALOGO.rock;
    texto = 'Aqui estão hinos do rock clássico com solos marcantes e energia contagiante:';
    genero = 'rock';
  } else if (msg.includes('chill') || msg.includes('lofi') || msg.includes('lo-fi') || msg.includes('relax') || msg.includes('foco') || msg.includes('calm') || msg.includes('estud')) {
    faixas = OFFLINE_CATALOGO.chill;
    texto = 'Encontrei faixas perfeitas com clima relaxante e alta acústica para você desacelerar ou focar:';
    genero = 'chill';
  } else if (msg.includes('mpb') || msg.includes('djavan') || msg.includes('caetano')) {
    faixas = OFFLINE_CATALOGO.mpb;
    texto = 'Obras primas da MPB selecionadas do catálogo com rica harmonia acústica:';
    genero = 'mpb';
  } else if (msg.includes('pop') || msg.includes('danc') || msg.includes('trein')) {
    faixas = OFFLINE_CATALOGO.pop;
    texto = 'Músicas pop com batidas vibrantes e alta dançabilidade separadas do dataset:';
    genero = 'pop';
  } else if (msg.includes('oi') || msg.includes('olá') || msg.includes('ola') || msg.includes('ajuda')) {
    texto = 'Olá! Sou o agente musical do Grupo 8 ResIA. Como posso ajudar seu dia com música? Experimente pedir por gênero (pagode, rock, pop, chill, MPB) ou momento!';
    faixas = [];
  } else {
    faixas = [OFFLINE_CATALOGO.pop[0], OFFLINE_CATALOGO.chill[1], OFFLINE_CATALOGO.mpb[0]];
    texto = `Entendi seu pedido! Busquei no acervo de 114k faixas do Spotify algumas recomendações que combinam com "${mensagem}":`;
  }

  return {
    session_id: sessionId,
    mensagem: texto,
    faixas: faixas,
    diversidade_generos: faixas.length > 0 ? 1 : 0,
    cobertura_sessao: 1.0,
    consulta_efetiva: { genero: genero, consulta: mensagem },
    _offline: true,
  };
}

async function enviarMensagem(sessionId, mensagem) {
  const url = `${API_BASE_URL}/chat`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        mensagem: mensagem,
        excluir_explicit: loadSettings().excludeExplicit,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Erro na resposta do backend: HTTP ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    console.warn('Backend inacessível ou offline. Utilizando resolução resiliente:', err);
    await new Promise((r) => setTimeout(r, 650));
    return resolverMockLocal(sessionId, mensagem);
  }
}

async function buscarJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, { credentials: 'include' });
  if (!response.ok) throw new Error(`Erro na resposta do backend: HTTP ${response.status}`);
  return response.json();
}

async function buscarHistorico(sessionId) {
  return buscarJson(`/chat/historico?session_id=${encodeURIComponent(sessionId)}`);
}

async function buscarPerfil(sessionId) {
  return buscarJson(`/perfil?session_id=${encodeURIComponent(sessionId)}`);
}

async function criarPlaylistResIA(trackIds, nome, descricao = '') {
  if (!Array.isArray(trackIds) || trackIds.length === 0) {
    throw new Error('Selecione ao menos uma faixa para criar a playlist.');
  }
  const response = await fetch(`${API_BASE_URL}/playlist/criar`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ track_ids: trackIds, nome, descricao }),
  });
  if (!response.ok) throw new Error(`Não foi possível criar a playlist: HTTP ${response.status}`);
  const playlist = await response.json();
  if (!saveCreatedPlaylist(playlist)) throw new Error('A API retornou uma playlist incompleta.');
  if (activePanel === 'playlists') renderPlaylistsPanel();
  return playlist;
}

function loadSettings() {
  try {
    const stored = JSON.parse(localStorage.getItem(SETTINGS_STORAGE_KEY) || '{}');
    return {
      excludeExplicit: stored.excludeExplicit !== false,
      theme: stored.theme === 'light' ? 'light' : 'dark',
    };
  } catch (error) {
    return { excludeExplicit: true, theme: 'dark' };
  }
}

function saveSettings(settings) {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.warn('Falha ao salvar preferências:', error);
  }
}

function applyTheme(theme) {
  const nextTheme = theme === 'light' ? 'light' : 'dark';
  document.documentElement.dataset.theme = nextTheme;
  const settings = loadSettings();
  saveSettings({ ...settings, theme: nextTheme });
}

function loadCreatedPlaylists() {
  try {
    const playlists = JSON.parse(localStorage.getItem(PLAYLISTS_STORAGE_KEY) || '[]');
    return Array.isArray(playlists) ? playlists.filter((playlist) => playlist && playlist.id && playlist.nome && playlist.link) : [];
  } catch (error) {
    return [];
  }
}

function saveCreatedPlaylist(playlist) {
  if (!playlist?.id || !playlist?.nome || !playlist?.link) return false;
  const playlists = loadCreatedPlaylists().filter((item) => item.id !== playlist.id);
  playlists.unshift({ id: playlist.id, nome: playlist.nome, link: playlist.link, created_at: playlist.created_at || new Date().toISOString() });
  try {
    localStorage.setItem(PLAYLISTS_STORAGE_KEY, JSON.stringify(playlists));
    return true;
  } catch (error) {
    console.warn('Falha ao salvar playlist ResIA:', error);
    return false;
  }
}

// ==========================================
// 3. Controlador da Interface e Estado
// ==========================================
let currentSessionId = null;
let messages = [];
let isProcessing = false;
let isEditingMessage = false; // Estado de edição (Ticket 16.2)
let activePanel = null;
let lastPanelTrigger = null;
let discoveries = { genres: new Map(), artists: new Map(), turns: [] };
let settings = loadSettings();

// Elementos DOM
const sessionIdDisplay = document.getElementById('session-id-display');
const btnCopySession = document.getElementById('btn-copy-session');
const btnNewChat = document.getElementById('btn-new-chat');
const btnSpotifyAuth = document.getElementById('btn-spotify-auth');
const chatScrollArea = document.getElementById('chat-scroll-area');
const heroEmptyState = document.getElementById('hero-empty-state');
const messagesContainer = document.getElementById('messages-container');
const typingIndicator = document.getElementById('typing-indicator');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const btnMic = document.getElementById('btn-mic');
const toastContainer = document.getElementById('toast-container');
const editMessageBanner = document.getElementById('edit-message-banner');
const btnCancelEdit = document.getElementById('btn-cancel-edit');
const panelBackdrop = document.getElementById('panel-backdrop');
const panelDefinitions = {
  profile: { panel: document.getElementById('profile-panel'), content: document.getElementById('profile-panel-content') },
  history: { panel: document.getElementById('history-panel'), content: document.getElementById('history-panel-content') },
  discoveries: { panel: document.getElementById('discoveries-panel'), content: document.getElementById('discoveries-panel-content') },
  settings: { panel: document.getElementById('settings-panel'), content: document.getElementById('settings-panel-content') },
  about: { panel: document.getElementById('about-panel'), content: document.getElementById('about-panel-content') },
  playlists: { panel: document.getElementById('playlists-panel'), content: document.getElementById('playlists-panel-content') },
};

function init() {
  currentSessionId = getSessionId();
  updateSessionDisplay();

  messages = loadChatHistory(currentSessionId);
  if (messages.length > 0) {
    if (heroEmptyState) heroEmptyState.style.display = 'none';
    messages.forEach((msg) => renderMessageBubble(msg, false));
    scrollToBottom();
  }

  rebuildDiscoveries();
  applyTheme(settings.theme);

  setupEventListeners();
}

function updateSessionDisplay() {
  if (!sessionIdDisplay) return;
  const shortId =
    currentSessionId && currentSessionId.length > 12
      ? `${currentSessionId.substring(0, 6)}...${currentSessionId.substring(currentSessionId.length - 4)}`
      : (currentSessionId || '...');
  sessionIdDisplay.textContent = shortId;
  sessionIdDisplay.parentElement.title = `Session ID completo: ${currentSessionId}`;
}

function showToast(message, duration = 3000) {
  if (!toastContainer) return;
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
window.showToast = showToast;

function setupEventListeners() {
  document.getElementById('btn-profile-panel')?.addEventListener('click', (event) => openPanel('profile', event.currentTarget));
  document.getElementById('btn-history-panel')?.addEventListener('click', (event) => openPanel('history', event.currentTarget));
  document.getElementById('btn-discoveries-panel')?.addEventListener('click', (event) => openPanel('discoveries', event.currentTarget));
  document.getElementById('btn-settings-panel')?.addEventListener('click', (event) => openPanel('settings', event.currentTarget));
  document.getElementById('btn-about-panel')?.addEventListener('click', (event) => openPanel('about', event.currentTarget));
  document.getElementById('btn-playlists-panel')?.addEventListener('click', (event) => openPanel('playlists', event.currentTarget));
  panelBackdrop?.addEventListener('click', closePanel);
  document.querySelectorAll('[data-close-panel]').forEach((button) => button.addEventListener('click', closePanel));

  btnCopySession?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(currentSessionId);
      showToast('Session ID copiado!');
    } catch (e) {
      showToast(`ID da Sessão: ${currentSessionId}`);
    }
  });

  btnNewChat?.addEventListener('click', () => {
    if (isProcessing) return;
    cancelEditMessage();
    currentSessionId = resetSession();
    messages = [];
    messagesContainer.innerHTML = '';
    if (heroEmptyState) heroEmptyState.style.display = 'flex';
    updateSessionDisplay();
    showToast('Nova conversa iniciada!');
    chatInput?.focus();
  });

  btnSpotifyAuth?.addEventListener('click', () => {
    showToast('Autenticação Spotify OAuth pronta para integração (Épico 5).');
  });

  btnMic?.addEventListener('click', () => {
    showToast('Entrada de voz Convora: gravação ativada (modo demo).');
  });

  // Botão de cancelar edição no banner (Ticket 16.2)
  btnCancelEdit?.addEventListener('click', () => {
    cancelEditMessage();
    chatInput?.focus();
  });

  document.querySelectorAll('.prompt-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      const prompt = pill.getAttribute('data-prompt');
      if (prompt && !isProcessing) {
        cancelEditMessage();
        chatInput.value = prompt;
        ajustarAlturaInput();
        btnSend.disabled = false;
        enviarMensagemUsuario(prompt);
      }
    });
  });

  chatInput?.addEventListener('input', () => {
    ajustarAlturaInput();
    const temTexto = chatInput.value.trim().length > 0;
    btnSend.disabled = !temTexto || isProcessing;
  });

  // Atalhos de teclado no input (Ticket 16.4)
  chatInput?.addEventListener('keydown', (e) => {
    // Enter envia mensagem; Shift+Enter insere quebra de linha
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!btnSend.disabled && !isProcessing) {
        const texto = chatInput.value.trim();
        if (texto) {
          // Limpar modo de edição antes de enviar
          if (isEditingMessage) {
            isEditingMessage = false;
            if (editMessageBanner) editMessageBanner.classList.remove('active');
          }
          enviarMensagemUsuario(texto);
        }
      }
    }

    // Escape cancela modo de edição (Ticket 16.4)
    if (e.key === 'Escape' && isEditingMessage) {
      e.preventDefault();
      cancelEditMessage();
    }

    // Seta pra cima com input vazio recupera última mensagem (Ticket 16.4)
    if (e.key === 'ArrowUp' && chatInput.value.trim() === '' && !isProcessing) {
      e.preventDefault();
      startEditLastMessage();
    }
  });

  chatForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!btnSend.disabled && !isProcessing) {
      const texto = chatInput.value.trim();
      if (texto) {
        if (isEditingMessage) {
          isEditingMessage = false;
          if (editMessageBanner) editMessageBanner.classList.remove('active');
        }
        enviarMensagemUsuario(texto);
      }
    }
  });

  // Atalho global "/" para focar no input (Ticket 16.4)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && activePanel) {
      closePanel();
      return;
    }
    // Ignorar se já estiver em um campo de texto ou textarea
    const tag = document.activeElement?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'textarea' || document.activeElement?.isContentEditable) {
      return;
    }

    if (e.key === '/') {
      e.preventDefault();
      chatInput?.focus();
    }
  });
}

function openPanel(name, trigger) {
  const definition = panelDefinitions[name];
  if (!definition) return;

  if (activePanel) closePanel();
  activePanel = name;
  lastPanelTrigger = trigger || null;
  definition.panel.hidden = false;
  definition.panel.classList.add('is-open');
  definition.panel.setAttribute('aria-hidden', 'false');
  panelBackdrop.hidden = false;
  panelBackdrop.classList.add('is-visible');

  if (name === 'profile') renderProfilePanel();
  if (name === 'history') renderHistoryPanel();
  if (name === 'discoveries') renderDiscoveriesPanel();
  if (name === 'settings') renderSettingsPanel();
  if (name === 'about') renderAboutPanel();
  if (name === 'playlists') renderPlaylistsPanel();
  definition.panel.querySelector('[data-close-panel]')?.focus();
}

function closePanel() {
  if (!activePanel) return;
  const definition = panelDefinitions[activePanel];
  definition.panel.classList.remove('is-open');
  definition.panel.setAttribute('aria-hidden', 'true');
  definition.panel.hidden = true;
  panelBackdrop.classList.remove('is-visible');
  panelBackdrop.hidden = true;
  const trigger = lastPanelTrigger;
  activePanel = null;
  lastPanelTrigger = null;
  trigger?.focus();
}

function rebuildDiscoveries() {
  discoveries = { genres: new Map(), artists: new Map(), turns: [] };
  messages.filter((message) => message.role === 'agent' && Array.isArray(message.faixas)).forEach((message) => recordDiscoveries(message));
}

function recordDiscoveries(response) {
  const tracks = Array.isArray(response.faixas) ? response.faixas : [];
  const genres = new Set();
  const artists = new Set();
  tracks.forEach((track) => {
    if (track.genero) genres.add(track.genero);
    if (track.artista) artists.add(track.artista);
  });
  genres.forEach((genre) => discoveries.genres.set(genre, (discoveries.genres.get(genre) || 0) + 1));
  artists.forEach((artist) => discoveries.artists.set(artist, (discoveries.artists.get(artist) || 0) + 1));
  if (tracks.length) discoveries.turns.push({
    timestamp: response.timestamp || new Date().toISOString(),
    genres: [...genres],
    artists: [...artists],
    diversidade_generos: response.diversidade_generos,
    cobertura_sessao: response.cobertura_sessao,
  });
}

function renderPanelMessage(content, message, type = '') {
  content.innerHTML = `<div class="panel-state ${type}">${escapeHtml(message)}</div>`;
}

function renderProfilePanel() {
  const content = panelDefinitions.profile.content;
  renderPanelMessage(content, 'Carregando seu perfil...', 'panel-state-loading');
  buscarPerfil(currentSessionId).then((profile) => {
    const vector = profile?.vetor_features_normalizado || profile?.perfil_usuario || profile?.vetor || null;
    if (!vector) {
      renderPanelMessage(content, 'Ainda não há histórico suficiente para montar um perfil personalizado.', 'panel-state-empty');
      return;
    }
    const entries = Object.entries(vector).filter(([, value]) => typeof value === 'number' && Number.isFinite(value));
    content.innerHTML = `
      <section class="profile-summary">
        <span class="panel-kicker">Seu gosto musical</span>
        <p>Características normalizadas a partir do seu histórico casado.</p>
      </section>
      <section class="feature-list" aria-label="Características do perfil">
        ${entries.map(([label, value]) => `
          <div class="feature-row">
            <div><span>${escapeHtml(label.replaceAll('_', ' '))}</span><strong>${value.toFixed(2)}</strong></div>
            <div class="feature-meter"><span style="width: ${Math.max(0, Math.min(100, value * 100))}%"></span></div>
          </div>
        `).join('')}
      </section>
      ${renderMetricHistory()}
    `;
  }).catch((error) => {
    console.warn('Falha ao carregar perfil:', error);
    renderPanelMessage(content, 'Não foi possível carregar o perfil agora.', 'panel-state-error');
  });
}

function renderMetricHistory() {
  const metricTurns = discoveries.turns.filter((turn) => turn.diversidade_generos !== undefined);
  if (!metricTurns.length) return '';
  return `<section class="metric-history"><h3>Histórico da sessão</h3>${metricTurns.map((turn) => `
    <div class="metric-row"><time>${escapeHtml(formatarHora(turn.timestamp))}</time><span>${turn.diversidade_generos} gêneros</span><strong>${Math.round(turn.cobertura_sessao * 100)}% novas</strong></div>
  `).join('')}</section>`;
}

function renderHistoryPanel() {
  const content = panelDefinitions.history.content;
  renderPanelMessage(content, 'Carregando histórico...', 'panel-state-loading');
  buscarHistorico(currentSessionId).then((data) => {
    const history = Array.isArray(data) ? data : (data?.historico || data?.mensagens || []);
    const panelMessages = history.length ? history : messages;
    if (!panelMessages.length) {
      renderPanelMessage(content, 'Nenhuma conversa nesta sessão.', 'panel-state-empty');
      return;
    }
    content.innerHTML = panelMessages.map((message) => `
    <article class="history-item ${message.role}">
      <span class="history-role">${message.role === 'user' ? 'Você' : 'ResIA'}</span>
      <p>${escapeHtml(message.conteudo)}</p>
      <time>${escapeHtml(formatarHora(message.timestamp))}</time>
    </article>
    `).join('');
  }).catch((error) => {
    console.warn('Falha ao carregar histórico:', error);
    if (messages.length) {
      content.innerHTML = `<div class="panel-state panel-state-info">API indisponível. Exibindo o histórico local desta sessão.</div>${messages.map((message) => `
        <article class="history-item ${message.role}"><span class="history-role">${message.role === 'user' ? 'Você' : 'ResIA'}</span><p>${escapeHtml(message.conteudo)}</p><time>${escapeHtml(formatarHora(message.timestamp))}</time></article>
      `).join('')}`;
    } else {
      renderPanelMessage(content, 'Não foi possível carregar o histórico.', 'panel-state-error');
    }
  });
}

function renderDiscoveriesPanel() {
  const content = panelDefinitions.discoveries.content;
  if (!discoveries.turns.length) {
    renderPanelMessage(content, 'As novas descobertas da sua sessão aparecerão aqui.', 'panel-state-empty');
    return;
  }
  const renderList = (title, values) => `<section class="discovery-group"><h3>${title}</h3><ul>${[...values.entries()].map(([label, count]) => `<li><span>${escapeHtml(label)}</span><strong>${count}</strong></li>`).join('')}</ul></section>`;
  content.innerHTML = `${renderList('Gêneros', discoveries.genres)}${renderList('Artistas', discoveries.artists)}`;
}

function renderSettingsPanel() {
  const content = panelDefinitions.settings.content;
  settings = loadSettings();
  content.innerHTML = `
    <section class="settings-group">
      <h3>Recomendações</h3>
      <label class="setting-row" for="exclude-explicit-toggle">
        <span><strong>Excluir faixas explícitas</strong><small>Aplicar por padrão às próximas recomendações.</small></span>
        <input id="exclude-explicit-toggle" class="setting-toggle" type="checkbox" ${settings.excludeExplicit ? 'checked' : ''}>
      </label>
    </section>
    <section class="settings-group">
      <h3>Aparência</h3>
      <div class="theme-options" role="group" aria-label="Tema">
        <button class="theme-option ${settings.theme === 'dark' ? 'is-selected' : ''}" data-theme-choice="dark" type="button">Escuro</button>
        <button class="theme-option ${settings.theme === 'light' ? 'is-selected' : ''}" data-theme-choice="light" type="button">Claro</button>
      </div>
    </section>
  `;
  content.querySelector('#exclude-explicit-toggle')?.addEventListener('change', (event) => {
    settings = { ...loadSettings(), excludeExplicit: event.target.checked };
    saveSettings(settings);
  });
  content.querySelectorAll('[data-theme-choice]').forEach((button) => button.addEventListener('click', () => {
    settings = { ...loadSettings(), theme: button.dataset.themeChoice };
    applyTheme(settings.theme);
    renderSettingsPanel();
  }));
}

function renderAboutPanel() {
  panelDefinitions.about.content.innerHTML = `
    <section class="info-section">
      <h3>Como ranqueamos</h3>
      <p>As recomendações combinam os sinais da sua consulta com características musicais e diversidade da sessão. Popularidade pode ser um sinal, mas não decide sozinha o resultado.</p>
    </section>
    <section class="info-section">
      <h3>Seus dados</h3>
      <p>O ResIA usa sua mensagem e o contexto da sessão para responder. O histórico e as preferências desta interface ficam associados à sessão; preferências e playlists ResIA são guardadas localmente neste navegador.</p>
    </section>
    <section class="info-section">
      <h3>Spotify</h3>
      <p>Quando você conecta sua conta, o acesso segue a autorização exibida pelo Spotify. O ResIA não grava tokens no navegador e só registra uma playlist localmente depois de confirmar sua criação.</p>
    </section>
  `;
}

function renderPlaylistsPanel() {
  const content = panelDefinitions.playlists.content;
  const playlists = loadCreatedPlaylists();
  if (!playlists.length) {
    renderPanelMessage(content, 'As playlists criadas pelo ResIA aparecerão aqui.', 'panel-state-empty');
    return;
  }
  content.innerHTML = `${playlists.map((playlist) => `
    <article class="playlist-item">
      <div><span class="panel-kicker">Playlist ResIA</span><h3>${escapeHtml(playlist.nome)}</h3><small>ID: ${escapeHtml(playlist.id)}</small></div>
      <a href="${escapeHtml(playlist.link)}" target="_blank" rel="noopener noreferrer" class="playlist-link" title="Abrir playlist no Spotify">Abrir</a>
    </article>
  `).join('')}`;
}

function ajustarAlturaInput() {
  if (!chatInput) return;
  chatInput.style.height = 'auto';
  chatInput.style.height = `${Math.min(chatInput.scrollHeight, 120)}px`;
}

function scrollToBottom() {
  if (!chatScrollArea) return;
  chatScrollArea.scrollTop = chatScrollArea.scrollHeight;
}

function formatarHora(timestamp) {
  const data = timestamp ? new Date(timestamp) : new Date();
  return data.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Renderiza markdown básico com sanitização XSS integrada (Ticket 16.1).
 * Suporta: negrito, itálico, código inline, links (http/https apenas),
 * listas não-ordenadas, listas ordenadas e parágrafos.
 * @param {string} text Texto bruto com possível markdown
 * @returns {string} HTML seguro para inserção via innerHTML
 */
function renderMarkdownSafe(text) {
  if (!text) return '';

  // 1. Sanitização XSS: escape de caracteres perigosos antes de qualquer transformação
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  // 2. Código inline: `codigo`
  safe = safe.replace(/`([^`]+)`/g, '<code>$1</code>');

  // 3. Negrito: **texto** ou __texto__
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // 4. Itálico: *texto* ou _texto_ (sem conflito com negrito pois ** já foi processado)
  safe = safe.replace(/\*(.+?)\*/g, '<em>$1</em>');
  safe = safe.replace(/(?<!\w)_(.+?)_(?!\w)/g, '<em>$1</em>');

  // 5. Links markdown: [rótulo](url) — apenas http:// e https://
  safe = safe.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // 6. URLs soltas (não já envolvidas em <a>): transformar em links clicáveis
  safe = safe.replace(/(?<!href=")(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

  // 7. Listas: processamento por linhas
  const lines = safe.split('\n');
  let result = [];
  let inUl = false;
  let inOl = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const ulMatch = line.match(/^\s*[-*]\s+(.+)/);
    const olMatch = line.match(/^\s*\d+\.\s+(.+)/);

    if (ulMatch) {
      if (inOl) { result.push('</ol>'); inOl = false; }
      if (!inUl) { result.push('<ul>'); inUl = true; }
      result.push(`<li>${ulMatch[1]}</li>`);
    } else if (olMatch) {
      if (inUl) { result.push('</ul>'); inUl = false; }
      if (!inOl) { result.push('<ol>'); inOl = true; }
      result.push(`<li>${olMatch[1]}</li>`);
    } else {
      if (inUl) { result.push('</ul>'); inUl = false; }
      if (inOl) { result.push('</ol>'); inOl = false; }
      // Linhas vazias como separador de parágrafos
      if (line.trim() === '') {
        result.push('<br>');
      } else {
        result.push(`<p>${line}</p>`);
      }
    }
  }
  if (inUl) result.push('</ul>');
  if (inOl) result.push('</ol>');

  return result.join('');
}

// ==========================================
// 5. Edição de Mensagem (Ticket 16.2)
// ==========================================

/**
 * Ativa o modo de edição: popula o input com a última mensagem do usuário
 * e exibe o banner informativo.
 */
function startEditLastMessage() {
  if (isProcessing) return;

  // Encontrar a última mensagem do usuário
  let lastUserMsg = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === 'user') {
      lastUserMsg = messages[i];
      break;
    }
  }

  if (!lastUserMsg) return;

  isEditingMessage = true;
  chatInput.value = lastUserMsg.conteudo;
  ajustarAlturaInput();
  btnSend.disabled = false;

  // Exibir banner de edição
  if (editMessageBanner) {
    editMessageBanner.classList.add('active');
  }

  // Focar e posicionar cursor no final
  chatInput.focus();
  chatInput.setSelectionRange(chatInput.value.length, chatInput.value.length);
}

/**
 * Cancela o modo de edição e limpa o input.
 */
function cancelEditMessage() {
  isEditingMessage = false;
  chatInput.value = '';
  ajustarAlturaInput();
  btnSend.disabled = true;

  if (editMessageBanner) {
    editMessageBanner.classList.remove('active');
  }
}

function renderMessageBubble(msg, animar = true) {
  if (!messagesContainer) return;

  const row = document.createElement('div');
  row.className = `message-row ${msg.role}`;
  if (!animar) row.style.animation = 'none';

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  if (msg.role === 'agent') {
    avatar.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9v-2h2v2zm0-4H9V7h2v5zm4 4h-2v-2h2v2zm0-4h-2V7h2v5z"/>
      </svg>
    `;
    avatar.title = 'Agente ResIA';
  } else {
    avatar.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    `;
    avatar.title = 'Você';
  }

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  const textElem = document.createElement('div');
  textElem.className = 'message-text';

  // Ticket 16.1: Renderizar markdown sanitizado nas mensagens do agente
  if (msg.role === 'agent') {
    textElem.innerHTML = renderMarkdownSafe(msg.conteudo);
  } else {
    textElem.textContent = msg.conteudo;
  }
  bubble.appendChild(textElem);

  // CRITÉRIO DE ACEITE TICKET 4.2:
  // "Cards montados a partir do campo faixas da resposta, não fazendo parsing do texto livre."
  if (msg.faixas && Array.isArray(msg.faixas) && msg.faixas.length > 0) {
    const tracksSection =
      window.ResIATrackCard && typeof window.ResIATrackCard.renderTrackCards === 'function'
        ? window.ResIATrackCard.renderTrackCards(msg.faixas)
        : null;

    if (tracksSection) {
      bubble.appendChild(tracksSection);
    }
  }

  const timeElem = document.createElement('span');
  timeElem.className = 'message-timestamp';
  timeElem.textContent = formatarHora(msg.timestamp);
  bubble.appendChild(timeElem);

  // Ticket 16.2: Botão de edição nas mensagens do usuário
  if (msg.role === 'user') {
    const editBtn = document.createElement('button');
    editBtn.className = 'btn-edit-message';
    editBtn.title = 'Editar e reenviar';
    editBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
      </svg>
    `;
    editBtn.addEventListener('click', () => {
      startEditLastMessage();
    });
    bubble.appendChild(editBtn);
  }

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
}

async function enviarMensagemUsuario(texto) {
  if (isProcessing) return;
  isProcessing = true;

  chatInput.value = '';
  ajustarAlturaInput();
  btnSend.disabled = true;

  if (heroEmptyState) {
    heroEmptyState.style.display = 'none';
  }

  const userMsg = {
    id: `user-${Date.now()}`,
    role: 'user',
    conteudo: texto,
    timestamp: new Date().toISOString(),
  };
  messages.push(userMsg);
  renderMessageBubble(userMsg, true);
  scrollToBottom();

  if (typingIndicator) {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
  }

  // Ticket 16.6: Skeleton loading de cards de faixa
  let skeletonBubble = null;
  if (window.ResIATrackCard && typeof window.ResIATrackCard.renderSkeletonTrackCards === 'function') {
    skeletonBubble = document.createElement('div');
    skeletonBubble.className = 'message-row agent';
    skeletonBubble.id = 'skeleton-loading-row';
    const skeletonAvatar = document.createElement('div');
    skeletonAvatar.className = 'message-avatar';
    skeletonAvatar.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9v-2h2v2zm0-4H9V7h2v5zm4 4h-2v-2h2v2zm0-4h-2V7h2v5z"/>
      </svg>
    `;
    const skeletonContent = document.createElement('div');
    skeletonContent.className = 'message-bubble';
    skeletonContent.appendChild(window.ResIATrackCard.renderSkeletonTrackCards(3));
    skeletonBubble.appendChild(skeletonAvatar);
    skeletonBubble.appendChild(skeletonContent);
    messagesContainer.appendChild(skeletonBubble);
    scrollToBottom();
  }

  try {
    const resposta = await enviarMensagem(currentSessionId, texto);

    const agentMsg = {
      id: `agent-${Date.now()}`,
      role: 'agent',
      conteudo: resposta.mensagem || 'Recomendações prontas!',
      faixas: resposta.faixas || [],
      diversidade_generos: resposta.diversidade_generos,
      cobertura_sessao: resposta.cobertura_sessao,
      timestamp: new Date().toISOString(),
    };
    messages.push(agentMsg);
    recordDiscoveries({ ...resposta, timestamp: agentMsg.timestamp });
    saveChatHistory(currentSessionId, messages);

    // Remover skeleton antes de renderizar resposta real
    if (skeletonBubble && skeletonBubble.parentNode) {
      skeletonBubble.remove();
    }
    if (typingIndicator) typingIndicator.style.display = 'none';
    renderMessageBubble(agentMsg, true);
    scrollToBottom();
  } catch (error) {
    console.error('Erro ao processar turno:', error);
    // Remover skeleton em caso de erro
    if (skeletonBubble && skeletonBubble.parentNode) {
      skeletonBubble.remove();
    }
    if (typingIndicator) typingIndicator.style.display = 'none';

    const errorMsg = {
      id: `error-${Date.now()}`,
      role: 'agent',
      conteudo: 'Desculpe, ocorreu uma instabilidade temporária. Por favor tente novamente.',
      timestamp: new Date().toISOString(),
    };
    messages.push(errorMsg);
    renderMessageBubble(errorMsg, true);
    scrollToBottom();
  } finally {
    isProcessing = false;
    btnSend.disabled = chatInput.value.trim().length === 0;
    chatInput.focus();
  }
}

// Expõe no objeto global window para testes ou depuração
window.ResIA = {
  getSessionId,
  saveSessionId,
  resetSession,
  enviarMensagem,
    buscarHistorico,
    buscarPerfil,
    criarPlaylistResIA,
    loadSettings,
    saveSettings,
    applyTheme,
    loadCreatedPlaylists,
    saveCreatedPlaylist,
  enviarMensagemUsuario,
  renderMarkdownSafe,
  startEditLastMessage,
  cancelEditMessage,
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
