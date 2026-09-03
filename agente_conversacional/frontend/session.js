/**
 * session.js — Gerenciador de Sessão e Persistência (Ticket 4.1)
 * Grupo 8 ResIA — Agente Conversacional de Recomendação Musical
 */

const SESSION_STORAGE_KEY = 'resia_chat_session_id';
const HISTORY_STORAGE_PREFIX = 'resia_chat_history_';

/**
 * Gera um UUID v4 criptograficamente seguro com fallback.
 */
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

/**
 * Lê cookie por nome.
 */
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

/**
 * Salva cookie com validade em dias.
 */
function setCookie(name, value, days = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

/**
 * Recupera o session_id persistido ou gera e salva um novo.
 * Critério de aceite: Mantém o session_id entre mensagens (cookie/localStorage).
 */
export function getSessionId() {
  // 1. Tenta recuperar do localStorage
  let sessionId = null;
  try {
    sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  } catch (e) {
    console.warn('Falha ao ler localStorage:', e);
  }

  // 2. Fallback: tenta recuperar de cookies
  if (!sessionId) {
    sessionId = getCookie(SESSION_STORAGE_KEY);
  }

  // 3. Se ainda não existir, cria um novo UUID v4
  if (!sessionId) {
    sessionId = generateUUID();
    saveSessionId(sessionId);
  }

  return sessionId;
}

/**
 * Salva o session_id tanto no localStorage quanto nos cookies para redundância.
 */
export function saveSessionId(sessionId) {
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

/**
 * Reseta a sessão atual criando um novo session_id.
 * Usado pelo botão "Nova Conversa".
 */
export function resetSession() {
  const newSessionId = generateUUID();
  saveSessionId(newSessionId);
  return newSessionId;
}

/**
 * Salva o histórico de mensagens localmente para suporte a refresh (F5).
 */
export function saveChatHistory(sessionId, messages) {
  if (!sessionId) return;
  try {
    localStorage.setItem(HISTORY_STORAGE_PREFIX + sessionId, JSON.stringify(messages));
  } catch (e) {
    console.warn('Falha ao salvar histórico no localStorage:', e);
  }
}

/**
 * Carrega o histórico de mensagens da sessão atual se houver.
 */
export function loadChatHistory(sessionId) {
  if (!sessionId) return [];
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_PREFIX + sessionId);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.warn('Falha ao carregar histórico do localStorage:', e);
    return [];
  }
}

/**
 * Limpa o histórico de uma sessão específica.
 */
export function clearChatHistory(sessionId) {
  if (!sessionId) return;
  try {
    localStorage.removeItem(HISTORY_STORAGE_PREFIX + sessionId);
  } catch (e) {
    console.warn('Falha ao remover histórico do localStorage:', e);
  }
}
