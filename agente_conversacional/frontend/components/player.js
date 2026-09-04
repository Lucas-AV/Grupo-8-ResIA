/**
 * player.js — Controles de reprodução Spotify Connect (Ticket 13.11 / KAN-120)
 * Grupo 8 ResIA — renderiza dentro da aba "Player" do painel Explorar Spotify
 * (components/explorer.js), que injeta `explorerFetch`/`escapeHtml` já
 * resolvidos com o session_id atual.
 *
 * O polling de GET /explorer/me/player fica num estado compartilhado
 * (window.ResIASpotifyPlayerState) pra não duplicar a chamada quando o
 * widget "Tocando agora" (Ticket 20.7 / KAN-166, components/nowPlaying.js)
 * também está inscrito ao mesmo tempo — só um intervalo de polling roda por
 * vez, não importa quantos consumidores estejam montados.
 */

(function () {
  // --- Estado compartilhado de polling (GET /explorer/me/player) ---

  const POLL_INTERVAL_MS = 5000;
  let pollTimer = null;
  const subscribers = new Set();
  let sharedFetch = null;
  let lastSnapshot = { state: null, error: null };

  async function poll() {
    try {
      const state = await sharedFetch('/explorer/me/player');
      lastSnapshot = { state: state && state.item ? state : null, error: null };
    } catch (err) {
      lastSnapshot = { state: null, error: err };
    }
    subscribers.forEach((cb) => cb(lastSnapshot));
  }

  /**
   * `explorerFetch` do primeiro inscrito vira a função usada pro polling
   * enquanto houver ao menos um inscrito — todos os consumidores atuais
   * (painel Player e widget "Tocando agora") resolvem pro mesmo backend com
   * o mesmo session_id, então não faz diferença qual instância é usada.
   */
  function subscribe(explorerFetch, cb) {
    if (!sharedFetch) sharedFetch = explorerFetch;
    subscribers.add(cb);
    if (subscribers.size === 1) {
      poll();
      pollTimer = setInterval(poll, POLL_INTERVAL_MS);
    } else {
      cb(lastSnapshot);
    }
    return function unsubscribe() {
      subscribers.delete(cb);
      if (subscribers.size === 0) {
        clearInterval(pollTimer);
        pollTimer = null;
        sharedFetch = null;
        lastSnapshot = { state: null, error: null };
      }
    };
  }

  window.ResIASpotifyPlayerState = { subscribe, refresh: poll };

  // --- Painel completo (aba "Player" do Explorar Spotify) ---

  function fmtMs(ms) {
    if (!ms && ms !== 0) return '--:--';
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
  }

  let panelUnsubscribe = null;

  async function render(container, { explorerFetch, escapeHtml }) {
    container.innerHTML = `
      <div class="explorer-player">
        <div class="explorer-player-now"></div>
        <div class="explorer-player-controls">
          <button type="button" data-action="shuffle" title="Aleatório">🔀</button>
          <button type="button" data-action="previous" title="Anterior">⏮</button>
          <button type="button" data-action="toggle-play" title="Tocar/Pausar">⏯</button>
          <button type="button" data-action="next" title="Próxima">⏭</button>
          <button type="button" data-action="repeat" title="Repetir">🔁</button>
        </div>
        <div class="explorer-player-seek">
          <span class="explorer-player-time-current">--:--</span>
          <input type="range" min="0" max="100" value="0" class="explorer-player-seek-input">
          <span class="explorer-player-time-total">--:--</span>
        </div>
        <div class="explorer-player-volume">
          <span>🔊</span>
          <input type="range" min="0" max="100" value="50" class="explorer-player-volume-input">
        </div>
        <p class="explorer-hint">Requer Spotify Premium com um dispositivo ativo (ex.: o app do Spotify aberto em algum lugar).</p>
      </div>
    `;

    const nowEl = container.querySelector('.explorer-player-now');
    const seekInput = container.querySelector('.explorer-player-seek-input');
    const timeCurrentEl = container.querySelector('.explorer-player-time-current');
    const timeTotalEl = container.querySelector('.explorer-player-time-total');
    const volumeInput = container.querySelector('.explorer-player-volume-input');

    let lastState = null;
    let seeking = false;

    function applySnapshot({ state, error }) {
      lastState = state;
      if (error) {
        nowEl.innerHTML = `<p class="explorer-empty">⚠️ ${escapeHtml(error.message || 'Não foi possível ler o estado do player.')}</p>`;
        return;
      }
      if (!state) {
        nowEl.innerHTML = '<p class="explorer-empty">Nenhum dispositivo Spotify ativo no momento.</p>';
        return;
      }
      const track = state.item;
      const cover = track.album && track.album.images && track.album.images[0] && track.album.images[0].url;
      nowEl.innerHTML = `
        ${cover ? `<img src="${escapeHtml(cover)}" alt="">` : ''}
        <div>
          <strong>${escapeHtml(track.name)}</strong>
          <span>${escapeHtml((track.artists || []).map((a) => a.name).join(', '))}</span>
        </div>
      `;
      if (!seeking) {
        seekInput.max = track.duration_ms || 0;
        seekInput.value = state.progress_ms || 0;
      }
      timeCurrentEl.textContent = fmtMs(state.progress_ms);
      timeTotalEl.textContent = fmtMs(track.duration_ms);
      volumeInput.value = (state.device && state.device.volume_percent) || 50;
      container.querySelector('[data-action="toggle-play"]').textContent = state.is_playing ? '⏸' : '▶';
    }

    container.querySelector('[data-action="toggle-play"]').addEventListener('click', async () => {
      const playing = lastState && lastState.is_playing;
      await explorerFetch(playing ? '/explorer/me/player/pause' : '/explorer/me/player/play', { method: 'POST' });
      setTimeout(() => window.ResIASpotifyPlayerState.refresh(), 400);
    });
    container.querySelector('[data-action="next"]').addEventListener('click', async () => {
      await explorerFetch('/explorer/me/player/next', { method: 'POST' });
      setTimeout(() => window.ResIASpotifyPlayerState.refresh(), 400);
    });
    container.querySelector('[data-action="previous"]').addEventListener('click', async () => {
      await explorerFetch('/explorer/me/player/previous', { method: 'POST' });
      setTimeout(() => window.ResIASpotifyPlayerState.refresh(), 400);
    });
    container.querySelector('[data-action="shuffle"]').addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      const novoEstado = !btn.classList.contains('active');
      await explorerFetch('/explorer/me/player/shuffle', { method: 'POST', params: { state: novoEstado } });
      btn.classList.toggle('active', novoEstado);
    });
    container.querySelector('[data-action="repeat"]').addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      const estados = ['off', 'context', 'track'];
      const atual = btn.dataset.state || 'off';
      const proximo = estados[(estados.indexOf(atual) + 1) % estados.length];
      btn.dataset.state = proximo;
      btn.classList.toggle('active', proximo !== 'off');
      await explorerFetch('/explorer/me/player/repeat', { method: 'POST', params: { state: proximo } });
    });

    seekInput.addEventListener('mousedown', () => (seeking = true));
    seekInput.addEventListener('touchstart', () => (seeking = true));
    seekInput.addEventListener('change', async () => {
      await explorerFetch('/explorer/me/player/seek', { method: 'POST', params: { position_ms: Math.round(Number(seekInput.value)) } });
      seeking = false;
      setTimeout(() => window.ResIASpotifyPlayerState.refresh(), 400);
    });

    let volumeDebounce = null;
    volumeInput.addEventListener('input', () => {
      clearTimeout(volumeDebounce);
      volumeDebounce = setTimeout(async () => {
        await explorerFetch('/explorer/me/player/volume', { method: 'POST', params: { volume_percent: Math.round(Number(volumeInput.value)) } });
      }, 300);
    });

    if (panelUnsubscribe) panelUnsubscribe();
    panelUnsubscribe = window.ResIASpotifyPlayerState.subscribe(explorerFetch, applySnapshot);
  }

  window.ResIAPlayer = { render };
})();
