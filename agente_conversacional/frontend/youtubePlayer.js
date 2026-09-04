/**
 * youtubePlayer.js — Widget de vídeo do YouTube (fallback de prévia, Ticket 13.12 / KAN-121)
 * Grupo 8 ResIA — Agente Conversacional de Recomendação Musical
 *
 * Usado por trackCard.js quando a Spotify não devolve preview_url pra uma
 * faixa (comum pra apps criados após nov/2024, ver
 * docs/superpowers/specs/2026-09-03-spotify-preview-player-design.md).
 * Controlador de baixo nível só: quem decide QUANDO usar o YouTube (vs a
 * prévia nativa da Spotify) e mantém o estado de qual faixa está tocando é
 * trackCard.js — aqui só carregamos/tocamos/pausamos um vídeo e
 * mostramos/escondemos o widget.
 *
 * O vídeo fica VISÍVEL enquanto toca — as políticas de API Services do
 * YouTube proíbem player "só-áudio" (tocar o áudio escondendo o vídeo
 * correspondente), por isso não usamos um iframe invisível.
 */

(function () {
  let ytPlayer = null;
  let ytApiReadyPromise = null;
  let onExternalPauseCallback = null;

  function carregarApiYouTube() {
    if (ytApiReadyPromise) return ytApiReadyPromise;

    ytApiReadyPromise = new Promise((resolve) => {
      if (window.YT && window.YT.Player) {
        resolve();
        return;
      }
      const anterior = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (typeof anterior === 'function') anterior();
        resolve();
      };
      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(script);
    });

    return ytApiReadyPromise;
  }

  function obterWrapperElement() {
    let wrapper = document.getElementById('youtube-preview-widget');
    if (!wrapper) {
      wrapper = document.createElement('div');
      wrapper.id = 'youtube-preview-widget';
      wrapper.style.cssText =
        'position:fixed;bottom:100px;right:20px;width:240px;height:135px;border-radius:10px;' +
        'overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,0.4);z-index:60;background:#000;' +
        'opacity:0;transform:translateY(8px);pointer-events:none;transition:opacity 0.2s ease,transform 0.2s ease;';
      document.body.appendChild(wrapper);
    }
    return wrapper;
  }

  function mostrarWidget() {
    const wrapper = document.getElementById('youtube-preview-widget');
    if (!wrapper) return;
    wrapper.style.opacity = '1';
    wrapper.style.transform = 'translateY(0)';
    wrapper.style.pointerEvents = 'auto';
  }

  function esconderWidget() {
    const wrapper = document.getElementById('youtube-preview-widget');
    if (!wrapper) return;
    wrapper.style.opacity = '0';
    wrapper.style.transform = 'translateY(8px)';
    wrapper.style.pointerEvents = 'none';
  }

  async function obterPlayer() {
    if (ytPlayer) return ytPlayer;
    await carregarApiYouTube();
    const wrapper = obterWrapperElement();
    const host = document.createElement('div');
    wrapper.appendChild(host);

    return new Promise((resolve) => {
      ytPlayer = new window.YT.Player(host, {
        height: '135',
        width: '240',
        playerVars: { playsinline: 1 },
        events: {
          onReady: () => resolve(ytPlayer),
          onStateChange: (event) => {
            const ENDED = window.YT.PlayerState.ENDED;
            const PAUSED = window.YT.PlayerState.PAUSED;
            // Cobre tanto o botão do card quanto os controles nativos do
            // próprio player do YouTube (o widget é visível e clicável).
            if (event.data === ENDED || event.data === PAUSED) {
              esconderWidget();
              if (typeof onExternalPauseCallback === 'function') onExternalPauseCallback();
            }
          },
        },
      });
    });
  }

  async function play(videoId) {
    const player = await obterPlayer();
    player.loadVideoById(videoId);
    player.playVideo();
    mostrarWidget();
  }

  function pause() {
    if (ytPlayer) ytPlayer.pauseVideo();
    esconderWidget();
  }

  /** Chamado quando o vídeo pausa/termina por conta própria (controles
   * nativos do player, fim do vídeo) — não quando trackCard.js chama pause() */
  function onExternalPause(fn) {
    onExternalPauseCallback = fn;
  }

  window.ResIAYoutubeWidget = { play, pause, onExternalPause };
})();
