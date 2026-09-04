/**
 * playlistSaveModal.js — Modal de confirmação do "Salvar no Spotify" (Ticket 12.6)
 * Grupo 8 ResIA — mostra as faixas que serão salvas e uma sugestão de
 * título/descrição gerada pelo LLM (GET /playlist/sugerir), editável antes
 * de confirmar. A criação de verdade (POST /playlist/criar) só acontece se
 * o usuário clicar "Salvar" aqui dentro — reaproveita
 * window.ResIA.criarPlaylistSpotify (app.js).
 *
 * Autocontido, mesmo padrão de trackCard.js/explorer.js — overlay/painel
 * criados sob demanda e injetados em document.body.
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

  let overlayEl = null;
  let tituloInput = null;
  let descricaoInput = null;
  let tracksCountEl = null;
  let tracksListEl = null;
  let errorEl = null;
  let confirmBtn = null;
  let faixasAtuais = [];

  // Miniatura de capa do álbum (mesmo endpoint/estratégia de trackCard.js):
  // GET /spotify/thumbnail/{track_id}, sem exigir login. Cache local à este
  // arquivo — cada componente mantém o próprio Map, sem estado compartilhado.
  const _thumbnailCache = new Map(); // track_id -> url | null

  async function _carregarThumbnail(trackId) {
    if (_thumbnailCache.has(trackId)) return _thumbnailCache.get(trackId);

    try {
      const response = await fetch(`${API_BASE_URL}/spotify/thumbnail/${encodeURIComponent(trackId)}`);
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

  function ensureModal() {
    if (overlayEl) return;

    const overlay = document.createElement('div');
    overlay.id = 'playlist-save-overlay';
    overlay.className = 'explorer-overlay';
    overlay.hidden = true;
    overlay.innerHTML = `
      <div class="playlist-save-panel" role="dialog" aria-label="Salvar playlist no Spotify">
        <header class="explorer-header">
          <h2>Salvar no Spotify</h2>
          <button type="button" class="explorer-close" title="Fechar" aria-label="Fechar">✕</button>
        </header>
        <div class="playlist-save-body">
          <label class="playlist-save-label" for="playlist-save-titulo">Título</label>
          <input type="text" id="playlist-save-titulo" class="playlist-save-input" maxlength="100">

          <label class="playlist-save-label" for="playlist-save-descricao">Descrição</label>
          <textarea id="playlist-save-descricao" class="playlist-save-textarea" maxlength="300" rows="3"></textarea>

          <div class="playlist-save-tracks-header"></div>
          <ul class="playlist-save-tracks-list"></ul>
        </div>
        <footer class="playlist-save-footer">
          <span class="playlist-save-error" hidden></span>
          <div class="playlist-save-actions">
            <button type="button" class="btn-response-action playlist-save-cancel">Cancelar</button>
            <button type="button" class="btn-response-action btn-salvar-spotify playlist-save-confirm">Salvar no Spotify</button>
          </div>
        </footer>
      </div>
    `;
    document.body.appendChild(overlay);

    overlayEl = overlay;
    tituloInput = overlay.querySelector('#playlist-save-titulo');
    descricaoInput = overlay.querySelector('#playlist-save-descricao');
    tracksCountEl = overlay.querySelector('.playlist-save-tracks-header');
    tracksListEl = overlay.querySelector('.playlist-save-tracks-list');
    errorEl = overlay.querySelector('.playlist-save-error');
    confirmBtn = overlay.querySelector('.playlist-save-confirm');

    overlay.querySelector('.explorer-close').addEventListener('click', close);
    overlay.querySelector('.playlist-save-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !overlay.hidden) close();
    });
    confirmBtn.addEventListener('click', handleConfirm);
  }

  function close() {
    if (overlayEl) overlayEl.hidden = true;
  }

  function renderTrackList(faixas) {
    const n = faixas.length;
    tracksCountEl.textContent = `${n} faixa${n === 1 ? '' : 's'} nesta playlist`;
    tracksListEl.innerHTML = faixas
      .map(
        (faixa) => `
          <li data-track-id="${escapeHtml((faixa && faixa.track_id) || '')}">
            <img class="playlist-save-track-thumb" alt="" loading="lazy">
            <span class="playlist-save-track-name">${escapeHtml((faixa && faixa.nome) || 'Faixa sem título')}</span>
            <span class="playlist-save-track-artist">${escapeHtml((faixa && faixa.artista) || '')}</span>
          </li>
        `
      )
      .join('');

    // Miniaturas de capa carregadas à parte — não bloqueiam a renderização
    // da lista, ver _carregarThumbnail.
    faixas.forEach((faixa) => {
      const trackId = faixa && faixa.track_id;
      if (!trackId) return;
      const li = tracksListEl.querySelector(`li[data-track-id="${CSS.escape(trackId)}"]`);
      const img = li && li.querySelector('.playlist-save-track-thumb');
      if (!img) return;
      _carregarThumbnail(trackId).then((url) => {
        if (!url) return;
        img.src = url;
      });
    });
  }

  async function buscarSugestao(faixas) {
    try {
      const response = await fetch(`${API_BASE_URL}/playlist/sugerir`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ faixas }),
      });
      if (!response.ok) return null;
      return await response.json();
    } catch (err) {
      console.warn('Falha ao buscar sugestão de título/descrição da playlist:', err);
      return null;
    }
  }

  /**
   * Abre o modal com as `faixas` (msg.faixas do card de resposta) e dispara
   * a busca da sugestão de título/descrição em paralelo — a lista de
   * faixas já aparece na hora, os campos de texto ficam num estado de
   * carregamento até a sugestão chegar (ou falhar, caindo pro padrão do
   * backend).
   */
  async function open(faixas) {
    ensureModal();
    faixasAtuais = Array.isArray(faixas) ? faixas : [];
    if (faixasAtuais.length === 0) return;

    tituloInput.value = '';
    tituloInput.placeholder = 'Gerando sugestão...';
    tituloInput.disabled = true;
    descricaoInput.value = '';
    descricaoInput.placeholder = 'Gerando sugestão...';
    descricaoInput.disabled = true;
    errorEl.hidden = true;
    confirmBtn.disabled = false;
    confirmBtn.textContent = 'Salvar no Spotify';
    renderTrackList(faixasAtuais);

    overlayEl.hidden = false;
    tituloInput.focus();

    const sugestao = await buscarSugestao(faixasAtuais);
    tituloInput.value = (sugestao && sugestao.titulo) || 'Recomendações ResIA';
    descricaoInput.value = (sugestao && sugestao.descricao) || 'Playlist gerada pelo agente conversacional do Grupo 8 ResIA.';
    tituloInput.disabled = false;
    descricaoInput.disabled = false;
  }

  async function handleConfirm() {
    if (confirmBtn.disabled) return;

    const trackIds = faixasAtuais.map((faixa) => faixa && faixa.track_id).filter(Boolean);
    if (trackIds.length === 0) {
      errorEl.textContent = 'Nenhuma faixa válida pra salvar.';
      errorEl.hidden = false;
      return;
    }

    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Salvando...';
    errorEl.hidden = true;

    try {
      const resultado = await window.ResIA.criarPlaylistSpotify(trackIds, {
        nome: tituloInput.value.trim() || undefined,
        descricao: descricaoInput.value.trim() || undefined,
      });
      if (typeof window.showToast === 'function') window.showToast('Playlist salva no seu Spotify!');
      if (resultado && resultado.url) {
        window.open(resultado.url, '_blank', 'noopener,noreferrer');
      }
      close();
    } catch (err) {
      errorEl.textContent = err.message || 'Não foi possível salvar a playlist no Spotify.';
      errorEl.hidden = false;
      confirmBtn.disabled = false;
      confirmBtn.textContent = 'Salvar no Spotify';
    }
  }

  window.ResIAPlaylistModal = { open, close };
})();
