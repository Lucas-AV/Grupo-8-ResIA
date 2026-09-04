/**
 * explorer.js — Painel "Explorar Spotify" (Épico 13 / KAN-123)
 * Grupo 8 ResIA — porta pro produto real as funcionalidades de navegação do
 * spotify_explorer (busca, faixa, artista, álbum, playlist, minhas
 * playlists, lançamentos, recomendações nativas, seguindo, meus dados).
 *
 * Autocontido, sem dependências externas — mesmo padrão de trackCard.js.
 * Usa window.ResIA.getSessionId()/verificarStatusSpotify() (app.js) e
 * window.showToast (app.js) em vez de duplicar essa lógica.
 */

(function () {
  const API_BASE_URL =
    window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
      ? ''
      : 'http://127.0.0.1:8000';

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  function sessionId() {
    return window.ResIA && typeof window.ResIA.getSessionId === 'function' ? window.ResIA.getSessionId() : null;
  }

  async function explorerFetch(path, { method = 'GET', params = {} } = {}) {
    const sid = sessionId();
    const query = new URLSearchParams({ session_id: sid, ...params });
    const url = `${API_BASE_URL}${path}?${query.toString()}`;
    const response = await fetch(url, { method });
    let body = null;
    try {
      body = await response.json();
    } catch (e) {
      body = null;
    }
    if (!response.ok) {
      const detail = body && body.detail ? body.detail : {};
      const err = new Error(detail.mensagem || `Falha ao consultar o Spotify (HTTP ${response.status})`);
      err.codigo = detail.codigo || 'erro_desconhecido';
      err.status = response.status;
      throw err;
    }
    return body;
  }

  // --- Estado do painel ---

  let panelEl = null;
  let contentEl = null;
  let tabsEl = null;
  let breadcrumbEl = null;
  let activeTab = 'search';
  let viewStack = []; // pilha de detalhes (track/artist/album/playlist) empilhados sobre a tab ativa

  const TABS = [
    { id: 'search', label: '🔍 Buscar' },
    { id: 'new-releases', label: '💿 Lançamentos' },
    { id: 'my-playlists', label: '📁 Minhas playlists' },
    { id: 'following', label: '👥 Seguindo' },
    { id: 'me', label: '👤 Meus dados' },
    { id: 'recommendations', label: '🎯 Recomendações' },
    { id: 'player', label: '🎚️ Player' },
  ];

  function ensurePanel() {
    if (panelEl) return;

    const overlay = document.createElement('div');
    overlay.id = 'explorer-overlay';
    overlay.className = 'explorer-overlay';
    overlay.hidden = true;
    overlay.innerHTML = `
      <div class="explorer-panel" role="dialog" aria-label="Explorar Spotify">
        <header class="explorer-header">
          <h2>Explorar Spotify</h2>
          <button type="button" class="explorer-close" title="Fechar" aria-label="Fechar">✕</button>
        </header>
        <nav class="explorer-tabs"></nav>
        <div class="explorer-breadcrumb" hidden></div>
        <div class="explorer-content"></div>
      </div>
    `;
    document.body.appendChild(overlay);

    panelEl = overlay;
    tabsEl = overlay.querySelector('.explorer-tabs');
    breadcrumbEl = overlay.querySelector('.explorer-breadcrumb');
    contentEl = overlay.querySelector('.explorer-content');

    overlay.querySelector('.explorer-close').addEventListener('click', closePanel);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closePanel();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !overlay.hidden) closePanel();
    });

    TABS.forEach((tab) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'explorer-tab-btn';
      btn.textContent = tab.label;
      btn.dataset.tab = tab.id;
      btn.addEventListener('click', () => selectTab(tab.id));
      tabsEl.appendChild(btn);
    });
  }

  // `tab` opcional (ex.: 'player', usado pelo widget "Tocando agora" —
  // Ticket 20.7 / KAN-166) abre o painel direto na aba pedida em vez da
  // última aba ativa.
  async function openPanel(tab) {
    ensurePanel();
    const autenticado = window.ResIA && typeof window.ResIA.verificarStatusSpotify === 'function'
      ? await window.ResIA.verificarStatusSpotify(sessionId())
      : false;
    if (!autenticado) {
      window.showToast && window.showToast('Conecte com o Spotify pra explorar sua conta.');
      return;
    }
    panelEl.hidden = false;
    document.body.classList.add('explorer-open');
    selectTab(tab || activeTab);
  }

  function closePanel() {
    if (!panelEl) return;
    panelEl.hidden = true;
    document.body.classList.remove('explorer-open');
  }

  function selectTab(tabId) {
    activeTab = tabId;
    viewStack = [];
    Array.from(tabsEl.children).forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    renderBreadcrumb();
    renderTab(tabId);
  }

  function pushDetail(kind, id, label) {
    viewStack.push({ kind, id, label });
    renderBreadcrumb();
    renderDetail(kind, id);
  }

  function renderBreadcrumb() {
    if (viewStack.length === 0) {
      breadcrumbEl.hidden = true;
      breadcrumbEl.innerHTML = '';
      return;
    }
    breadcrumbEl.hidden = false;
    const tabLabel = (TABS.find((t) => t.id === activeTab) || {}).label || '';
    const crumbs = [`<button type="button" data-back-to="-1">${escapeHtml(tabLabel)}</button>`].concat(
      viewStack.map((v, i) => `<button type="button" data-back-to="${i}">${escapeHtml(v.label)}</button>`)
    );
    breadcrumbEl.innerHTML = crumbs.join(' <span class="crumb-sep">›</span> ');
    breadcrumbEl.querySelectorAll('button').forEach((btn) => {
      btn.addEventListener('click', () => {
        const backTo = parseInt(btn.dataset.backTo, 10);
        viewStack = viewStack.slice(0, backTo + 1);
        renderBreadcrumb();
        if (viewStack.length === 0) {
          renderTab(activeTab);
        } else {
          const top = viewStack[viewStack.length - 1];
          renderDetail(top.kind, top.id);
        }
      });
    });
  }

  function setLoading(label) {
    contentEl.innerHTML = `<div class="explorer-loading">Carregando ${escapeHtml(label || '')}…</div>`;
  }

  function setError(err) {
    contentEl.innerHTML = `<div class="explorer-error">⚠️ ${escapeHtml(err.message || 'Algo deu errado.')}</div>`;
  }

  // --- Cards de item genéricos (usados em busca/lançamentos/playlists/seguindo) ---

  function itemCardHtml({ image, title, subtitle, kind, id }) {
    const cover = image
      ? `<img src="${escapeHtml(image)}" alt="" loading="lazy">`
      : `<div class="explorer-item-cover-placeholder">🎵</div>`;
    return `
      <button type="button" class="explorer-item-card" data-kind="${escapeHtml(kind)}" data-id="${escapeHtml(id)}">
        <div class="explorer-item-cover">${cover}</div>
        <div class="explorer-item-text">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(subtitle || '')}</span>
        </div>
      </button>
    `;
  }

  function bindItemCards(container) {
    container.querySelectorAll('.explorer-item-card').forEach((card) => {
      card.addEventListener('click', () => {
        const kind = card.dataset.kind;
        const id = card.dataset.id;
        const title = card.querySelector('strong').textContent;
        pushDetail(kind, id, title);
      });
    });
  }

  // --- Tab: Buscar (13.1) ---

  function renderSearchTab() {
    contentEl.innerHTML = `
      <form class="explorer-search-form">
        <input type="search" name="q" placeholder="Buscar faixas, artistas, álbuns, playlists…" autocomplete="off">
        <select name="type">
          <option value="track">Faixas</option>
          <option value="artist">Artistas</option>
          <option value="album">Álbuns</option>
          <option value="playlist">Playlists</option>
        </select>
        <button type="submit">Buscar</button>
      </form>
      <div class="explorer-results"></div>
    `;
    const form = contentEl.querySelector('.explorer-search-form');
    const results = contentEl.querySelector('.explorer-results');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = form.q.value.trim();
      const type = form.type.value;
      if (!q) return;
      results.innerHTML = '<div class="explorer-loading">Buscando…</div>';
      try {
        const data = await explorerFetch('/explorer/search', { params: { q, type, limit: 20 } });
        const items = (data[`${type}s`] && data[`${type}s`].items) || [];
        if (items.length === 0) {
          results.innerHTML = '<p class="explorer-empty">Nenhum resultado.</p>';
          return;
        }
        results.innerHTML = `<div class="explorer-grid">${items
          .map((item) =>
            itemCardHtml({
              image: (item.images && item.images[0] && item.images[0].url) || (item.album && item.album.images && item.album.images[0] && item.album.images[0].url),
              title: item.name,
              subtitle: type === 'track' ? (item.artists || []).map((a) => a.name).join(', ') : type === 'artist' ? 'Artista' : type === 'album' ? (item.artists || []).map((a) => a.name).join(', ') : `por ${(item.owner && item.owner.display_name) || ''}`,
              kind: type,
              id: item.id,
            })
          )
          .join('')}</div>`;
        bindItemCards(results);
      } catch (err) {
        results.innerHTML = '';
        setError(err);
      }
    });
  }

  // --- Tab: Lançamentos (13.7) ---

  async function renderNewReleasesTab() {
    setLoading('lançamentos');
    try {
      const data = await explorerFetch('/explorer/new-releases', { params: { limit: 20 } });
      const items = (data.albums && data.albums.items) || [];
      if (items.length === 0) {
        contentEl.innerHTML = '<p class="explorer-empty">Nenhum lançamento encontrado.</p>';
        return;
      }
      contentEl.innerHTML = `<div class="explorer-grid">${items
        .map((album) =>
          itemCardHtml({
            image: album.images && album.images[0] && album.images[0].url,
            title: album.name,
            subtitle: (album.artists || []).map((a) => a.name).join(', '),
            kind: 'album',
            id: album.id,
          })
        )
        .join('')}</div>`;
      bindItemCards(contentEl);
    } catch (err) {
      setError(err);
    }
  }

  // --- Tab: Minhas playlists (13.6) ---

  async function renderMyPlaylistsTab() {
    setLoading('suas playlists');
    try {
      const data = await explorerFetch('/explorer/me/playlists', { params: { limit: 50 } });
      const items = data.items || [];
      if (items.length === 0) {
        contentEl.innerHTML = '<p class="explorer-empty">Você ainda não tem playlists no Spotify.</p>';
        return;
      }
      contentEl.innerHTML = `<div class="explorer-grid">${items
        .map((pl) =>
          itemCardHtml({
            image: pl.images && pl.images[0] && pl.images[0].url,
            title: pl.name,
            subtitle: `${pl.tracks && pl.tracks.total ? pl.tracks.total : 0} faixas`,
            kind: 'playlist',
            id: pl.id,
          })
        )
        .join('')}</div>`;
      bindItemCards(contentEl);
    } catch (err) {
      setError(err);
    }
  }

  // --- Tab: Seguindo (13.9) ---

  async function renderFollowingTab() {
    setLoading('artistas que você segue');
    try {
      const data = await explorerFetch('/explorer/me/following', { params: { limit: 50 } });
      const items = (data.artists && data.artists.items) || [];
      if (items.length === 0) {
        contentEl.innerHTML = '<p class="explorer-empty">Você ainda não segue nenhum artista no Spotify.</p>';
        return;
      }
      contentEl.innerHTML = `<div class="explorer-grid">${items
        .map((artist) =>
          itemCardHtml({
            image: artist.images && artist.images[0] && artist.images[0].url,
            title: artist.name,
            subtitle: (artist.genres || []).slice(0, 2).join(', '),
            kind: 'artist',
            id: artist.id,
          })
        )
        .join('')}</div>`;
      bindItemCards(contentEl);
    } catch (err) {
      setError(err);
    }
  }

  // --- Tab: Meus dados (13.10) ---

  async function renderMeTab() {
    setLoading('seus dados');
    try {
      const [perfil, topTracks, topArtists, recentes] = await Promise.all([
        explorerFetch('/explorer/me'),
        explorerFetch('/explorer/me/top/tracks', { params: { limit: 10 } }),
        explorerFetch('/explorer/me/top/artists', { params: { limit: 10 } }),
        explorerFetch('/explorer/me/player/recently-played', { params: { limit: 10 } }),
      ]);

      const secao = (titulo, itens, render) => `
        <section class="explorer-me-section">
          <h3>${escapeHtml(titulo)}</h3>
          ${itens.length ? `<div class="explorer-grid explorer-grid-compact">${itens.map(render).join('')}</div>` : '<p class="explorer-empty">Nada por aqui ainda.</p>'}
        </section>
      `;

      contentEl.innerHTML = `
        <div class="explorer-me-profile">
          ${perfil.images && perfil.images[0] ? `<img src="${escapeHtml(perfil.images[0].url)}" alt="" class="explorer-me-avatar">` : ''}
          <div>
            <strong>${escapeHtml(perfil.display_name || 'Você')}</strong>
            <span>${perfil.followers ? perfil.followers.total + ' seguidores' : ''}</span>
          </div>
        </div>
        ${secao('Top faixas', topTracks.items || [], (t) =>
          itemCardHtml({
            image: t.album && t.album.images && t.album.images[0] && t.album.images[0].url,
            title: t.name,
            subtitle: (t.artists || []).map((a) => a.name).join(', '),
            kind: 'track',
            id: t.id,
          })
        )}
        ${secao('Top artistas', topArtists.items || [], (a) =>
          itemCardHtml({ image: a.images && a.images[0] && a.images[0].url, title: a.name, subtitle: 'Artista', kind: 'artist', id: a.id })
        )}
        ${secao(
          'Tocadas recentemente',
          (recentes.items || []).map((it) => it.track),
          (t) =>
            itemCardHtml({
              image: t.album && t.album.images && t.album.images[0] && t.album.images[0].url,
              title: t.name,
              subtitle: (t.artists || []).map((a) => a.name).join(', '),
              kind: 'track',
              id: t.id,
            })
        )}
      `;
      bindItemCards(contentEl);
    } catch (err) {
      setError(err);
    }
  }

  // --- Tab: Recomendações via API nativa do Spotify (13.8) ---

  function renderRecommendationsTab() {
    contentEl.innerHTML = `
      <p class="explorer-hint">Recomendações nativas do Spotify a partir de uma faixa (distintas do motor de recomendação do próprio agente). Cole o ID ou a URL de uma faixa do Spotify.</p>
      <form class="explorer-search-form">
        <input type="text" name="seed" placeholder="ID ou link da faixa (spotify:track:... ou https://open.spotify.com/track/...)" autocomplete="off">
        <button type="submit">Gerar</button>
      </form>
      <div class="explorer-results"></div>
    `;
    const form = contentEl.querySelector('.explorer-search-form');
    const results = contentEl.querySelector('.explorer-results');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const raw = form.seed.value.trim();
      const trackId = raw.split('/').pop().split('?')[0].replace('spotify:track:', '');
      if (!trackId) return;
      results.innerHTML = '<div class="explorer-loading">Gerando recomendações…</div>';
      try {
        const data = await explorerFetch('/explorer/recommendations', { params: { seed_tracks: trackId, limit: 20 } });
        const items = data.tracks || [];
        if (items.length === 0) {
          results.innerHTML = '<p class="explorer-empty">Nenhuma recomendação encontrada pra essa faixa.</p>';
          return;
        }
        results.innerHTML = `<div class="explorer-grid">${items
          .map((t) =>
            itemCardHtml({
              image: t.album && t.album.images && t.album.images[0] && t.album.images[0].url,
              title: t.name,
              subtitle: (t.artists || []).map((a) => a.name).join(', '),
              kind: 'track',
              id: t.id,
            })
          )
          .join('')}</div>`;
        bindItemCards(results);
      } catch (err) {
        results.innerHTML = '';
        setError(err);
      }
    });
  }

  // --- Tab: Player (13.11) — delega pro módulo player.js ---

  function renderPlayerTab() {
    if (window.ResIAPlayer && typeof window.ResIAPlayer.render === 'function') {
      window.ResIAPlayer.render(contentEl, { explorerFetch, escapeHtml });
    } else {
      contentEl.innerHTML = '<p class="explorer-empty">Controles de reprodução indisponíveis.</p>';
    }
  }

  function renderTab(tabId) {
    if (tabId === 'search') return renderSearchTab();
    if (tabId === 'new-releases') return renderNewReleasesTab();
    if (tabId === 'my-playlists') return renderMyPlaylistsTab();
    if (tabId === 'following') return renderFollowingTab();
    if (tabId === 'me') return renderMeTab();
    if (tabId === 'recommendations') return renderRecommendationsTab();
    if (tabId === 'player') return renderPlayerTab();
  }

  // --- Detalhes (13.2 faixa, 13.3 artista, 13.4 álbum, 13.5 playlist) ---

  async function renderDetail(kind, id) {
    setLoading('detalhes');
    try {
      if (kind === 'track') return renderTrackDetail(id);
      if (kind === 'artist') return renderArtistDetail(id);
      if (kind === 'album') return renderAlbumDetail(id);
      if (kind === 'playlist') return renderPlaylistDetail(id);
    } catch (err) {
      setError(err);
    }
  }

  function trackListHtml(tracks) {
    return `<div class="explorer-tracklist">${tracks
      .map(
        (t, i) => `
        <div class="explorer-tracklist-row">
          <span class="explorer-tracklist-index">${i + 1}</span>
          <div class="explorer-tracklist-text">
            <strong>${escapeHtml(t.name)}</strong>
            <span>${escapeHtml((t.artists || []).map((a) => a.name).join(', '))}</span>
          </div>
          <a href="https://open.spotify.com/track/${escapeHtml(t.id)}" target="_blank" rel="noopener noreferrer" title="Abrir no Spotify">↗</a>
        </div>`
      )
      .join('')}</div>`;
  }

  async function renderTrackDetail(id) {
    const [track, features] = await Promise.all([
      explorerFetch(`/explorer/track/${encodeURIComponent(id)}`),
      explorerFetch(`/explorer/track/${encodeURIComponent(id)}/audio-features`).catch(() => null),
    ]);
    const cover = track.album && track.album.images && track.album.images[0] && track.album.images[0].url;
    const featureRows = features
      ? ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness', 'tempo']
          .filter((k) => features[k] !== undefined)
          .map((k) => `<div class="explorer-feature-row"><span>${k}</span><strong>${Number(features[k]).toFixed(2)}</strong></div>`)
          .join('')
      : '<p class="explorer-empty">Audio features indisponíveis.</p>';

    contentEl.innerHTML = `
      <div class="explorer-detail-header">
        ${cover ? `<img src="${escapeHtml(cover)}" alt="">` : ''}
        <div>
          <h3>${escapeHtml(track.name)}</h3>
          <p>${escapeHtml((track.artists || []).map((a) => a.name).join(', '))} · ${escapeHtml(track.album ? track.album.name : '')}</p>
          <a href="https://open.spotify.com/track/${escapeHtml(id)}" target="_blank" rel="noopener noreferrer">Abrir no Spotify ↗</a>
        </div>
      </div>
      <section class="explorer-me-section">
        <h3>Audio features</h3>
        <div class="explorer-features-grid">${featureRows}</div>
      </section>
    `;
  }

  async function renderArtistDetail(id) {
    const [artist, topTracks, albums, related] = await Promise.all([
      explorerFetch(`/explorer/artist/${encodeURIComponent(id)}`),
      explorerFetch(`/explorer/artist/${encodeURIComponent(id)}/top-tracks`),
      explorerFetch(`/explorer/artist/${encodeURIComponent(id)}/albums`),
      explorerFetch(`/explorer/artist/${encodeURIComponent(id)}/related-artists`).catch(() => ({ artists: [] })),
    ]);
    const cover = artist.images && artist.images[0] && artist.images[0].url;

    contentEl.innerHTML = `
      <div class="explorer-detail-header">
        ${cover ? `<img src="${escapeHtml(cover)}" alt="" class="explorer-detail-cover-round">` : ''}
        <div>
          <h3>${escapeHtml(artist.name)}</h3>
          <p>${escapeHtml((artist.genres || []).slice(0, 3).join(', '))}</p>
          <a href="https://open.spotify.com/artist/${escapeHtml(id)}" target="_blank" rel="noopener noreferrer">Abrir no Spotify ↗</a>
        </div>
      </div>
      <section class="explorer-me-section">
        <h3>Top faixas</h3>
        ${trackListHtml((topTracks.tracks || []).slice(0, 10))}
      </section>
      <section class="explorer-me-section">
        <h3>Álbuns</h3>
        <div class="explorer-grid">${(albums.items || [])
          .map((al) => itemCardHtml({ image: al.images && al.images[0] && al.images[0].url, title: al.name, subtitle: al.release_date, kind: 'album', id: al.id }))
          .join('')}</div>
      </section>
      <section class="explorer-me-section">
        <h3>Artistas relacionados</h3>
        <div class="explorer-grid">${(related.artists || [])
          .slice(0, 10)
          .map((a) => itemCardHtml({ image: a.images && a.images[0] && a.images[0].url, title: a.name, subtitle: 'Artista', kind: 'artist', id: a.id }))
          .join('')}</div>
      </section>
    `;
    bindItemCards(contentEl);
  }

  async function renderAlbumDetail(id) {
    const album = await explorerFetch(`/explorer/album/${encodeURIComponent(id)}`);
    const cover = album.images && album.images[0] && album.images[0].url;
    const tracks = (album.tracks && album.tracks.items) || [];

    contentEl.innerHTML = `
      <div class="explorer-detail-header">
        ${cover ? `<img src="${escapeHtml(cover)}" alt="">` : ''}
        <div>
          <h3>${escapeHtml(album.name)}</h3>
          <p>${escapeHtml((album.artists || []).map((a) => a.name).join(', '))} · ${escapeHtml(album.release_date || '')}</p>
          <a href="https://open.spotify.com/album/${escapeHtml(id)}" target="_blank" rel="noopener noreferrer">Abrir no Spotify ↗</a>
        </div>
      </div>
      <section class="explorer-me-section">
        <h3>Faixas</h3>
        ${trackListHtml(tracks)}
      </section>
    `;
  }

  async function renderPlaylistDetail(id) {
    const playlist = await explorerFetch(`/explorer/playlist/${encodeURIComponent(id)}`);
    const cover = playlist.images && playlist.images[0] && playlist.images[0].url;
    const tracks = ((playlist.tracks && playlist.tracks.items) || []).map((it) => it.track).filter(Boolean);

    contentEl.innerHTML = `
      <div class="explorer-detail-header">
        ${cover ? `<img src="${escapeHtml(cover)}" alt="">` : ''}
        <div>
          <h3>${escapeHtml(playlist.name)}</h3>
          <p>${escapeHtml((playlist.owner && playlist.owner.display_name) || '')} · ${tracks.length} faixas</p>
          <a href="https://open.spotify.com/playlist/${escapeHtml(id)}" target="_blank" rel="noopener noreferrer">Abrir no Spotify ↗</a>
        </div>
      </div>
      <section class="explorer-me-section">
        <h3>Faixas</h3>
        ${trackListHtml(tracks)}
      </section>
    `;
  }

  function createOpenButton() {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'btn-open-explorer';
    btn.className = 'header-menu-item';
    btn.setAttribute('role', 'menuitem');
    btn.title = 'Explorar Spotify (busca, playlists, player e mais)';
    btn.setAttribute('aria-label', 'Explorar Spotify');
    btn.innerHTML = `
      <span class="header-menu-item-icon">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </span>
      <span>Explorar Spotify</span>
    `;
    btn.addEventListener('click', openPanel);
    return btn;
  }

  // Ticket 20.6 (KAN-165): botão passa a viver dentro do menu "···" de
  // ações secundárias do header em vez de solto ao lado do tema.
  function init() {
    const anchor = document.getElementById('btn-theme-toggle');
    if (anchor && anchor.parentElement && !document.getElementById('btn-open-explorer')) {
      anchor.parentElement.insertBefore(createOpenButton(), anchor);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.ResIAExplorer = { open: openPanel, close: closePanel };
})();
