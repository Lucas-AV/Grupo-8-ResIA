/**
 * player.js — Controles de reprodução Spotify Connect (Ticket 13.11 / KAN-120)
 * Grupo 8 ResIA — renderiza dentro da aba "Player" do painel Explorar Spotify
 * (components/explorer.js), que injeta `explorerFetch`/`escapeHtml` já
 * resolvidos com o session_id atual.
 */

(function () {
  let pollTimer = null;

  function fmtMs(ms) {
    if (!ms && ms !== 0) return '--:--';
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
  }

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

    async function refresh() {
      try {
        const state = await explorerFetch('/explorer/me/player');
        lastState = state && state.item ? state : null;
        if (!lastState) {
          nowEl.innerHTML = '<p class="explorer-empty">Nenhum dispositivo Spotify ativo no momento.</p>';
          return;
        }
        const track = lastState.item;
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
          seekInput.value = lastState.progress_ms || 0;
        }
        timeCurrentEl.textContent = fmtMs(lastState.progress_ms);
        timeTotalEl.textContent = fmtMs(track.duration_ms);
        volumeInput.value = (lastState.device && lastState.device.volume_percent) || 50;
        container.querySelector('[data-action="toggle-play"]').textContent = lastState.is_playing ? '⏸' : '▶';
      } catch (err) {
        nowEl.innerHTML = `<p class="explorer-empty">⚠️ ${escapeHtml(err.message || 'Não foi possível ler o estado do player.')}</p>`;
      }
    }

    container.querySelector('[data-action="toggle-play"]').addEventListener('click', async () => {
      const playing = lastState && lastState.is_playing;
      await explorerFetch(playing ? '/explorer/me/player/pause' : '/explorer/me/player/play', { method: 'POST' });
      setTimeout(refresh, 400);
    });
    container.querySelector('[data-action="next"]').addEventListener('click', async () => {
      await explorerFetch('/explorer/me/player/next', { method: 'POST' });
      setTimeout(refresh, 400);
    });
    container.querySelector('[data-action="previous"]').addEventListener('click', async () => {
      await explorerFetch('/explorer/me/player/previous', { method: 'POST' });
      setTimeout(refresh, 400);
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
      setTimeout(refresh, 400);
    });

    let volumeDebounce = null;
    volumeInput.addEventListener('input', () => {
      clearTimeout(volumeDebounce);
      volumeDebounce = setTimeout(async () => {
        await explorerFetch('/explorer/me/player/volume', { method: 'POST', params: { volume_percent: Math.round(Number(volumeInput.value)) } });
      }, 300);
    });

    clearInterval(pollTimer);
    await refresh();
    pollTimer = setInterval(refresh, 5000);
  }

  window.ResIAPlayer = { render };
})();
