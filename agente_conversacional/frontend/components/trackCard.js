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

    <!-- Ações Rápidas: Abrir e Copiar Link -->
    <div class="track-actions-group">
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
