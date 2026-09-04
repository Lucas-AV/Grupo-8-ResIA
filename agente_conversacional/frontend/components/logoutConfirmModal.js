/**
 * logoutConfirmModal.js — Dialog de confirmação antes de desconectar do
 * Spotify (Ticket 20.11 / KAN-170).
 *
 * Hoje clicar em "Conectar Spotify" enquanto autenticado chama
 * handleLogoutSpotify() direto (app.js), sem confirmação — um clique sem
 * querer desconecta na hora. Este componente só intercepta esse clique com
 * um dialog de sim/não; o fluxo de logout em si (POST /auth/logout,
 * 4.5/KAN-40) continua em app.js, inalterado.
 *
 * Autocontido, mesmo padrão de qrLogin.js/playlistSaveModal.js — overlay
 * criado sob demanda e injetado em document.body, reaproveitando as classes
 * .explorer-overlay/.explorer-header/.explorer-close já usadas pelos outros
 * modais do produto.
 */

(function () {
  let overlayEl = null;
  let onConfirm = null;

  function ensureModal() {
    if (overlayEl) return;

    const overlay = document.createElement('div');
    overlay.id = 'logout-confirm-overlay';
    overlay.className = 'explorer-overlay';
    overlay.hidden = true;
    overlay.innerHTML = `
      <div class="playlist-save-panel confirm-dialog-panel" role="dialog" aria-label="Desconectar do Spotify">
        <header class="explorer-header">
          <h2>Desconectar do Spotify?</h2>
          <button type="button" class="explorer-close" title="Fechar" aria-label="Fechar">✕</button>
        </header>
        <div class="playlist-save-body">
          <p>Você vai precisar fazer login de novo para salvar playlists, ver recomendações personalizadas e usar o Explorar Spotify.</p>
        </div>
        <footer class="playlist-save-footer">
          <div class="playlist-save-actions">
            <button type="button" class="btn-response-action playlist-save-cancel">Cancelar</button>
            <button type="button" class="btn-response-action btn-logout-confirm">Desconectar</button>
          </div>
        </footer>
      </div>
    `;
    document.body.appendChild(overlay);

    overlayEl = overlay;
    overlay.querySelector('.explorer-close').addEventListener('click', close);
    overlay.querySelector('.playlist-save-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !overlay.hidden) close();
    });
    overlay.querySelector('.btn-logout-confirm').addEventListener('click', () => {
      const confirmar = onConfirm;
      close();
      if (typeof confirmar === 'function') confirmar();
    });
  }

  function close() {
    if (overlayEl) overlayEl.hidden = true;
    onConfirm = null;
  }

  /** Abre o dialog; `callback` só roda se o usuário confirmar. */
  function open(callback) {
    ensureModal();
    onConfirm = callback;
    overlayEl.hidden = false;
  }

  window.ResIALogoutConfirmModal = { open, close };
})();
