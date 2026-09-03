/**
 * Gerador PARAMETRIZADO de Google Forms.
 *
 * Diferença para criar_formulario.gs: aquele cria o formulário com as
 * perguntas hardcoded (chamadas diretas de FormApp). Este lê as perguntas
 * de uma entrada de dados — texto estruturado OU JSON — e monta o form a
 * partir disso, então funciona pra qualquer questionário, não só este.
 *
 * Como usar:
 * 1. Abra https://script.google.com > Novo projeto.
 * 2. Cole este arquivo inteiro.
 * 3. Edite PERGUNTAS_TEXTO (ou PERGUNTAS_JSON, trocando MODO_ENTRADA para
 *    'json') com suas próprias perguntas, seguindo o formato abaixo.
 * 4. Rode a função `gerarFormulario`. Autorize na primeira execução.
 * 5. O log de execução mostra o link de edição e o link público do Form.
 *
 * ---------------------------------------------------------------------
 * FORMATO DE TEXTO (MODO_ENTRADA = 'texto')
 * ---------------------------------------------------------------------
 * Um bloco por pergunta (ou por seção), separados por uma linha "---".
 *
 *   N. Texto da pergunta[*]
 *   Alternativas:
 *   1. Opção A
 *   2. Opção B
 *   ---
 *
 * - "*" no fim do texto da pergunta = obrigatória (sem "*" = opcional).
 * - "Alternativas:" + lista numerada = opções (múltipla escolha/caixa).
 *   Perguntas de texto livre ou escala não levam "Alternativas:".
 * - Tag opcional entre colchetes logo após o número, pra escolher o tipo:
 *     [caixa]      → caixa de seleção (múltiplas respostas)
 *     [curta]      → resposta curta (texto livre de 1 linha)
 *     [paragrafo]  → parágrafo (texto livre longo)
 *     [escala 1-5 | Rótulo do mínimo | Rótulo do máximo] → escala linear
 *     sem tag      → múltipla escolha (padrão)
 * - Um bloco começando com "Seção: <título>" (sem número) vira uma
 *   quebra de seção (nova página no Form) em vez de uma pergunta.
 *
 * Exemplo mínimo:
 *
 *   Seção: Perfil
 *   ---
 *   1. Qual sua idade?*
 *   Alternativas:
 *   1. <18
 *   2. 18-24
 *   ---
 *   2. [escala 1-5 | Discordo totalmente | Concordo totalmente] Gosto de música nova
 *   ---
 *   3. [paragrafo] Algo mais que queira dizer?
 *
 * ---------------------------------------------------------------------
 * FORMATO JSON (MODO_ENTRADA = 'json')
 * ---------------------------------------------------------------------
 * {
 *   "sections": [
 *     {
 *       "title": "Perfil",
 *       "questions": [
 *         {
 *           "type": "multipla_escolha",   // multipla_escolha | caixa_selecao | escala | curta | paragrafo
 *           "text": "Qual sua idade?",
 *           "required": true,
 *           "options": ["<18", "18-24"]
 *         },
 *         {
 *           "type": "escala",
 *           "text": "Gosto de música nova",
 *           "required": false,
 *           "min": 1, "max": 5,
 *           "labelMin": "Discordo totalmente",
 *           "labelMax": "Concordo totalmente"
 *         }
 *       ]
 *     }
 *   ]
 * }
 *
 * PERGUNTAS_JSON também aceita uma string JSON crua (ela é parseada com
 * JSON.parse antes de usar) — útil se você quiser colar o conteúdo de um
 * arquivo .json diretamente.
 */

// ======================= CONFIGURAÇÃO =======================

var FORM_TITLE = 'Pesquisa de hábitos musicais — Projeto ResIA';
var FORM_DESCRICAO =
  'Estamos construindo um agente de recomendação de músicas como ' +
  'projeto acadêmico. Suas respostas (anônimas) ajudam a calibrar as ' +
  'recomendações com base em hábitos reais de escuta. Leva menos de 7 minutos.';

// 'texto' ou 'json' — qual constante abaixo alimenta o gerador.
var MODO_ENTRADA = 'texto';

// ======================= ENTRADA: TEXTO =======================

var PERGUNTAS_TEXTO = `
Seção: Seção 1 — Perfil rápido
---
1. Qual sua faixa etária?*
Alternativas:
1. <18
2. 18–24
3. 25–34
4. 35–44
5. 45–54
6. 55+
---
2. [caixa] Quais serviços de streaming de música você usa?*
Alternativas:
1. Spotify
2. YouTube Music
3. Apple Music
4. Deezer
5. Amazon Music
6. Outro
7. Não uso streaming
---
3. Com que frequência você escuta música?*
Alternativas:
1. Várias vezes ao dia
2. 1x ao dia
3. Algumas vezes na semana
4. Raramente
---
4. Em média, quantas horas por dia você passa ouvindo música?
Alternativas:
1. <1h
2. 1–2h
3. 2–4h
4. 4h+
---
Seção: Seção 2 — Contexto de escuta
---
5. [caixa] Em quais situações você mais ouve música?*
Alternativas:
1. Trabalhando/estudando
2. Se exercitando
3. No transporte
4. Relaxando/dormindo
5. Em festas/eventos sociais
6. Tarefas domésticas
7. Outro
---
6. [caixa] O que mais influencia sua escolha de música no momento? (marque até 3)*
Alternativas:
1. Meu humor
2. A atividade que estou fazendo
3. Recomendação do app
4. Indicação de amigos
5. Redes sociais (TikTok, Reels)
6. Rádio
7. Playlists prontas que já conheço
---
7. Você costuma ouvir músicas em português, inglês, ou ambos?
Alternativas:
1. Majoritariamente português
2. Majoritariamente inglês
3. Equilibrado entre os dois
4. Outros idiomas
5. Não presto atenção ao idioma
---
Seção: Seção 3 — Preferências musicais
---
8. [caixa] Quais gêneros você mais ouve? (marque até 5)*
Alternativas:
1. Pop
2. Rock
3. Sertanejo
4. Funk
5. Hip-Hop/Rap
6. Eletrônica/House
7. MPB/Samba/Pagode/Forró
8. R&B/Soul
9. Outro
---
9. [curta] Dentre os marcados acima, qual é o seu gênero favorito?*
---
10. [caixa] O que mais te atrai em uma música? (marque até 3)*
Alternativas:
1. Letra/mensagem
2. Melodia
3. Ritmo/batida
4. Voz/interpretação do artista
5. Instrumental/produção
6. Dá pra dançar
7. Dá pra treinar
8. Clima/sonoridade geral
9. Fama do artista/hit do momento
---
11. Desses, qual é o MAIS importante pra você gostar de uma música?*
Alternativas:
1. Letra/mensagem
2. Melodia
3. Ritmo/batida
4. Voz/interpretação do artista
5. Instrumental/produção
6. Dá pra dançar
7. Dá pra treinar
8. Clima/sonoridade geral
9. Fama do artista/hit do momento
---
12. [escala 1-5 | Sempre as mesmas bandas/estilos | Gosto de descobrir algo novo toda semana] Como você descreveria seu gosto musical?*
---
13. [escala 1-5 | Calmas/acústicas | Agitadas/eletrônicas] Você prefere músicas mais...
---
14. [escala 1-5 | Tristes/melancólicas | Alegres/animadas] Você prefere músicas mais...
---
15. Você costuma pular músicas com conteúdo explícito (palavrão)?
Alternativas:
1. Sim, sempre
2. Às vezes
3. Não, indiferente
4. Prefiro conteúdo explícito
---
16. Você prefere faixas curtas (~2–3 min) ou mais longas (5 min+)?
Alternativas:
1. Prefiro curtas
2. Prefiro longas
3. Indiferente
---
17. [paragrafo] O que faz você repetir a mesma música várias vezes? (opcional)
---
Seção: Seção 4 — Descoberta e recomendação
---
18. [caixa] Como você geralmente descobre músicas novas?*
Alternativas:
1. Recomendações do app (Discover Weekly, Radio, etc.)
2. Redes sociais
3. Amigos/família
4. Rádio tradicional
5. Trilhas de filmes/séries/jogos
6. Playlists editoriais
---
19. [escala 1-5 | Nunca acerta | Sempre acerta] O quanto você confia nas recomendações automáticas do seu app de streaming?*
---
20. [paragrafo] O que mais te frustra nas recomendações atuais? (opcional)
---
21. Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback?*
Alternativas:
1. Sim
2. Não
3. Talvez
---
22. [curta] Se sim, deixe seu e-mail para contato (opcional)
`;

// ======================= ENTRADA: JSON =======================
// Equivalente exato de PERGUNTAS_TEXTO acima, no formato JSON.
// Troque MODO_ENTRADA para 'json' pra usar esta entrada no lugar.

var PERGUNTAS_JSON = {
  sections: [
    {
      title: 'Seção 1 — Perfil rápido',
      questions: [
        { type: 'multipla_escolha', text: 'Qual sua faixa etária?', required: true,
          options: ['<18', '18–24', '25–34', '35–44', '45–54', '55+'] },
        { type: 'caixa_selecao', text: 'Quais serviços de streaming de música você usa?', required: true,
          options: ['Spotify', 'YouTube Music', 'Apple Music', 'Deezer', 'Amazon Music', 'Outro', 'Não uso streaming'] },
        { type: 'multipla_escolha', text: 'Com que frequência você escuta música?', required: true,
          options: ['Várias vezes ao dia', '1x ao dia', 'Algumas vezes na semana', 'Raramente'] },
        { type: 'multipla_escolha', text: 'Em média, quantas horas por dia você passa ouvindo música?', required: false,
          options: ['<1h', '1–2h', '2–4h', '4h+'] }
      ]
    },
    {
      title: 'Seção 2 — Contexto de escuta',
      questions: [
        { type: 'caixa_selecao', text: 'Em quais situações você mais ouve música?', required: true,
          options: ['Trabalhando/estudando', 'Se exercitando', 'No transporte', 'Relaxando/dormindo', 'Em festas/eventos sociais', 'Tarefas domésticas', 'Outro'] },
        { type: 'caixa_selecao', text: 'O que mais influencia sua escolha de música no momento? (marque até 3)', required: true,
          options: ['Meu humor', 'A atividade que estou fazendo', 'Recomendação do app', 'Indicação de amigos', 'Redes sociais (TikTok, Reels)', 'Rádio', 'Playlists prontas que já conheço'] },
        { type: 'multipla_escolha', text: 'Você costuma ouvir músicas em português, inglês, ou ambos?', required: false,
          options: ['Majoritariamente português', 'Majoritariamente inglês', 'Equilibrado entre os dois', 'Outros idiomas', 'Não presto atenção ao idioma'] }
      ]
    },
    {
      title: 'Seção 3 — Preferências musicais',
      questions: [
        { type: 'caixa_selecao', text: 'Quais gêneros você mais ouve? (marque até 5)', required: true,
          options: ['Pop', 'Rock', 'Sertanejo', 'Funk', 'Hip-Hop/Rap', 'Eletrônica/House', 'MPB/Samba/Pagode/Forró', 'R&B/Soul', 'Outro'] },
        { type: 'curta', text: 'Dentre os marcados acima, qual é o seu gênero favorito?', required: true },
        { type: 'caixa_selecao', text: 'O que mais te atrai em uma música? (marque até 3)', required: true,
          options: ['Letra/mensagem', 'Melodia', 'Ritmo/batida', 'Voz/interpretação do artista', 'Instrumental/produção', 'Dá pra dançar', 'Dá pra treinar', 'Clima/sonoridade geral', 'Fama do artista/hit do momento'] },
        { type: 'multipla_escolha', text: 'Desses, qual é o MAIS importante pra você gostar de uma música?', required: true,
          options: ['Letra/mensagem', 'Melodia', 'Ritmo/batida', 'Voz/interpretação do artista', 'Instrumental/produção', 'Dá pra dançar', 'Dá pra treinar', 'Clima/sonoridade geral', 'Fama do artista/hit do momento'] },
        { type: 'escala', text: 'Como você descreveria seu gosto musical?', required: true,
          min: 1, max: 5, labelMin: 'Sempre as mesmas bandas/estilos', labelMax: 'Gosto de descobrir algo novo toda semana' },
        { type: 'escala', text: 'Você prefere músicas mais...', required: false,
          min: 1, max: 5, labelMin: 'Calmas/acústicas', labelMax: 'Agitadas/eletrônicas' },
        { type: 'escala', text: 'Você prefere músicas mais...', required: false,
          min: 1, max: 5, labelMin: 'Tristes/melancólicas', labelMax: 'Alegres/animadas' },
        { type: 'multipla_escolha', text: 'Você costuma pular músicas com conteúdo explícito (palavrão)?', required: false,
          options: ['Sim, sempre', 'Às vezes', 'Não, indiferente', 'Prefiro conteúdo explícito'] },
        { type: 'multipla_escolha', text: 'Você prefere faixas curtas (~2–3 min) ou mais longas (5 min+)?', required: false,
          options: ['Prefiro curtas', 'Prefiro longas', 'Indiferente'] },
        { type: 'paragrafo', text: 'O que faz você repetir a mesma música várias vezes? (opcional)', required: false }
      ]
    },
    {
      title: 'Seção 4 — Descoberta e recomendação',
      questions: [
        { type: 'caixa_selecao', text: 'Como você geralmente descobre músicas novas?', required: true,
          options: ['Recomendações do app (Discover Weekly, Radio, etc.)', 'Redes sociais', 'Amigos/família', 'Rádio tradicional', 'Trilhas de filmes/séries/jogos', 'Playlists editoriais'] },
        { type: 'escala', text: 'O quanto você confia nas recomendações automáticas do seu app de streaming?', required: true,
          min: 1, max: 5, labelMin: 'Nunca acerta', labelMax: 'Sempre acerta' },
        { type: 'paragrafo', text: 'O que mais te frustra nas recomendações atuais? (opcional)', required: false },
        { type: 'multipla_escolha', text: 'Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback?', required: true,
          options: ['Sim', 'Não', 'Talvez'] },
        { type: 'curta', text: 'Se sim, deixe seu e-mail para contato (opcional)', required: false }
      ]
    }
  ]
};

// ======================= PONTO DE ENTRADA =======================

function gerarFormulario() {
  var itens = (MODO_ENTRADA === 'json')
    ? normalizarJson(PERGUNTAS_JSON)
    : parseTexto(PERGUNTAS_TEXTO);

  var form = construirForm(FORM_TITLE, FORM_DESCRICAO, itens);

  Logger.log('Formulário criado a partir do modo: ' + MODO_ENTRADA);
  Logger.log('Link de edição: ' + form.getEditUrl());
  Logger.log('Link público:   ' + form.getPublishedUrl());
}

// ======================= PARSER: FORMATO TEXTO =======================

function parseTexto(texto) {
  var blocos = texto.split(/\n\s*---\s*\n/)
    .map(function (b) { return b.trim(); })
    .filter(Boolean);

  var itens = [];

  blocos.forEach(function (bloco) {
    var linhas = bloco.split('\n')
      .map(function (l) { return l.trim(); })
      .filter(Boolean);
    if (linhas.length === 0) return;

    var primeira = linhas[0];

    var matchSecao = primeira.match(/^Se[cç][ãa]o:\s*(.+)$/i);
    if (matchSecao) {
      itens.push({ tipo: 'secao', titulo: matchSecao[1].trim() });
      return;
    }

    var matchPergunta = primeira.match(/^\d+\.\s*(?:\[(.*?)\]\s*)?(.+)$/);
    if (!matchPergunta) {
      throw new Error('Bloco não reconhecido (esperava "N. pergunta" ou "Seção: ..."): "' + primeira + '"');
    }

    var pergunta = parseTag(matchPergunta[1] || '');
    var textoPergunta = matchPergunta[2].trim();

    pergunta.obrigatoria = /\*$/.test(textoPergunta);
    pergunta.texto = pergunta.obrigatoria ? textoPergunta.replace(/\*$/, '').trim() : textoPergunta;

    var idxAlt = linhas.findIndex(function (l) { return /^Alternativas:?$/i.test(l); });
    if (idxAlt !== -1) {
      pergunta.opcoes = linhas.slice(idxAlt + 1).map(function (l) {
        return l.replace(/^\d+\.\s*/, '').trim();
      });
    }

    itens.push(pergunta);
  });

  return itens;
}

function parseTag(tag) {
  tag = tag.trim();
  if (!tag) return { tipo: 'multipla_escolha' };

  var partes = tag.split('|').map(function (p) { return p.trim(); });
  var chave = partes[0].toLowerCase();

  if (chave === 'caixa') return { tipo: 'caixa_selecao' };
  if (chave === 'curta') return { tipo: 'curta' };
  if (chave === 'paragrafo') return { tipo: 'paragrafo' };
  if (chave.indexOf('escala') === 0) {
    var bounds = chave.match(/(\d+)\s*-\s*(\d+)/) || [null, '1', '5'];
    return {
      tipo: 'escala',
      min: parseInt(bounds[1], 10),
      max: parseInt(bounds[2], 10),
      rotuloMin: partes[1] || '',
      rotuloMax: partes[2] || ''
    };
  }
  return { tipo: 'multipla_escolha' };
}

// ======================= PARSER: FORMATO JSON =======================

function normalizarJson(entrada) {
  var dados = (typeof entrada === 'string') ? JSON.parse(entrada) : entrada;
  var secoes = dados.sections || [{ questions: dados.questions || [] }];
  var itens = [];

  secoes.forEach(function (secao) {
    if (secao.title) {
      itens.push({ tipo: 'secao', titulo: secao.title });
    }
    (secao.questions || []).forEach(function (q) {
      var item = {
        tipo: q.type || 'multipla_escolha',
        texto: q.text,
        obrigatoria: !!q.required,
        opcoes: q.options
      };
      if (item.tipo === 'escala') {
        item.min = q.min || 1;
        item.max = q.max || 5;
        item.rotuloMin = q.labelMin || '';
        item.rotuloMax = q.labelMax || '';
      }
      itens.push(item);
    });
  });

  return itens;
}

// ======================= CONSTRUÇÃO DO FORM =======================

function construirForm(titulo, descricao, itens) {
  var form = FormApp.create(titulo);
  form.setDescription(descricao);
  form.setCollectEmail(false);
  form.setProgressBar(true);

  itens.forEach(function (item) {
    switch (item.tipo) {
      case 'secao':
        form.addPageBreakItem().setTitle(item.titulo);
        break;
      case 'caixa_selecao':
        form.addCheckboxItem()
          .setTitle(item.texto)
          .setChoiceValues(item.opcoes)
          .setRequired(item.obrigatoria);
        break;
      case 'escala':
        form.addScaleItem()
          .setTitle(item.texto)
          .setBounds(item.min, item.max)
          .setLabels(item.rotuloMin, item.rotuloMax)
          .setRequired(item.obrigatoria);
        break;
      case 'curta':
        form.addTextItem()
          .setTitle(item.texto)
          .setRequired(item.obrigatoria);
        break;
      case 'paragrafo':
        form.addParagraphTextItem()
          .setTitle(item.texto)
          .setRequired(item.obrigatoria);
        break;
      case 'multipla_escolha':
      default:
        form.addMultipleChoiceItem()
          .setTitle(item.texto)
          .setChoiceValues(item.opcoes)
          .setRequired(item.obrigatoria);
        break;
    }
  });

  return form;
}
