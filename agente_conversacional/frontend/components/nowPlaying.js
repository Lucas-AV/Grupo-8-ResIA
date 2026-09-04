/**
 * nowPlaying.js — Widget "Tocando agora" persistente na tela principal
 * (Ticket 20.7 / KAN-166) Grupo 8 ResIA.
 *
 * Fica escondido (fora do DOM até o primeiro uso, depois com `hidden`) até
 * confirmar sessão Spotify conectada via `resia:spotify-auth-changed`
 * (disparado por app.js sempre que `isSpotifyAuthenticated` muda) — nunca
 * aparece pra usuário anônimo, nem vazio. Reaproveita o polling
 * compartilhado de GET /explorer/me/player já usado pelo painel Explorar
 * Spotify (window.ResIASpotifyPlayerState, ver components/player.js) em vez
 * de duplicar essa lógica. Clicar no widget abre o painel na aba Player.
 */

(function () {
  const API_BASE_URL =
    window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
      ? ''
      : 'http://127.0.0.1:8000';

  function sessionId() {
    return window.ResIA && typeof window.ResIA.getSessionId === 'function' ? window.ResIA.getSessionId() : null;
  }

  async function explorerFetch(path, { method = 'GET', params = {} } = {}) {
    const sid = sessionId();
    const query = new URLSearchParams({ session_id: sid, ...params });
    const response = await fetch(`${API_BASE_URL}${path}?${query.toString()}`, { method });
    let body = null;
    try {
      body = await response.json();
    } catch (e) {
      body = null;
    }
    if (!response.ok) {
      const detail = body && body.detail ? body.detail : {};
      throw new Error(detail.mensagem || `Falha ao consultar o Spotify (HTTP ${response.status})`);
    }
    return body;
  }

  let widgetEl = null;
  let unsubscribe = null;

  function ensureWidget() {
    if (widgetEl) return widgetEl;
    const root = document.getElementById('now-playing-widget-root');
    if (!root) return null;

    widgetEl = document.createElement('button');
    widgetEl.type = 'button';
    widgetEl.id = 'now-playing-widget';
    widgetEl.className = 'now-playing-widget';
    widgetEl.hidden = true;
    widgetEl.title = 'Abrir controles do Spotify';
    widgetEl.setAttribute('aria-label', 'Tocando agora no Spotify — abrir controles');
    widgetEl.innerHTML = `
      <img class="now-playing-cover" alt="">
      <span class="now-playing-info">
        <span class="now-playing-track"></span>
        <span class="now-playing-artist"></span>
      </span>
      <span class="now-playing-eq" aria-hidden="true"><span></span><span></span><span></span></span>
    `;
    widgetEl.addEventListener('click', () => {
      if (window.ResIAExplorer && typeof window.ResIAExplorer.open === 'function') {
        window.ResIAExplorer.open('player');
      }
    });
    root.appendChild(widgetEl);
    return widgetEl;
  }

  function hideWidget() {
    const widget = ensureWidget();
    if (widget) widget.hidden = true;
  }

  function applySnapshot({ state, error }) {
    const widget = ensureWidget();
    if (!widget) return;

    // Nada tocando, nenhum dispositivo ativo, ou erro pontual de rede —
    // o widget só existe enquanto há algo pra mostrar (critério de aceite).
    if (error || !state || !state.item || !state.device) {
      widget.hidden = true;
      return;
    }

    const track = state.item;
    const images = (track.album && track.album.images) || [];
    const cover = images[images.length - 1] || images[0];

    const coverEl = widget.querySelector('.now-playing-cover');
    coverEl.src = (cover && cover.url) || '';
    coverEl.hidden = !cover;
    widget.querySelector('.now-playing-track').textContent = track.name || '';
    widget.querySelector('.now-playing-artist').textContent = (track.artists || []).map((a) => a.name).join(', ');
    widget.classList.toggle('is-paused', !state.is_playing);
    widget.hidden = false;
  }

  function start() {
    if (unsubscribe || !window.ResIASpotifyPlayerState) return;
    unsubscribe = window.ResIASpotifyPlayerState.subscribe(explorerFetch, applySnapshot);
  }

  function stop() {
    if (unsubscribe) {
      unsubscribe();
      unsubscribe = null;
    }
    hideWidget();
  }

  window.addEventListener('resia:spotify-auth-changed', (e) => {
    if (e.detail && e.detail.authenticated) {
      start();
    } else {
      stop();
    }
  });
})();
