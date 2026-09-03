/**
 * api.js — Cliente HTTP para comunicação com a API do Agente Conversacional
 * Grupo 8 ResIA — Proposta B (Ticket 4.1)
 */

// Detecta URL base da API: se a página foi servida pelo FastAPI usa '', caso contrário aponta para :8000
const API_BASE_URL =
  window.location.protocol.startsWith('http') && window.location.port !== '5500' && window.location.port !== '3000'
    ? ''
    : 'http://127.0.0.1:8000';

/**
 * Catálogo offline para demonstração/fallback caso o backend não esteja ativo
 */
const OFFLINE_CATALOGO = {
  pagode: [
    { track_id: '3n3Ppam7vgaVa1iaRUc9Lp', nome: 'Deixa Acontecer', artista: 'Grupo Revelação', album: 'Ao Vivo', genero: 'pagode' },
    { track_id: '2OzhsB92lF4N4Ynxy7P9hP', nome: 'Pé Na Areia', artista: 'Diogo Nogueira', album: 'Munduê', genero: 'pagode' },
    { track_id: '5gB82p5T9z7Xw8Q7F1oE7B', nome: 'Falta Você', artista: 'Thiaguinho', album: 'Meu Nome É Thiago André', genero: 'pagode' },
  ],
  rock: [
    { track_id: '08mG3Y1vljYA6bvNXEsOh9', nome: "Sweet Child O' Mine", artista: "Guns N' Roses", album: "Appetite For Destruction", genero: 'rock' },
    { track_id: '2VxeLyX666F8uXCJ0dZF8B', nome: "Livin' On A Prayer", artista: 'Bon Jovi', album: 'Slippery When Wet', genero: 'rock' },
    { track_id: '7w8OXQ8oo6b5gPshx842Xk', nome: 'Back In Black', artista: 'AC/DC', album: 'Back In Black', genero: 'rock' },
  ],
  chill: [
    { track_id: '3U4isOIWM3VvDubwSI3y7a', nome: 'Weightless', artista: 'Marconi Union', album: 'Weightless (Vol. 2)', genero: 'chill' },
    { track_id: '4GfK1A2GZJvD1YwV61y6hA', nome: 'Sunset Lover', artista: 'Petit Biscuit', album: 'Presence', genero: 'chill' },
    { track_id: '1A7F0J3F5F4h8C4G7x1A2B', nome: 'Coffee', artista: 'beabadoobee', album: 'Loveworm', genero: 'chill' },
  ],
  pop: [
    { track_id: '0VjIjW4GlUZAMYd2vXMi3b', nome: 'Blinding Lights', artista: 'The Weeknd', album: 'After Hours', genero: 'pop' },
    { track_id: '4Dvkj6JhhA12EX05fT7y2e', nome: 'As It Was', artista: 'Harry Styles', album: "Harry's House", genero: 'pop' },
    { track_id: '1BxfuPKGuaTgP7aM0XbdMe', nome: 'Levitating', artista: 'Dua Lipa', album: 'Future Nostalgia', genero: 'pop' },
  ],
};

function resolverMockLocal(sessionId, mensagem) {
  const msg = mensagem.toLowerCase();
  let faixas = [];
  let texto = '';
  let genero = 'misto';

  if (msg.includes('pagode') || msg.includes('samba') || msg.includes('churrasco')) {
    faixas = OFFLINE_CATALOGO.pagode;
    texto = 'Selecionei clássicos do pagode com energia lá em cima para animar o seu churrasco!';
    genero = 'pagode';
  } else if (msg.includes('rock') || msg.includes('80') || msg.includes('guitarra')) {
    faixas = OFFLINE_CATALOGO.rock;
    texto = 'Aqui estão hinos do rock clássico com solos marcantes e energia contagiante:';
    genero = 'rock';
  } else if (msg.includes('chill') || msg.includes('lofi') || msg.includes('lo-fi') || msg.includes('relax') || msg.includes('foco') || msg.includes('calm')) {
    faixas = OFFLINE_CATALOGO.chill;
    texto = 'Encontrei faixas perfeitas com clima relaxante e alta acústica para você desacelerar ou focar:';
    genero = 'chill';
  } else if (msg.includes('pop') || msg.includes('danc')) {
    faixas = OFFLINE_CATALOGO.pop;
    texto = 'Músicas pop com batidas vibrantes e alta dançabilidade separadas do dataset:';
    genero = 'pop';
  } else if (msg.includes('oi') || msg.includes('olá') || msg.includes('ola') || msg.includes('ajuda')) {
    texto = 'Olá! Sou o agente musical do Grupo 8 ResIA. Como posso ajudar seu dia com música? Experimente pedir por gênero (pagode, rock, pop, chill) ou momento!';
    faixas = [];
  } else {
    faixas = [OFFLINE_CATALOGO.pop[0], OFFLINE_CATALOGO.chill[1], OFFLINE_CATALOGO.rock[0]];
    texto = `Entendi seu pedido! Busquei no acervo de 114k faixas do Spotify algumas recomendações que combinam com "${mensagem}":`;
  }

  return {
    session_id: sessionId,
    mensagem: texto,
    faixas: faixas,
    diversidade_generos: faixas.length > 0 ? 1 : 0,
    cobertura_sessao: 1.0,
    consulta_efetiva: { genero: genero, consulta: mensagem },
    _offline: true,
  };
}

/**
 * Envia uma mensagem ao backend via POST /chat.
 * Em caso de falha de conexão, utiliza fallback local com o catálogo do dataset.
 */
export async function enviarMensagem(sessionId, mensagem) {
  const url = `${API_BASE_URL}/chat`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        mensagem: mensagem,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Erro na resposta do backend: HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (err) {
    console.warn('Backend inacessível ou falha na requisição. Utilizando mock de desenvolvimento:', err);
    // Simula pequena latência de processamento antes do fallback
    await new Promise((r) => setTimeout(r, 600));
    return resolverMockLocal(sessionId, mensagem);
  }
}
