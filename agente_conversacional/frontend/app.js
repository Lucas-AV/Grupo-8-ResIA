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

/**
 * Erro do backend padronizado pelo Ticket 8.3 (HTTP 5xx com corpo {"erro": "..."}).
 * Sinalizado com uma classe própria pra não cair no fallback silencioso de mock:
 * o Ticket 4.8 (KAN-75) exige feedback visível ao usuário nesse caso, não um
 * console.warn escondido atrás de uma resposta falsa de sucesso.
 */
class ErroBackend extends Error {
  constructor(mensagem, status) {
    super(mensagem);
    this.name = 'ErroBackend';
    this.status = status;
  }
}

async function enviarMensagem(sessionId, mensagem) {
  const url = `${API_BASE_URL}/chat`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        mensagem: mensagem,
      }),
      signal: controller.signal,
    });
  } catch (err) {
    // Falha de rede/timeout (backend fora do ar): mantém a resiliência existente
    // e responde com o catálogo offline em vez de travar o chat.
    clearTimeout(timeoutId);
    console.warn('Backend inacessível ou offline. Utilizando resolução resiliente:', err);
    await new Promise((r) => setTimeout(r, 650));
    return resolverMockLocal(sessionId, mensagem);
  }
  clearTimeout(timeoutId);

  // Ticket 4.9 (KAN-76): limite de mensagens atingido (rate limiting do
  // ticket 8.4, quando ligado no backend). Fica fora do try/catch acima de
  // propósito — não deve cair no fallback offline, que mascararia do
  // usuário que ele precisa esperar antes de tentar de novo.
  if (response.status === 429) {
    const rateLimitError = new Error('Limite de mensagens atingido (HTTP 429).');
    rateLimitError.isRateLimit = true;
    throw rateLimitError;
  }

  if (response.status >= 500) {
    let corpo = null;
    try {
      corpo = await response.json();
    } catch (_) {
      // resposta 500 sem JSON válido — segue com mensagem genérica abaixo
    }
    throw new ErroBackend((corpo && corpo.erro) || 'erro interno do servidor', response.status);
  }

  if (!response.ok) {
    throw new Error(`Erro na resposta do backend: HTTP ${response.status}`);
  }

  return await response.json();
}

// ==========================================
// 3. Controlador da Interface e Estado
// ==========================================
let currentSessionId = null;
let messages = [];
let isProcessing = false;

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

function init() {
  currentSessionId = getSessionId();
  updateSessionDisplay();

  // Ticket 4.12 (KAN-79): sessão restaurada já tem histórico -> não mostra onboarding.
  messages = loadChatHistory(currentSessionId);
  if (messages.length > 0) {
    if (heroEmptyState) heroEmptyState.style.display = 'none';
    messages.forEach((msg) => renderMessageBubble(msg, false));
    scrollToBottom();
  }

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

/**
 * Banner/toast genérico de erro (Ticket 4.8 / KAN-75).
 * Reaproveita o container de toasts existente em vez de criar um novo componente.
 * Diferente de showToast(), não some sozinho: fica visível até o usuário fechar
 * ou tentar de novo, e nunca bloqueia o restante da tela/chat.
 */
function showErrorBanner(message, onRetry) {
  if (!toastContainer) {
    window.alert(message);
    return;
  }

  const toast = document.createElement('div');
  toast.className = 'toast-notification toast-error';
  toast.setAttribute('role', 'alert');

  const textElem = document.createElement('span');
  textElem.className = 'toast-error-text';
  textElem.textContent = message;
  toast.appendChild(textElem);

  if (typeof onRetry === 'function') {
    const retryBtn = document.createElement('button');
    retryBtn.type = 'button';
    retryBtn.className = 'toast-retry-btn';
    retryBtn.textContent = 'Tentar novamente';
    retryBtn.addEventListener('click', () => {
      toast.remove();
      onRetry();
    });
    toast.appendChild(retryBtn);
  }

  const closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'toast-close-btn';
  closeBtn.setAttribute('aria-label', 'Fechar aviso');
  closeBtn.textContent = '×';
  closeBtn.addEventListener('click', () => toast.remove());
  toast.appendChild(closeBtn);

  toastContainer.appendChild(toast);
}
window.showErrorBanner = showErrorBanner;

function setupEventListeners() {
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
    currentSessionId = resetSession();
    messages = [];
    messagesContainer.innerHTML = '';
    // Ticket 4.12 (KAN-79): nova conversa volta a ficar sem histórico -> onboarding reaparece.
    if (heroEmptyState) heroEmptyState.style.display = 'flex';
    updateSessionDisplay();
    showToast('Nova conversa iniciada!');
    chatInput?.focus();
  });

  btnSpotifyAuth?.addEventListener('click', () => {
    // Ticket 4.7 (KAN-74): antes de qualquer redirect real pro Spotify, o
    // usuário passa pela página de consentimento própria do backend
    // (GET /auth/login → spotify_auth/consent.py), que lista os scopes
    // lidos e a política de dados (ticket 5.10) e só depois linka pro
    // redirect de fato (GET /auth/login/start). Abrimos essa página em vez
    // de replicar o texto aqui pra não divergir do que o backend descreve.
    window.location.href = `${API_BASE_URL}/auth/login?session_id=${encodeURIComponent(currentSessionId)}`;
  });

  btnMic?.addEventListener('click', () => {
    showToast('Entrada de voz Convora: gravação ativada (modo demo).');
  });

  document.querySelectorAll('.prompt-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      const prompt = pill.getAttribute('data-prompt');
      if (prompt && !isProcessing) {
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

  chatInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!btnSend.disabled && !isProcessing) {
        const texto = chatInput.value.trim();
        if (texto) {
          enviarMensagemUsuario(texto);
        }
      }
    }
  });

  chatForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!btnSend.disabled && !isProcessing) {
      const texto = chatInput.value.trim();
      if (texto) {
        enviarMensagemUsuario(texto);
      }
    }
  });
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
  // Ticket 4.9 (KAN-76): marca visualmente a mensagem de limite de taxa
  // (HTTP 429) como distinta de uma resposta normal do agente.
  if (msg.isRateLimitError) {
    bubble.classList.add('message-bubble--rate-limit');
  }

  const textElem = document.createElement('div');
  textElem.className = 'message-text';
  textElem.textContent = msg.conteudo;
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

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
}

async function enviarMensagemUsuario(texto, { isRetry = false } = {}) {
  if (isProcessing) return;
  isProcessing = true;

  if (!isRetry) {
    chatInput.value = '';
    ajustarAlturaInput();
  }
  btnSend.disabled = true;

  // Ticket 4.12 (KAN-79): sugestões somem assim que o usuário envia a primeira
  // mensagem — feito aqui, antes da chamada à API, para sumir de imediato.
  if (heroEmptyState) {
    heroEmptyState.style.display = 'none';
  }

  if (!isRetry) {
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      conteudo: texto,
      timestamp: new Date().toISOString(),
    };
    messages.push(userMsg);
    renderMessageBubble(userMsg, true);
    scrollToBottom();
  }

  if (typingIndicator) {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
  }

  try {
    const resposta = await enviarMensagem(currentSessionId, texto);

    const agentMsg = {
      id: `agent-${Date.now()}`,
      role: 'agent',
      conteudo: resposta.mensagem || 'Recomendações prontas!',
      faixas: resposta.faixas || [],
      timestamp: new Date().toISOString(),
    };
    messages.push(agentMsg);
    saveChatHistory(currentSessionId, messages);

    if (typingIndicator) typingIndicator.style.display = 'none';
    renderMessageBubble(agentMsg, true);
    scrollToBottom();
  } catch (error) {
    console.error('Erro ao processar turno:', error);
    if (typingIndicator) typingIndicator.style.display = 'none';

    if (error && error.isRateLimit) {
      // Ticket 4.9 (KAN-76): HTTP 429 recebe mensagem própria, clara sobre o
      // limite de mensagens, em vez do erro genérico/banner do ticket 4.8 (KAN-75).
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: 'agent',
        conteudo: 'Você atingiu o limite de mensagens. Aguarde um instante e tente novamente.',
        isRateLimitError: true,
        timestamp: new Date().toISOString(),
      };
      messages.push(errorMsg);
      renderMessageBubble(errorMsg, true);
      scrollToBottom();
    } else if (error instanceof ErroBackend) {
      // Ticket 4.8 (KAN-75): erro 500 padronizado do backend (ticket 8.3) vira
      // banner/toast genérico e recuperável — não trava o chat, não exige reload.
      showErrorBanner('Ocorreu um erro no servidor. Tente novamente em instantes.', () => {
        enviarMensagemUsuario(texto, { isRetry: true });
      });
    } else {
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: 'agent',
        conteudo: 'Desculpe, ocorreu uma instabilidade temporária. Por favor tente novamente.',
        timestamp: new Date().toISOString(),
      };
      messages.push(errorMsg);
      renderMessageBubble(errorMsg, true);
      scrollToBottom();
    }
  } finally {
    // Critério de aceite (KAN-76): o input do chat continua disponível para
    // uma nova tentativa, mesmo após um 429 — nada aqui desabilita o campo.
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
  enviarMensagemUsuario,
  ErroBackend,
  showErrorBanner,
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
