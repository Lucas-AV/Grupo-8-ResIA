/**
 * qrLogin.js — Login via QR code / pareamento de dispositivo móvel (Ticket 13.13 / KAN-122)
 * Grupo 8 ResIA — porta pro produto real o fluxo de pareamento por QR do
 * spotify_explorer (spotify_explorer/qr_page.py + pairing_store.py), como
 * alternativa ao login por redirect já existente (botão "Conectar Spotify").
 *
 * ATENÇÃO (ver KAN-122): o código de pareamento aqui não tem vínculo com o
 * dispositivo que gerou o QR — qualquer um de posse do código dentro da
 * janela de 5 min pode completar o pareamento. Aceitável só enquanto o QR
 * fica visível apenas pra quem está fisicamente perto da tela; não expor
 * esse código por nenhum outro canal.
 */

(function () {
  const API_BASE_URL =
    window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
      ? ''
      : 'http://127.0.0.1:8000';

  let modalEl = null;
  let pollTimer = null;

  function sessionId() {
    return window.ResIA && typeof window.ResIA.getSessionId === 'function' ? window.ResIA.getSessionId() : null;
  }

  function ensureModal() {
    if (modalEl) return;
    const overlay = document.createElement('div');
    overlay.id = 'qr-login-overlay';
    overlay.className = 'explorer-overlay';
    overlay.hidden = true;
    overlay.innerHTML = `
      <div class="qr-login-panel" role="dialog" aria-label="Conectar com Spotify por QR code">
        <header class="explorer-header">
          <h2>Conectar por QR code</h2>
          <button type="button" class="explorer-close" title="Fechar" aria-label="Fechar">✕</button>
        </header>
        <div class="qr-login-body">
          <p>Escaneie com a câmera do seu celular e faça login com a sua conta Spotify por lá.</p>
          <div class="qr-login-image"></div>
          <p class="qr-login-status">Gerando QR code…</p>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    overlay.querySelector('.explorer-close').addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal();
    });
    modalEl = overlay;
  }

  function closeModal() {
    if (modalEl) modalEl.hidden = true;
    clearTimeout(pollTimer);
  }

  async function poll(code) {
    try {
      const sid = sessionId();
      const response = await fetch(
        `${API_BASE_URL}/auth/pair/${encodeURIComponent(code)}/status?session_id=${encodeURIComponent(sid)}`
      );
      const data = await response.json();
      const statusEl = modalEl.querySelector('.qr-login-status');

      if (data.status === 'completed') {
        statusEl.textContent = 'Conectado! Fechando…';
        window.showToast && window.showToast('Spotify conectado via QR code!');
        setTimeout(() => {
          closeModal();
          window.location.reload();
        }, 800);
        return;
      }
      if (data.status === 'not_found') {
        statusEl.textContent = 'QR code expirou. Gere um novo.';
        return;
      }
      statusEl.textContent = 'Aguardando alguém escanear…';
      pollTimer = setTimeout(() => poll(code), 2000);
    } catch (err) {
      modalEl.querySelector('.qr-login-status').textContent = 'Falha ao verificar o pareamento.';
    }
  }

  async function openModal() {
    ensureModal();
    modalEl.hidden = false;
    const imageEl = modalEl.querySelector('.qr-login-image');
    const statusEl = modalEl.querySelector('.qr-login-status');
    imageEl.innerHTML = '';
    statusEl.textContent = 'Gerando QR code…';

    try {
      const sid = sessionId();
      const response = await fetch(`${API_BASE_URL}/auth/qr?session_id=${encodeURIComponent(sid)}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      imageEl.innerHTML = `<img src="${data.qr_svg_data_uri}" alt="QR code para login com Spotify" width="220" height="220">`;
      statusEl.textContent = 'Aguardando alguém escanear…';
      pollTimer = setTimeout(() => poll(data.code), 2000);
    } catch (err) {
      statusEl.textContent = 'Não foi possível gerar o QR code agora.';
    }
  }

  function createTriggerLink() {
    const link = document.createElement('button');
    link.type = 'button';
    link.id = 'btn-qr-login';
    link.className = 'btn-icon-secondary';
    link.title = 'Conectar com Spotify escaneando um QR code';
    link.setAttribute('aria-label', 'Conectar com Spotify por QR code');
    link.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7"></rect>
        <rect x="14" y="3" width="7" height="7"></rect>
        <rect x="3" y="14" width="7" height="7"></rect>
        <line x1="14" y1="14" x2="14" y2="21"></line>
        <line x1="21" y1="14" x2="21" y2="21"></line>
        <line x1="17.5" y1="17.5" x2="17.5" y2="17.5"></line>
      </svg>
    `;
    link.addEventListener('click', openModal);
    return link;
  }

  function init() {
    const authBtn = document.getElementById('btn-spotify-auth');
    if (authBtn && authBtn.parentElement && !document.getElementById('btn-qr-login')) {
      authBtn.insertAdjacentElement('afterend', createTriggerLink());
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.ResIAQrLogin = { open: openModal, close: closeModal };
})();
