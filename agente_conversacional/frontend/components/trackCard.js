/**
 * trackCard.js — Componente de Cards de Faixa a partir da Lista Estruturada (Ticket 4.2)
 * Grupo 8 ResIA — Agente Conversacional de Recomendação Musical
 *
 * CRITÉRIO DE ACEITE:
 * "Cards montados a partir do campo faixas da resposta, não fazendo parsing do texto livre."
 */

/**
 * Paleta de gradientes temáticos para os gêneros musicais do dataset (Kaggle 114k faixas).
 * Inspirado nas capas de playlists editoriais do Spotify.
 */
const GENRE_THEMES = {
  pagode: { bg: 'linear-gradient(135deg, #10b981 0%, #064e3b 100%)', text: '#34d399', accent: '#059669' },
  samba: { bg: 'linear-gradient(135deg, #059669 0%, #065f46 100%)', text: '#6ee7b7', accent: '#10b981' },
  rock: { bg: 'linear-gradient(135deg, #dc2626 0%, #450a0a 100%)', text: '#f87171', accent: '#b91c1c' },
  'hard-rock': { bg: 'linear-gradient(135deg, #b91c1c 0%, #3a0000 100%)', text: '#fca5a5', accent: '#991b1b' },
  metal: { bg: 'linear-gradient(135deg, #4b5563 0%, #111827 100%)', text: '#9ca3af', accent: '#374151' },
  chill: { bg: 'linear-gradient(135deg, #0284c7 0%, #082f49 100%)', text: '#38bdf8', accent: '#0369a1' },
  ambient: { bg: 'linear-gradient(135deg, #0d9488 0%, #134e4a 100%)', text: '#2dd4bf', accent: '#0f766e' },
  pop: { bg: 'linear-gradient(135deg, #ec4899 0%, #831843 100%)', text: '#f472b6', accent: '#be185d' },
  dance: { bg: 'linear-gradient(135deg, #f59e0b 0%, #78350f 100%)', text: '#fbbf24', accent: '#d97706' },
  mpb: { bg: 'linear-gradient(135deg, #ea580c 0%, #431407 100%)', text: '#fb923c', accent: '#c2410c' },
  acoustic: { bg: 'linear-gradient(135deg, #d97706 0%, #451a03 100%)', text: '#fde68a', accent: '#b45309' },
  jazz: { bg: 'linear-gradient(135deg, #8b5cf6 0%, #2e1065 100%)', text: '#c4b5fd', accent: '#6d28d9' },
  classical: { bg: 'linear-gradient(135deg, #64748b 0%, #0f172a 100%)', text: '#cbd5e1', accent: '#475569' },
  'hip-hop': { bg: 'linear-gradient(135deg, #6366f1 0%, #1e1b4b 100%)', text: '#a5b4fc', accent: '#4338ca' },
  reggae: { bg: 'linear-gradient(135deg, #16a34a 0%, #14532d 100%)', text: '#86efac', accent: '#15803d' },
  blues: { bg: 'linear-gradient(135deg, #2563eb 0%, #172554 100%)', text: '#93c5fd', accent: '#1d4ed8' },
  default: { bg: 'linear-gradient(135deg, #2a2a2a 0%, #151515 100%)', text: '#1db954', accent: '#1db954' },
};

/**
 * Retorna o tema visual para um gênero musical.
 */
function getGenreTheme(genero) {
  if (!genero) return GENRE_THEMES.default;
  const key = String(genero).toLowerCase().trim();
  return GENRE_THEMES[key] || GENRE_THEMES.default;
}

// ==========================================
// Preview de áudio (Ticket 13.12 / KAN-121). Tenta a prévia nativa da
// Spotify primeiro (GET /explorer/track/{id}, precisa de sessão autenticada
// com Spotify). Quando preview_url vier null — o caso comum: a Spotify
// parou de preencher esse campo pra apps criados após nov/2024, ver
// docs/superpowers/specs/2026-09-03-spotify-preview-player-design.md — cai
// pro YouTube (GET /youtube/preview, sem exigir login) tocado no widget
// visível de youtubePlayer.js (nunca áudio escondido, ver política de API
// Services do YouTube sobre player "só-áudio").
// ==========================================

const _PREVIEW_API_BASE_URL =
  window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
    ? ''
    : 'http://127.0.0.1:8000';

const _previewAudio = new Audio();
let _previewTrackId = null;
let _previewSource = null; // 'spotify' | 'youtube' | null
let _previewButtonEl = null;
const _previewCache = new Map(); // track_id -> { source: 'spotify', url } | { source: 'youtube', videoId } | { source: null }

function _setPreviewButtonState(state) {
  if (!_previewButtonEl) return;
  _previewButtonEl.classList.toggle('playing', state === 'playing');
  _previewButtonEl.classList.toggle('loading', state === 'loading');
  _previewButtonEl.setAttribute('aria-label', state === 'playing' ? 'Pausar prévia' : 'Tocar prévia');
}

function _pararPreviewAtual() {
  _previewAudio.pause();
  if (window.ResIAYoutubeWidget) window.ResIAYoutubeWidget.pause();
  if (_previewButtonEl) _setPreviewButtonState('idle');
  _previewTrackId = null;
  _previewSource = null;
  _previewButtonEl = null;
}

_previewAudio.addEventListener('ended', () => {
  if (_previewSource === 'spotify') _pararPreviewAtual();
});

if (window.ResIAYoutubeWidget) {
  // Cobre pause/fim disparado pelos controles nativos do widget do YouTube,
  // não só pelo botão do card.
  window.ResIAYoutubeWidget.onExternalPause(() => {
    if (_previewSource === 'youtube') _pararPreviewAtual();
  });
}

/**
 * Resolve de onde tocar a prévia de uma faixa: preview_url nativo da
 * Spotify primeiro, YouTube como fallback. Resultado cacheado por faixa —
 * nunca refaz as duas chamadas pra mesma faixa na mesma sessão de página.
 */
async function _resolvePreview(trackId, nome, artista) {
  if (_previewCache.has(trackId)) return _previewCache.get(trackId);

  let resultado = { source: null };

  // Sem sessão Spotify autenticada, GET /explorer/track/{id} sempre devolve
  // 401 — pula direto pro fallback do YouTube em vez de garantir um erro
  // no console a cada clique de prévia.
  const spotifyAutenticado =
    window.ResIA && typeof window.ResIA.isSpotifyAuthenticated === 'function' && window.ResIA.isSpotifyAuthenticated();
  const sessionId =
    spotifyAutenticado && typeof window.ResIA.getSessionId === 'function' ? window.ResIA.getSessionId() : null;
  if (sessionId) {
    try {
      const response = await fetch(
        `${_PREVIEW_API_BASE_URL}/explorer/track/${encodeURIComponent(trackId)}?session_id=${encodeURIComponent(sessionId)}`
      );
      if (response.ok) {
        const track = await response.json();
        if (track.preview_url) {
          resultado = { source: 'spotify', url: track.preview_url };
        }
      }
    } catch (err) {
      console.warn('Falha ao consultar prévia da Spotify:', err);
    }
  }

  if (resultado.source === null) {
    try {
      const params = new URLSearchParams({ nome: nome || '' });
      if (artista) params.set('artista', artista);
      const response = await fetch(`${_PREVIEW_API_BASE_URL}/youtube/preview?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        if (data.video_id) {
          resultado = { source: 'youtube', videoId: data.video_id };
        }
      }
    } catch (err) {
      console.warn('Falha ao buscar prévia no YouTube:', err);
    }
  }

  _previewCache.set(trackId, resultado);
  return resultado;
}

async function togglePreview(trackId, nome, artista, buttonEl) {
  if (!trackId) return;

  // Já é a faixa carregada: alterna play/pause (Spotify) ou para (YouTube —
  // o widget tem controles próprios visíveis pra retomar).
  if (_previewTrackId === trackId && _previewButtonEl === buttonEl) {
    if (_previewSource === 'spotify') {
      if (_previewAudio.paused) {
        _previewAudio.play().catch(() => {});
        _setPreviewButtonState('playing');
      } else {
        _previewAudio.pause();
        _setPreviewButtonState('idle');
      }
    } else {
      _pararPreviewAtual();
    }
    return;
  }

  // Troca de faixa: para a anterior e mostra loading na nova.
  _pararPreviewAtual();
  _previewButtonEl = buttonEl;
  _setPreviewButtonState('loading');

  const preview = await _resolvePreview(trackId, nome, artista);

  if (preview.source === 'spotify') {
    _previewAudio.src = preview.url;
    _previewAudio.play().catch(() => {});
    _previewTrackId = trackId;
    _previewSource = 'spotify';
    _setPreviewButtonState('playing');
  } else if (preview.source === 'youtube' && window.ResIAYoutubeWidget) {
    await window.ResIAYoutubeWidget.play(preview.videoId);
    _previewTrackId = trackId;
    _previewSource = 'youtube';
    _setPreviewButtonState('playing');
  } else {
    _setPreviewButtonState('idle');
    _previewButtonEl = null;
    if (typeof window.showToast === 'function') {
      window.showToast(`Prévia de "${nome}" não encontrada.`);
    }
  }
}

// ==========================================
// Miniatura de capa do álbum. Usa o oEmbed público da Spotify
// (GET /spotify/thumbnail/{track_id}, sem exigir login) — a capa real
// substitui o gradiente temático assim que carrega; sem thumbnail
// disponível, o gradiente + ícone de vinil (já no HTML) continuam sendo o
// fallback visual, sem nenhuma mudança de layout.
// ==========================================

const _thumbnailCache = new Map(); // track_id -> url | null

async function _carregarThumbnail(trackId) {
  if (_thumbnailCache.has(trackId)) return _thumbnailCache.get(trackId);

  try {
    const response = await fetch(`${_PREVIEW_API_BASE_URL}/spotify/thumbnail/${encodeURIComponent(trackId)}`);
    if (!response.ok) {
      _thumbnailCache.set(trackId, null);
      return null;
    }
    const data = await response.json();
    const url = data.thumbnail_url || null;
    _thumbnailCache.set(trackId, url);
    return url;
  } catch (err) {
    console.warn('Falha ao buscar miniatura da faixa:', err);
    return null;
  }
}

// ==========================================
// Tocar no dispositivo Spotify Connect ativo (Ticket 13.14). Com sessão
// autenticada, clicar no card toca a faixa direto no dispositivo ativo do
// usuário (ex.: o Spotify aberto no celular) em vez de abrir
// open.spotify.com numa nova aba — sem autenticação, mantém o link normal
// (não dá pra controlar playback sem token).
// ==========================================

async function _tocarNoDispositivoAtivo(trackId, nome) {
  const sessionId = window.ResIA && typeof window.ResIA.getSessionId === 'function' ? window.ResIA.getSessionId() : null;
  if (!sessionId) return;

  try {
    const response = await fetch(`${_PREVIEW_API_BASE_URL}/explorer/track/play?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_id: trackId }),
    });

    if (response.ok) {
      if (typeof window.showToast === 'function') window.showToast(`Tocando "${nome}" no seu Spotify.`);
      return;
    }

    const corpo = await response.json().catch(() => null);
    const mensagem = (corpo && corpo.detail && corpo.detail.mensagem) || 'Não foi possível tocar essa faixa no Spotify agora.';
    if (typeof window.showToast === 'function') window.showToast(mensagem);
  } catch (err) {
    console.warn('Falha ao tocar faixa no Spotify Connect:', err);
    if (typeof window.showToast === 'function') {
      window.showToast('Não foi possível tocar essa faixa no Spotify agora.');
    }
  }
}

/**
 * Escapa strings contra injeção de HTML.
 */
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Cria um card individual a partir de um objeto de faixa estruturado.
 * @param {Object} faixa Objeto contendo { track_id, nome, artista, album, genero }
 * @param {number} index Índice do card para animação sequencial
 * @returns {HTMLElement} Elemento DOM do card
 */
function createTrackCardElement(faixa, index = 0) {
  const trackId = faixa.track_id || '';
  const nome = faixa.nome || 'Faixa sem título';
  const artista = faixa.artista || 'Artista desconhecido';
  const album = faixa.album || '';
  const genero = faixa.genero || 'Geral';
  const theme = getGenreTheme(genero);

  const card = document.createElement('div');
  card.className = 'track-card';
  card.style.animationDelay = `${index * 0.07}s`;
  card.setAttribute('data-track-id', trackId);

  // Link para o Spotify
  const spotifyUrl = trackId ? `https://open.spotify.com/track/${trackId}` : '#';

  card.innerHTML = `
    <!-- Capa Estilizada com Gradiente Temático do Gênero -->
    <a href="${spotifyUrl}" target="_blank" rel="noopener noreferrer" class="track-cover-link" title="Ouvir &quot;${escapeHtml(nome)}&quot; no Spotify">
      <div class="track-cover-art" style="background: ${theme.bg};">
        <img class="track-cover-img" alt="" loading="lazy" style="display: none;">
        <svg class="vinyl-icon" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
        </svg>
        <div class="track-play-badge" title="Tocar no Spotify">
          <div class="play-circle">
            <svg viewBox="0 0 24 24">
              <polygon points="8 5 19 12 8 19 8 5"/>
            </svg>
          </div>
        </div>
      </div>
    </a>

    <!-- Detalhes da Faixa -->
    <div class="track-details">
      <a href="${spotifyUrl}" target="_blank" rel="noopener noreferrer" class="track-name-link">
        <h4 class="track-name" title="${escapeHtml(nome)}">${escapeHtml(nome)}</h4>
      </a>
      <p class="track-artist" title="${escapeHtml(artista)}${album ? ' · ' + escapeHtml(album) : ''}">
        <span class="artist-name">${escapeHtml(artista)}</span>
        ${album ? `<span class="album-separator">·</span><span class="album-name">${escapeHtml(album)}</span>` : ''}
      </p>
      <div class="track-tags">
        <span class="genre-pill" style="border-left: 3px solid ${theme.text};">${escapeHtml(genero)}</span>
      </div>
    </div>

    <!-- Ações Rápidas: Salvar, Prévia, Abrir e Copiar Link -->
    <div class="track-actions-group">
      <button type="button" class="btn-track-action btn-track-save" title="Salvar em Músicas Curtidas" aria-label="Salvar em Músicas Curtidas">
        <svg class="icon-save-outline" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"/>
        </svg>
        <svg class="icon-save-filled" width="15" height="15" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
          <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"/>
        </svg>
      </button>
      <button type="button" class="btn-track-action btn-track-preview" title="Tocar prévia de 30s" aria-label="Tocar prévia de 30s">
        <svg class="icon-preview-play" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="6 3 20 12 6 21 6 3"/>
        </svg>
        <svg class="icon-preview-pause" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
          <rect x="5" y="3" width="5" height="18"/><rect x="14" y="3" width="5" height="18"/>
        </svg>
      </button>
      <button type="button" class="btn-track-action btn-copy-track-link" title="Copiar link do Spotify" data-url="${spotifyUrl}">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
      <a href="${spotifyUrl}" target="_blank" rel="noopener noreferrer" class="btn-track-action btn-open-spotify" title="Abrir no Spotify">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
          <polyline points="15 3 21 3 21 9"></polyline>
          <line x1="10" y1="14" x2="21" y2="3"></line>
        </svg>
      </a>
    </div>
  `;

  // Miniatura de capa (oEmbed da Spotify) — substitui o gradiente quando carrega.
  if (trackId) {
    const coverImg = card.querySelector('.track-cover-img');
    const vinylIcon = card.querySelector('.vinyl-icon');
    _carregarThumbnail(trackId).then((url) => {
      if (!url || !coverImg) return;
      coverImg.src = url;
      coverImg.style.display = 'block';
      if (vinylIcon) vinylIcon.style.display = 'none';
    });
  }

  // Clique na capa/nome: com Spotify autenticado, toca no dispositivo ativo
  // (ex.: celular) em vez de abrir open.spotify.com numa nova aba (ticket 13.14).
  if (trackId) {
    const linksDaFaixa = [card.querySelector('.track-cover-link'), card.querySelector('.track-name-link')];
    linksDaFaixa.forEach((link) => {
      if (!link) return;
      link.addEventListener('click', (e) => {
        const autenticado =
          window.ResIA && typeof window.ResIA.isSpotifyAuthenticated === 'function' && window.ResIA.isSpotifyAuthenticated();
        if (!autenticado) return; // sem sessão Spotify, mantém o link normal (abre no Spotify)
        e.preventDefault();
        e.stopPropagation();
        _tocarNoDispositivoAtivo(trackId, nome);
      });
    });
  }

  // Ouvinte do botão "Salvar em Músicas Curtidas" (ticket 13.15)
  const saveBtn = card.querySelector('.btn-track-save');
  if (saveBtn && trackId) {
    saveBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      e.preventDefault();
      if (saveBtn.classList.contains('saved') || saveBtn.classList.contains('loading')) return;

      const autenticado =
        window.ResIA && typeof window.ResIA.isSpotifyAuthenticated === 'function' && window.ResIA.isSpotifyAuthenticated();
      if (!autenticado) {
        if (typeof window.showToast === 'function') window.showToast('Conecte com o Spotify pra salvar faixas.');
        return;
      }

      const sessionId = typeof window.ResIA.getSessionId === 'function' ? window.ResIA.getSessionId() : null;
      if (!sessionId) return;

      saveBtn.classList.add('loading');
      try {
        const response = await fetch(
          `${_PREVIEW_API_BASE_URL}/explorer/track/${encodeURIComponent(trackId)}/save?session_id=${encodeURIComponent(sessionId)}`,
          { method: 'POST' }
        );
        if (response.ok) {
          saveBtn.classList.add('saved');
          saveBtn.setAttribute('aria-label', 'Salva em Músicas Curtidas');
          saveBtn.title = 'Salva em Músicas Curtidas';
          if (typeof window.showToast === 'function') window.showToast(`"${nome}" salva em Músicas Curtidas.`);
        } else {
          const corpo = await response.json().catch(() => null);
          const mensagem = (corpo && corpo.detail && corpo.detail.mensagem) || 'Não foi possível salvar essa faixa agora.';
          if (typeof window.showToast === 'function') window.showToast(mensagem);
        }
      } catch (err) {
        console.warn('Falha ao salvar faixa no Spotify:', err);
        if (typeof window.showToast === 'function') window.showToast('Não foi possível salvar essa faixa agora.');
      } finally {
        saveBtn.classList.remove('loading');
      }
    });
  }

  // Ouvinte para o botão de prévia de 30s (ticket 13.12)
  const previewBtn = card.querySelector('.btn-track-preview');
  if (previewBtn && trackId) {
    previewBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePreview(trackId, nome, artista, previewBtn);
    });
  }

  // Ouvinte para cópia do link do Spotify
  const copyBtn = card.querySelector('.btn-copy-track-link');
  if (copyBtn) {
    copyBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const url = copyBtn.getAttribute('data-url');
      try {
        await navigator.clipboard.writeText(url);
        copyBtn.classList.add('copied');
        setTimeout(() => copyBtn.classList.remove('copied'), 1500);
        if (typeof window.showToast === 'function') {
          window.showToast(`Link de "${nome}" copiado!`);
        }
      } catch (err) {
        console.warn('Erro ao copiar link:', err);
      }
    });
  }

  return card;
}

/**
 * Renderiza o contêiner de cards exclusivamente a partir do array estruturado `faixas`.
 * NUNCA faz parsing de texto livre.
 *
 * @param {Array<Object>} faixas Array de objetos retornado em resposta.faixas
 * @returns {HTMLElement|null} Elemento DOM da seção de faixas, ou null se a lista for vazia
 */
function renderTrackCards(faixas) {
  // Validação estrita do critério de aceite
  if (!Array.isArray(faixas) || faixas.length === 0) {
    return null;
  }

  const section = document.createElement('div');
  section.className = 'tracks-section';

  // Cabeçalho da Seção de Faixas
  const header = document.createElement('div');
  header.className = 'tracks-header';
  header.innerHTML = `
    <span class="tracks-title">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
      </svg>
      Faixas Recomendadas
      <span class="tracks-count-badge">${faixas.length}</span>
    </span>
  `;
  section.appendChild(header);

  // Grade / Carrossel de Cards
  const grid = document.createElement('div');
  grid.className = 'tracks-grid';

  faixas.forEach((faixa, index) => {
    // Apenas renderiza se o item for um objeto estruturado
    if (faixa && typeof faixa === 'object') {
      const cardElem = createTrackCardElement(faixa, index);
      grid.appendChild(cardElem);
    }
  });

  section.appendChild(grid);
  return section;
}

// Expõe globalmente para compatibilidade universal com scripts normais
if (typeof window !== 'undefined') {
  window.ResIATrackCard = {
    renderTrackCards,
    createTrackCardElement,
    getGenreTheme,
  };
}
