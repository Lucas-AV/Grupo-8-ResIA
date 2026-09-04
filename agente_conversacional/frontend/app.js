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

async function resetSession() {
  const newSessionId = (await criarSessaoRemota()) || generateUUID();
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

function clearChatHistory(sessionId) {
  if (!sessionId) return;
  try {
    localStorage.removeItem(HISTORY_STORAGE_PREFIX + sessionId);
  } catch (e) {
    console.warn('Falha ao limpar histórico do localStorage:', e);
  }
}

// ==========================================
// 2. Módulo de API e Catálogo Demo
// ==========================================
const API_BASE_URL =
  window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
    ? ''
    : 'http://127.0.0.1:8000';

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

async function enviarMensagem(sessionId, mensagem, extras = {}) {
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
      // Ticket 12.4 (KAN-107): `extras` carrega faixas_ja_mostradas quando o
      // pedido vem do botão "Gerar outra recomendação" — o backend hoje
      // ignora chaves que ChatRequest não declara (comportamento padrão do
      // pydantic), então isso é inofensivo enquanto o schema não abraça o
      // campo, e já fica pronto pro dia em que abraçar.
      body: JSON.stringify({
        session_id: sessionId,
        mensagem: mensagem,
        ...extras,
      }),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    console.warn('Backend inacessível ou offline. Utilizando resolução resiliente:', err);
    await new Promise((r) => setTimeout(r, 650));
    // Não apresenta um catálogo local como se fosse uma recomendação
    // confirmada. A interface trata esta falha com uma mensagem clara.
    throw err;
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

/**
 * Cria uma sessão no backend (POST /session) e devolve o `session_id` gerado por ele.
 * O backend nunca aceita um `session_id` inventado pelo cliente (SessionStore só reconhece
 * ids que ele mesmo gerou via uuid4) — sem essa chamada, todo POST /chat cai em 404
 * `sessao_invalida`, mesmo em uma conversa nova. Retorna `null` se o backend estiver
 * inacessível (rede/timeout); os chamadores decidem o fallback (id local, offline).
 */
async function criarSessaoRemota() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(`${API_BASE_URL}/session`, {
      method: 'POST',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (!response.ok) return null;
    const data = await response.json();
    return data.session_id || null;
  } catch (e) {
    console.warn('Não foi possível criar sessão no backend, mantendo id local:', e);
    return null;
  }
}

/**
 * Consulta o histórico salvo no backend para a sessão atual (Ticket 4.6, GET /chat/historico).
 * Retorna `null` quando o backend está inacessível (falha de rede/timeout) — nesse caso o
 * chamador deve recorrer ao cache local, preservando o comportamento resiliente já existente
 * em enviarMensagem(). Retorna `{ valida: false }` quando a sessão não existe mais no backend
 * (HTTP 404), sem lançar erro visível ao usuário.
 */
async function buscarHistoricoRemoto(sessionId) {
  const url = `${API_BASE_URL}/chat/historico?session_id=${encodeURIComponent(sessionId)}`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(url, { method: 'GET', signal: controller.signal });

    clearTimeout(timeoutId);

    if (response.status === 404) {
      // Sessão inválida/expirada: cai pro estado de conversa nova, sem erro visível ao usuário.
      return { valida: false, mensagens: [] };
    }

    if (!response.ok) {
      throw new Error(`Erro ao consultar histórico: HTTP ${response.status}`);
    }

    const data = await response.json();
    return { valida: true, mensagens: mapearHistoricoRemoto(data.historico) };
  } catch (err) {
    console.warn('Histórico remoto indisponível, utilizando cache local como fallback:', err);
    return null;
  }
}

/**
 * Converte o formato de histórico devolvido pelo backend (roles 'usuario'/'agente'/'sistema')
 * para o formato de mensagem usado pela interface de chat (roles 'user'/'agent').
 * Observação: o histórico remoto devolve apenas os IDs das faixas citadas (faixas_citadas),
 * sem os metadados completos (nome/artista/álbum) — por isso os cards de faixa não são
 * reconstruídos para mensagens restauradas do backend, só o texto e a ordem da conversa.
 */
function mapearHistoricoRemoto(historico) {
  const ROLE_MAP = { usuario: 'user', agente: 'agent', sistema: 'agent' };
  if (!Array.isArray(historico)) return [];

  return historico.map((item, indice) => ({
    id: `historico-${indice}-${item.timestamp || indice}`,
    role: ROLE_MAP[item.role] || 'agent',
    conteudo: item.conteudo,
    faixas: [],
    timestamp: item.timestamp,
  }));
}

/**
 * Ticket 12.2 (KAN-105): consulta GET /auth/status pra saber se a sessão
 * atual está autenticada com o Spotify (ticket 12.1, GET /auth/status).
 * Falha de rede/timeout resolve pra `false` (fail-closed) — não mostra ação
 * que exige login sem ter certeza de que ele existe.
 */
async function verificarStatusSpotify(sessionId) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(`${API_BASE_URL}/auth/status?session_id=${encodeURIComponent(sessionId)}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (!response.ok) return false;
    const data = await response.json();
    return Boolean(data.autenticado);
  } catch (err) {
    console.warn('Não foi possível verificar o status de autenticação com o Spotify:', err);
    return false;
  }
}

/**
 * Ticket 20.8 (KAN-167): busca o `display_name` do usuário Spotify logado
 * (`GET /explorer/me`, ticket 13.10) pra mostrar no header. Só é chamada ao
 * (re)autenticar — nunca a cada render do botão. Falha de rede/parse ou
 * `display_name` vazio resolve pra `null`, e quem chama cai no rótulo
 * genérico ("Spotify conectado") em vez de mostrar um botão vazio.
 */
async function buscarNomeUsuarioSpotify(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/explorer/me?session_id=${encodeURIComponent(sessionId)}`);
    if (!response.ok) return null;
    const data = await response.json();
    return data && data.display_name ? data.display_name : null;
  } catch (err) {
    console.warn('Não foi possível obter o nome do usuário Spotify:', err);
    return null;
  }
}

/**
 * Ticket 4.5 (KAN-40): chama POST /auth/logout (ticket 5.8,
 * spotify_auth/routes.py) pra descartar os tokens Spotify da sessão atual.
 * Não recebe `session_id` no corpo — a rota espera query param, como
 * /auth/status logo acima.
 */
async function logoutSpotify(sessionId) {
  const response = await fetch(`${API_BASE_URL}/auth/logout?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Erro ao desconectar do Spotify: HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Lê o parâmetro `?spotify_login=` deixado pelo redirect de
 * spotify_auth/routes.py (GET /auth/callback) depois do fluxo OAuth (ticket
 * 4.7 / KAN-74), mostra um toast com o resultado e limpa a URL — sem isso o
 * parâmetro ficaria preso na barra de endereço após um reload.
 */
function tratarRetornoLoginSpotify() {
  const params = new URLSearchParams(window.location.search);
  const resultado = params.get('spotify_login');
  if (!resultado) return;

  const MENSAGENS_POR_RESULTADO = {
    success: 'Conectado ao Spotify com sucesso!',
    cancelled: 'Login com o Spotify cancelado.',
    failed: 'Não foi possível conectar ao Spotify. Tente novamente.',
    state_mismatch: 'Falha de segurança ao conectar ao Spotify. Tente novamente.',
  };
  const mensagem = MENSAGENS_POR_RESULTADO[resultado];
  if (mensagem) showToast(mensagem);

  params.delete('spotify_login');
  const query = params.toString();
  const novaUrl = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`;
  window.history.replaceState({}, '', novaUrl);
}

/**
 * Ticket 12.1 (KAN-104): chama POST /playlist/criar com as faixas da
 * sessão atual. Propaga erro (mensagem do backend, quando houver) pro
 * chamador tratar visivelmente — nunca falha silenciosa em console.log.
 */
async function criarPlaylistSpotify(trackIds) {
  const response = await fetch(`${API_BASE_URL}/playlist/criar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSessionId, faixas: trackIds }),
  });

  if (!response.ok) {
    let corpo = null;
    try {
      corpo = await response.json();
    } catch (_) {
      // resposta sem JSON válido — segue com a mensagem genérica abaixo
    }
    const mensagem = (corpo && corpo.detail && corpo.detail.mensagem) || 'Não foi possível salvar a playlist no Spotify.';
    throw new Error(mensagem);
  }

  return await response.json();
}

/**
 * Handler do clique em "Salvar no Spotify" (ticket 12.2): desabilita o
 * botão durante a chamada, dá feedback visível de sucesso/erro (nunca só
 * console.log) reaproveitando showToast/showErrorBanner do ticket 4.8.
 */
async function handleSalvarSpotify(button, trackIds) {
  if (!trackIds || trackIds.length === 0 || button.disabled) return;

  button.disabled = true;
  const textoOriginal = button.textContent;
  button.textContent = 'Salvando...';

  try {
    const resultado = await criarPlaylistSpotify(trackIds);
    showToast('Playlist salva no seu Spotify!');
    if (resultado && resultado.url) {
      window.open(resultado.url, '_blank', 'noopener,noreferrer');
    }
  } catch (err) {
    console.error('Erro ao salvar playlist no Spotify:', err);
    showErrorBanner(err.message || 'Não foi possível salvar a playlist no Spotify.', () =>
      handleSalvarSpotify(button, trackIds)
    );
  } finally {
    button.disabled = false;
    button.textContent = textoOriginal;
  }
}

/**
 * Handler de logout (Ticket 4.5 / KAN-40): acionado ao clicar no botão de
 * Spotify quando a sessão já está conectada (ver setupEventListeners).
 * Critérios de aceite: (1) após o logout a UI volta ao estado anônimo —
 * `isSpotifyAuthenticated` some, o botão e as ações Spotify-gated somem
 * junto; (2) o histórico da conversa atual permanece intacto — não toca em
 * `messages` nem re-renderiza os balões, só a UI/estado de autenticação.
 * Falha na chamada vira showErrorBanner (nunca falha silenciosa), reaproveitando
 * o mesmo padrão do Ticket 4.8 (KAN-75).
 */
async function handleLogoutSpotify() {
  if (!btnSpotifyAuth || btnSpotifyAuth.disabled) return;

  btnSpotifyAuth.disabled = true;
  const label = btnSpotifyAuth.querySelector('span');
  if (label) label.textContent = 'Desconectando...';

  try {
    await logoutSpotify(currentSessionId);
    isSpotifyAuthenticated = false;
    spotifyDisplayName = null;
    removerAcoesSpotifyGated();
    showToast('Desconectado do Spotify.');
  } catch (err) {
    console.error('Erro ao desconectar do Spotify:', err);
    showErrorBanner('Não foi possível desconectar do Spotify. Tente novamente.', handleLogoutSpotify);
  } finally {
    btnSpotifyAuth.disabled = false;
    // Ressincroniza label/classe/title com o `isSpotifyAuthenticated` atual —
    // volta ao estado anônimo em caso de sucesso, ou restaura "conectado" se
    // a chamada falhou (nada mudou no backend nesse caso).
    atualizarBotaoSpotifyAuth();
  }
}

/**
 * Remove as ações "Salvar no Spotify" já renderizadas em respostas
 * anteriores da conversa atual (Ticket 4.5 / KAN-40) — depois do logout elas
 * dariam 401 se clicadas. O texto e os cards de faixa das mensagens
 * permanecem intactos; some só essa ação Spotify-gated (critério de aceite
 * de UI voltar ao estado anônimo, sem apagar a conversa).
 */
function removerAcoesSpotifyGated() {
  document.querySelectorAll('.btn-salvar-spotify').forEach((btn) => btn.remove());
}

// ==========================================
// 3. Controlador da Interface e Estado
// ==========================================
let currentSessionId = null;
let messages = [];
let isProcessing = false;
// Ticket 12.2 (KAN-105): reflete se a sessão atual tem login Spotify ativo
// no backend (GET /auth/status) — controla se o botão "Salvar no Spotify"
// aparece nos cards de resposta. Começa false (fail-closed): enquanto não
// confirmamos com o backend, não mostramos ação que exige autenticação.
let isSpotifyAuthenticated = false;
// Ticket 20.8 (KAN-167): display_name do usuário Spotify logado, pra mostrar
// no header em vez do rótulo genérico. Cache em memória — só busca de novo
// ao (re)autenticar (init/logout), não a cada render do botão.
let spotifyDisplayName = null;
// Ticket 12.4 (KAN-107): track_ids de toda faixa já mostrada nesta sessão
// (acumulado no cliente a partir de msg.faixas de cada resposta do agente),
// usado pelo botão "Gerar outra recomendação" pra pedir uma busca nova sem
// repetir o que já apareceu.
const faixasMostradasSessao = new Set();

function atualizarFaixasMostradas(faixas) {
  if (!Array.isArray(faixas)) return;
  faixas.forEach((faixa) => {
    if (faixa && faixa.track_id) faixasMostradasSessao.add(faixa.track_id);
  });
}

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
const btnThemeToggle = document.getElementById('btn-theme-toggle');
const iconThemeDark = document.getElementById('icon-theme-dark');
const iconThemeLight = document.getElementById('icon-theme-light');
const btnHeaderMenu = document.getElementById('btn-header-menu');
const headerMenuPanel = document.querySelector('.header-menu-panel');

// ==========================================
// 2.1 Módulo de Tema Claro/Escuro (Ticket 12.5 / KAN-108)
// ==========================================
const THEME_STORAGE_KEY = 'resia_theme';

function getStoredTheme() {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY);
  } catch (e) {
    console.warn('Falha ao ler preferência de tema do localStorage:', e);
    return null;
  }
}

function saveStoredTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (e) {
    console.warn('Falha ao salvar preferência de tema no localStorage:', e);
  }
}

/**
 * Aplica o tema imediatamente (sem reload — critério de aceite do ticket
 * 12.5) alternando `data-theme` na raiz do documento; style.css cuida do
 * resto via `[data-theme="light"]` sobrescrevendo os tokens de cor.
 */
function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  if (iconThemeDark) iconThemeDark.style.display = theme === 'light' ? 'none' : '';
  if (iconThemeLight) iconThemeLight.style.display = theme === 'light' ? '' : 'none';
  if (btnThemeToggle) {
    btnThemeToggle.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
    btnThemeToggle.title = theme === 'light' ? 'Mudar para tema escuro' : 'Mudar para tema claro';
  }
}

function toggleTheme() {
  const temaAtual = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  const novoTema = temaAtual === 'light' ? 'dark' : 'light';
  applyTheme(novoTema);
  saveStoredTheme(novoTema);
}

// ==========================================
// 2.2 Menu "···" de ações secundárias do header (Ticket 20.6 / KAN-165)
// ==========================================
function closeHeaderMenu() {
  if (!btnHeaderMenu || !headerMenuPanel) return;
  headerMenuPanel.classList.remove('is-open');
  headerMenuPanel.setAttribute('aria-hidden', 'true');
  btnHeaderMenu.setAttribute('aria-expanded', 'false');
}

function toggleHeaderMenu() {
  if (!btnHeaderMenu || !headerMenuPanel) return;
  const isOpen = headerMenuPanel.classList.toggle('is-open');
  headerMenuPanel.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
  btnHeaderMenu.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

async function init() {
  // Ticket 12.5 (KAN-108): sincroniza os ícones/estado do botão com o
  // `data-theme` que o script inline no <head> já aplicou na raiz do
  // documento antes da primeira pintura (evita flash de tema errado).
  applyTheme(document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark');

  currentSessionId = getSessionId();
  updateSessionDisplay();
  setupEventListeners();
  tratarRetornoLoginSpotify();

  // Bloqueia novo input enquanto o histórico é recuperado (Ticket 4.6, critério de aceite:
  // "mensagens anteriores aparecem antes de qualquer novo envio").
  isProcessing = true;
  if (btnSend) btnSend.disabled = true;

  // Garante que `currentSessionId` existe de verdade no backend antes de qualquer
  // chamada que dependa dele — um id gerado só no cliente (getSessionId acima)
  // nunca foi registrado via POST /session, e tanto /auth/status quanto /chat
  // rejeitam session_id desconhecido.
  await carregarHistoricoInicial();

  // Ticket 12.2 (KAN-105): resolve o status de autenticação Spotify antes de
  // renderizar qualquer bolha de mensagem, pra já nascer com o botão
  // "Salvar no Spotify" no estado certo (sem esperar reload/re-render).
  isSpotifyAuthenticated = await verificarStatusSpotify(currentSessionId);
  spotifyDisplayName = isSpotifyAuthenticated ? await buscarNomeUsuarioSpotify(currentSessionId) : null;
  atualizarBotaoSpotifyAuth();

  isProcessing = false;
  if (btnSend) btnSend.disabled = !chatInput || chatInput.value.trim().length === 0;
}

/**
 * Reflete `isSpotifyAuthenticated` no botão do header (ticket 12.2) — feedback
 * visível de que a sessão já está conectada, sem precisar clicar de novo.
 *
 * Também dispara `resia:spotify-auth-changed` (Ticket 20.7 / KAN-166): é o
 * único ponto do app que muda `isSpotifyAuthenticated` (init/logout), então
 * é o lugar certo pra avisar quem precisa nascer/sumir com o estado de auth
 * — ex. o widget "Tocando agora" (components/nowPlaying.js), que nunca pode
 * aparecer pra usuário anônimo.
 */
function atualizarBotaoSpotifyAuth() {
  if (!btnSpotifyAuth) return;
  const label = btnSpotifyAuth.querySelector('span');
  if (isSpotifyAuthenticated) {
    btnSpotifyAuth.classList.add('btn-spotify-auth--connected');
    // Ticket 4.5 (KAN-40): o botão agora também é a ação de logout.
    btnSpotifyAuth.title = 'Clique para desconectar do Spotify';
    // Ticket 20.8 (KAN-167): mostra o nome de quem está logado quando
    // disponível; cai no rótulo genérico se a conta não tem nome público.
    if (label) label.textContent = spotifyDisplayName || 'Spotify conectado';
  } else {
    btnSpotifyAuth.classList.remove('btn-spotify-auth--connected');
    btnSpotifyAuth.title = 'Conectar com o Spotify para recomendações personalizadas';
    if (label) label.textContent = 'Conectar Spotify';
  }
  window.dispatchEvent(new CustomEvent('resia:spotify-auth-changed', { detail: { authenticated: isSpotifyAuthenticated } }));
}

/**
 * Recupera o histórico ao reabrir a conversa (Ticket 4.6):
 * 1. Tenta buscar o histórico salvo no backend (GET /chat/historico).
 * 2. Sessão válida: usa o histórico do backend e sincroniza o cache local.
 * 3. Sessão inválida/expirada (404): estado de conversa nova, sem erro visível ao usuário.
 * 4. Backend inacessível (rede/timeout): mantém o comportamento anterior, restaurando do
 *    localStorage — não regride a experiência quando offline.
 */
async function carregarHistoricoInicial(resultado) {
  // `init` já consulta o backend para validar/criar a sessão antes de chamar
  // esta função. Mantemos a leitura aqui como fallback para usos futuros que
  // chamem a função isoladamente.
  if (resultado === undefined) {
    resultado = await buscarHistoricoRemoto(currentSessionId);
  }

  if (resultado === null) {
    messages = loadChatHistory(currentSessionId);
  } else if (resultado.valida) {
    messages = resultado.mensagens;
    saveChatHistory(currentSessionId, messages);
  } else {
    // Sessão local não existe no backend (id gerado pelo cliente, ou expirada) —
    // registra uma sessão de verdade agora, pra POST /chat não cair em 404
    // sessao_invalida no primeiro envio.
    const idAntigo = currentSessionId;
    const novoId = await criarSessaoRemota();
    if (novoId) {
      currentSessionId = novoId;
      saveSessionId(novoId);
      updateSessionDisplay();
    }
    messages = [];
    clearChatHistory(idAntigo);
  }

  // Ticket 12.4 (KAN-107): semeia o set de faixas já mostradas a partir do
  // histórico restaurado — cobre o caso de cache local (localStorage guarda
  // msg.faixas completo); histórico vindo do backend não traz faixas (ver
  // mapearHistoricoRemoto), então não contribui aqui, mesma limitação já
  // documentada pros cards de faixa não reconstruídos.
  messages.forEach((msg) => atualizarFaixasMostradas(msg.faixas));

  // Ticket 4.12 (KAN-79): sessão restaurada já tem histórico -> não mostra onboarding.
  // (a checagem de messages.length abaixo já cobre isso; sem novo fetch local aqui,
  // que sobrescreveria o resultado do 4.6 acima com o cache desatualizado.)
  if (messages.length > 0) {
    if (heroEmptyState) heroEmptyState.style.display = 'none';
    messages.forEach((msg) => renderMessageBubble(msg, false));
    scrollToBottom();
  }
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

  btnNewChat?.addEventListener('click', async () => {
    if (isProcessing) return;
    currentSessionId = await resetSession();
    messages = [];
    faixasMostradasSessao.clear();
    messagesContainer.innerHTML = '';
    // Ticket 4.12 (KAN-79): nova conversa volta a ficar sem histórico -> onboarding reaparece.
    if (heroEmptyState) heroEmptyState.style.display = 'flex';
    updateSessionDisplay();
    showToast('Nova conversa iniciada!');
    chatInput?.focus();
  });

  btnSpotifyAuth?.addEventListener('click', () => {
    // Ticket 4.5 (KAN-40): sessão já conectada -> o mesmo botão desconecta
    // em vez de iniciar um novo fluxo OAuth (evita duplicar todo o padrão
    // de botão de auth só pra um logout).
    if (isSpotifyAuthenticated) {
      handleLogoutSpotify();
      return;
    }

    // Ticket 4.7 (KAN-74): antes de qualquer redirect real pro Spotify, o
    // usuário passa pela página de consentimento própria do backend
    // (GET /auth/login → spotify_auth/consent.py), que lista os scopes
    // lidos e a política de dados (ticket 5.10) e só depois linka pro
    // redirect de fato (GET /auth/login/start). Abrimos essa página em vez
    // de replicar o texto aqui pra não divergir do que o backend descreve.
    window.location.href = `${API_BASE_URL}/auth/login?session_id=${encodeURIComponent(currentSessionId)}`;
  });

  btnThemeToggle?.addEventListener('click', toggleTheme);

  // Ticket 20.6 (KAN-165): abre/fecha o menu "···" e fecha em clique fora,
  // Esc ou seleção de qualquer item (tema, QR login, Explorar Spotify).
  btnHeaderMenu?.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleHeaderMenu();
  });

  headerMenuPanel?.addEventListener('click', (e) => {
    if (e.target.closest('.header-menu-item')) closeHeaderMenu();
  });

  document.addEventListener('click', (e) => {
    if (!headerMenuPanel || !headerMenuPanel.classList.contains('is-open')) return;
    if (headerMenuPanel.contains(e.target) || btnHeaderMenu?.contains(e.target)) return;
    closeHeaderMenu();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeHeaderMenu();
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

function criarResumoDiversidadeECobertura(resposta) {
  // Ticket 6.2: os números já calculados pelo backend aparecem junto das
  // recomendações, em linguagem simples. O indicador também deixa explícito
  // quando popularidade participa do ranqueamento, sem esconder esse sinal.
  const diversidade = Number(resposta.diversidade_generos) || 0;
  const cobertura = Math.max(0, Math.min(1, Number(resposta.cobertura_sessao) || 0));
  const resumo = document.createElement('aside');
  resumo.className = 'recommendation-metrics';
  resumo.setAttribute('aria-label', 'Resumo de diversidade e novidade das recomendações');
  resumo.innerHTML = `
    <span><strong>${diversidade}</strong> gênero${diversidade === 1 ? '' : 's'} na seleção</span>
    <span><strong>${Math.round(cobertura * 100)}%</strong> de faixas novas nesta conversa</span>
    <small>O resultado combina seu pedido com sinais como popularidade, sem definir sozinho a recomendação.</small>
  `;
  return resumo;
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

    if (msg.metricas) {
      bubble.appendChild(criarResumoDiversidadeECobertura(msg.metricas));
    }

    // Ações logo abaixo dos cards de faixa — só faz sentido pra respostas do
    // agente (nunca numa mensagem do próprio usuário).
    if (msg.role === 'agent') {
      const actionsRow = document.createElement('div');
      actionsRow.className = 'response-actions';

      // Ticket 12.4 (KAN-107): "Gerar outra recomendação" aparece em toda
      // resposta com faixas, sessão autenticada ou não.
      const btnOutraRecomendacao = document.createElement('button');
      btnOutraRecomendacao.type = 'button';
      btnOutraRecomendacao.className = 'btn-response-action btn-outra-recomendacao';
      btnOutraRecomendacao.textContent = 'Gerar outra recomendação';
      btnOutraRecomendacao.addEventListener('click', () => {
        if (isProcessing) return;
        enviarMensagemUsuario('Gere outra recomendação, sem repetir as músicas já mostradas.', {
          extras: { faixas_ja_mostradas: Array.from(faixasMostradasSessao) },
        });
      });
      actionsRow.appendChild(btnOutraRecomendacao);

      // Ticket 12.2 (KAN-105): "Salvar no Spotify" só aparece pra sessão
      // autenticada — nunca tenta a ação sabendo de antemão que vai dar 401.
      if (isSpotifyAuthenticated) {
        const trackIds = msg.faixas.map((faixa) => faixa && faixa.track_id).filter(Boolean);
        const btnSalvar = document.createElement('button');
        btnSalvar.type = 'button';
        btnSalvar.className = 'btn-response-action btn-salvar-spotify';
        btnSalvar.textContent = 'Salvar no Spotify';
        btnSalvar.addEventListener('click', () => handleSalvarSpotify(btnSalvar, trackIds));
        actionsRow.appendChild(btnSalvar);
      }

      bubble.appendChild(actionsRow);
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

async function enviarMensagemUsuario(texto, { isRetry = false, extras = {} } = {}) {
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
    const resposta = await enviarMensagem(currentSessionId, texto, extras);

    const agentMsg = {
      id: `agent-${Date.now()}`,
      role: 'agent',
      conteudo: resposta.mensagem || 'Recomendações prontas!',
      faixas: resposta.faixas || [],
      metricas: resposta,
      timestamp: new Date().toISOString(),
    };
    messages.push(agentMsg);
    atualizarFaixasMostradas(agentMsg.faixas);
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
  enviarMensagem,
  enviarMensagemUsuario,
  buscarHistoricoRemoto,
  criarSessaoRemota,
  ErroBackend,
  showErrorBanner,
  verificarStatusSpotify,
  buscarNomeUsuarioSpotify,
  criarPlaylistSpotify,
  logoutSpotify,
  atualizarFaixasMostradas,
  applyTheme,
  toggleTheme,
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
