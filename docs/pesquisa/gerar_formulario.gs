/**
 * Gerador PARAMETRIZADO de Google Forms.
 *
 * Diferença para criar_formulario.gs: aquele cria o formulário com as
 * perguntas hardcoded (chamadas diretas de FormApp). Este lê as perguntas
 * de uma entrada de dados — texto estruturado OU JSON — e monta o form a
 * partir disso, então funciona pra qualquer questionário, não só este.
 *
 * Como usar (primeira vez):
 * 1. Abra https://script.google.com > Novo projeto.
 * 2. Cole este arquivo inteiro.
 * 3. Edite PERGUNTAS_TEXTO (ou PERGUNTAS_JSON, trocando MODO_ENTRADA para
 *    'json') com suas próprias perguntas, seguindo o formato abaixo.
 * 4. Rode a função `gerarFormulario`. Autorize na primeira execução.
 * 5. O log de execução mostra o link de edição e o link público do Form.
 *
 * Como usar (já criou o form e quer atualizar as perguntas):
 * 1. Copie o ID do formulário: é o trecho entre "/d/" e "/edit" no link
 *    de edição que apareceu no log (docs.google.com/forms/d/ESSE_ID/edit).
 * 2. Cole o ID na constante FORM_ID abaixo.
 * 3. Edite PERGUNTAS_TEXTO/PERGUNTAS_JSON.
 * 4. Rode a função `editarFormulario`. Ela apaga todas as perguntas do
 *    form existente e recria a partir do código — sem gerar um novo link.
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
 * - Tag opcional entre colchetes logo após o número, pra escolher o tipo
 *   e/ou adicionar opção "Outro" com campo de texto livre. Tokens
 *   separados por vírgula, em qualquer ordem:
 *     [caixa]        → caixa de seleção (múltiplas respostas)
 *     [curta]        → resposta curta (texto livre de 1 linha)
 *     [paragrafo]    → parágrafo (texto livre longo)
 *     [escala 1-5 | Rótulo do mínimo | Rótulo do máximo] → escala linear
 *     [outro]        → adiciona opção "Outro:" com texto livre
 *                       (só vale pra múltipla escolha/caixa; combine com
 *                       o tipo, ex: "[caixa, outro]")
 *     sem tag        → múltipla escolha (padrão)
 * - Um bloco começando com "Seção: <título>" (sem número) vira uma
 *   quebra de seção (nova página no Form) em vez de uma pergunta. O
 *   título também serve de "rótulo" pra navegação condicional (ver
 *   abaixo) — precisa ser único.
 * - Navegação condicional (pular pergunta/seção conforme a resposta):
 *   numa pergunta de múltipla escolha (não vale pra caixa de seleção,
 *   o Google Forms não permite pular página em perguntas de múltiplas
 *   respostas), cada alternativa pode terminar em " -> Destino":
 *     1. Sim -> Seção 2 — Contexto de escuta
 *     2. Não -> FIM
 *   "Destino" é o título exato de um bloco "Seção: ...". Use "FIM" para
 *   enviar o formulário imediatamente (pula tudo que vem depois). Se
 *   nenhuma alternativa da pergunta tiver "->", ela segue o fluxo normal
 *   (sem pular nada).
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
 *           "type": "multipla_escolha",
 *           "text": "Você usa streaming?",
 *           "required": true,
 *           "options": [
 *             { "value": "Sim", "goTo": "Contexto" },
 *             { "value": "Não", "goTo": "FIM" }
 *           ]
 *         },
 *         {
 *           "type": "caixa_selecao",
 *           "text": "Quais serviços você usa?",
 *           "required": true,
 *           "other": true,
 *           "options": ["Spotify", "Deezer"]
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
 * "other": true adiciona opção "Outro:" com texto livre (multipla_escolha
 * ou caixa_selecao). Uma opção pode ser string simples ou objeto
 * { "value": ..., "goTo": "<título da seção>" | "FIM" } pra navegação
 * condicional — só em multipla_escolha, mesma regra do formato texto.
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

// Cole aqui o ID do formulário já criado (fica vazio até você rodar
// gerarFormulario() e copiar o ID do link de edição gerado no log).
var FORM_ID = '';

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
2. Você usa algum serviço de streaming de música (Spotify, YouTube Music, etc.)?*
Alternativas:
1. Sim -> Seção 1 — Detalhe do streaming
2. Não -> Seção 1 — Frequência de escuta
---
Seção: Seção 1 — Detalhe do streaming
---
3. [caixa, outro] Quais serviços de streaming de música você usa?*
Alternativas:
1. Spotify
2. YouTube Music
3. Apple Music
4. Deezer
5. Amazon Music
---
Seção: Seção 1 — Frequência de escuta
---
4. Com que frequência você escuta música?*
Alternativas:
1. Várias vezes ao dia
2. 1x ao dia
3. Algumas vezes na semana
4. Raramente
---
5. Em média, quantas horas por dia você passa ouvindo música?
Alternativas:
1. <1h
2. 1–2h
3. 2–4h
4. 4h+
---
Seção: Seção 2 — Contexto de escuta
---
6. [caixa, outro] Em quais situações você mais ouve música?*
Alternativas:
1. Trabalhando/estudando
2. Se exercitando
3. No transporte
4. Relaxando/dormindo
5. Em festas/eventos sociais
6. Tarefas domésticas
---
7. [caixa, outro] O que mais influencia sua escolha de música no momento? (marque até 3)*
Alternativas:
1. Meu humor
2. A atividade que estou fazendo
3. Recomendação do app
4. Indicação de amigos
5. Redes sociais (TikTok, Reels)
6. Rádio
7. Playlists prontas que já conheço
---
8. [outro] Em qual(is) idioma(s) você mais ouve música?
Alternativas:
1. Majoritariamente português
2. Majoritariamente inglês
3. Equilibrado entre português e inglês
4. Não presto atenção ao idioma
---
9. Você costuma ouvir playlists prontas (do app/editoriais) ou prefere montar as suas próprias?
Alternativas:
1. Só playlists prontas
2. Mistura playlists prontas e próprias
3. Só playlists próprias
4. Não uso playlists
---
Seção: Seção 3 — Preferências musicais
---
10. [caixa, outro] Quais gêneros você mais ouve? (marque até 5)*
Alternativas:
1. Pop
2. Rock
3. Sertanejo
4. Funk
5. Hip-Hop/Rap
6. Eletrônica/House
7. MPB/Samba/Pagode/Forró
8. R&B/Soul
---
11. [curta] Dentre os marcados acima, qual é o seu gênero favorito?*
---
12. [paragrafo] Cite até 3 artistas ou bandas que você mais ouve atualmente (opcional)
---
13. [caixa, outro] O que mais te atrai em uma música? (marque até 3)*
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
14. [outro] Desses, qual é o MAIS importante pra você gostar de uma música?*
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
15. [escala 1-5 | Sempre as mesmas bandas/estilos | Gosto de descobrir algo novo toda semana] Como você descreveria seu gosto musical?*
---
16. [escala 1-5 | Calmas/acústicas | Agitadas/eletrônicas] Você prefere músicas mais calmas/acústicas ou agitadas/eletrônicas?
---
17. [escala 1-5 | Tristes/melancólicas | Alegres/animadas] Você prefere músicas mais tristes/melancólicas ou alegres/animadas?
---
18. Você costuma pular músicas com conteúdo explícito (palavrão)?
Alternativas:
1. Sim, sempre
2. Às vezes
3. Não, indiferente
4. Prefiro conteúdo explícito
---
19. Você prefere faixas curtas (~2–3 min) ou mais longas (5 min+)?
Alternativas:
1. Prefiro curtas
2. Prefiro longas
3. Indiferente
---
20. [paragrafo] O que faz você repetir a mesma música várias vezes? (opcional)
---
Seção: Seção 4 — Descoberta e recomendação
---
21. [caixa, outro] Como você geralmente descobre músicas novas?*
Alternativas:
1. Recomendações do app (Discover Weekly, Radio, etc.)
2. Redes sociais
3. Amigos/família
4. Rádio tradicional
5. Trilhas de filmes/séries/jogos
6. Playlists editoriais
---
22. [escala 1-5 | Nunca acerta | Sempre acerta] O quanto você confia nas recomendações automáticas do seu app de streaming?*
---
23. [paragrafo] O que mais te frustra nas recomendações atuais? (opcional)
---
24. Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback?*
Alternativas:
1. Sim -> Contato
2. Talvez -> Contato
3. Não -> FIM
---
Seção: Contato
---
25. [curta] Deixe seu e-mail para contato (opcional)
`;

// ======================= ENTRADA: JSON =======================
// Equivalente exato de PERGUNTAS_TEXTO acima, no formato JSON.
// Troque MODO_ENTRADA para 'json' pra usar esta entrada no lugar.

var ATRACOES = ['Letra/mensagem', 'Melodia', 'Ritmo/batida', 'Voz/interpretação do artista', 'Instrumental/produção', 'Dá pra dançar', 'Dá pra treinar', 'Clima/sonoridade geral', 'Fama do artista/hit do momento'];

var PERGUNTAS_JSON = {
  sections: [
    {
      title: 'Seção 1 — Perfil rápido',
      questions: [
        { type: 'multipla_escolha', text: 'Qual sua faixa etária?', required: true,
          options: ['<18', '18–24', '25–34', '35–44', '45–54', '55+'] },
        { type: 'multipla_escolha', text: 'Você usa algum serviço de streaming de música (Spotify, YouTube Music, etc.)?', required: true,
          options: [
            { value: 'Sim', goTo: 'Seção 1 — Detalhe do streaming' },
            { value: 'Não', goTo: 'Seção 1 — Frequência de escuta' }
          ] }
      ]
    },
    {
      title: 'Seção 1 — Detalhe do streaming',
      questions: [
        { type: 'caixa_selecao', text: 'Quais serviços de streaming de música você usa?', required: true, other: true,
          options: ['Spotify', 'YouTube Music', 'Apple Music', 'Deezer', 'Amazon Music'] }
      ]
    },
    {
      title: 'Seção 1 — Frequência de escuta',
      questions: [
        { type: 'multipla_escolha', text: 'Com que frequência você escuta música?', required: true,
          options: ['Várias vezes ao dia', '1x ao dia', 'Algumas vezes na semana', 'Raramente'] },
        { type: 'multipla_escolha', text: 'Em média, quantas horas por dia você passa ouvindo música?', required: false,
          options: ['<1h', '1–2h', '2–4h', '4h+'] }
      ]
    },
    {
      title: 'Seção 2 — Contexto de escuta',
      questions: [
        { type: 'caixa_selecao', text: 'Em quais situações você mais ouve música?', required: true, other: true,
          options: ['Trabalhando/estudando', 'Se exercitando', 'No transporte', 'Relaxando/dormindo', 'Em festas/eventos sociais', 'Tarefas domésticas'] },
        { type: 'caixa_selecao', text: 'O que mais influencia sua escolha de música no momento? (marque até 3)', required: true, other: true,
          options: ['Meu humor', 'A atividade que estou fazendo', 'Recomendação do app', 'Indicação de amigos', 'Redes sociais (TikTok, Reels)', 'Rádio', 'Playlists prontas que já conheço'] },
        { type: 'multipla_escolha', text: 'Em qual(is) idioma(s) você mais ouve música?', required: false, other: true,
          options: ['Majoritariamente português', 'Majoritariamente inglês', 'Equilibrado entre português e inglês', 'Não presto atenção ao idioma'] },
        { type: 'multipla_escolha', text: 'Você costuma ouvir playlists prontas (do app/editoriais) ou prefere montar as suas próprias?', required: false,
          options: ['Só playlists prontas', 'Mistura playlists prontas e próprias', 'Só playlists próprias', 'Não uso playlists'] }
      ]
    },
    {
      title: 'Seção 3 — Preferências musicais',
      questions: [
        { type: 'caixa_selecao', text: 'Quais gêneros você mais ouve? (marque até 5)', required: true, other: true,
          options: ['Pop', 'Rock', 'Sertanejo', 'Funk', 'Hip-Hop/Rap', 'Eletrônica/House', 'MPB/Samba/Pagode/Forró', 'R&B/Soul'] },
        { type: 'curta', text: 'Dentre os marcados acima, qual é o seu gênero favorito?', required: true },
        { type: 'paragrafo', text: 'Cite até 3 artistas ou bandas que você mais ouve atualmente (opcional)', required: false },
        { type: 'caixa_selecao', text: 'O que mais te atrai em uma música? (marque até 3)', required: true, other: true,
          options: ATRACOES },
        { type: 'multipla_escolha', text: 'Desses, qual é o MAIS importante pra você gostar de uma música?', required: true, other: true,
          options: ATRACOES },
        { type: 'escala', text: 'Como você descreveria seu gosto musical?', required: true,
          min: 1, max: 5, labelMin: 'Sempre as mesmas bandas/estilos', labelMax: 'Gosto de descobrir algo novo toda semana' },
        { type: 'escala', text: 'Você prefere músicas mais calmas/acústicas ou agitadas/eletrônicas?', required: false,
          min: 1, max: 5, labelMin: 'Calmas/acústicas', labelMax: 'Agitadas/eletrônicas' },
        { type: 'escala', text: 'Você prefere músicas mais tristes/melancólicas ou alegres/animadas?', required: false,
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
        { type: 'caixa_selecao', text: 'Como você geralmente descobre músicas novas?', required: true, other: true,
          options: ['Recomendações do app (Discover Weekly, Radio, etc.)', 'Redes sociais', 'Amigos/família', 'Rádio tradicional', 'Trilhas de filmes/séries/jogos', 'Playlists editoriais'] },
        { type: 'escala', text: 'O quanto você confia nas recomendações automáticas do seu app de streaming?', required: true,
          min: 1, max: 5, labelMin: 'Nunca acerta', labelMax: 'Sempre acerta' },
        { type: 'paragrafo', text: 'O que mais te frustra nas recomendações atuais? (opcional)', required: false },
        { type: 'multipla_escolha', text: 'Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback?', required: true,
          options: [
            { value: 'Sim', goTo: 'Contato' },
            { value: 'Talvez', goTo: 'Contato' },
            { value: 'Não', goTo: 'FIM' }
          ] }
      ]
    },
    {
      title: 'Contato',
      questions: [
        { type: 'curta', text: 'Deixe seu e-mail para contato (opcional)', required: false }
      ]
    }
  ]
};

// ======================= PONTO DE ENTRADA =======================

function gerarFormulario() {
  var form = FormApp.create(FORM_TITLE);
  preencherForm(form);

  Logger.log('Formulário criado a partir do modo: ' + MODO_ENTRADA);
  Logger.log('Link de edição: ' + form.getEditUrl());
  Logger.log('Link público:   ' + form.getPublishedUrl());
}

function editarFormulario() {
  if (!FORM_ID) {
    throw new Error('Defina FORM_ID no topo do arquivo com o ID do formulário (está na URL de edição, entre "/d/" e "/edit").');
  }

  var form = FormApp.openById(FORM_ID);
  form.getItems().forEach(function (item) {
    form.deleteItem(item);
  });
  preencherForm(form);

  Logger.log('Formulário atualizado a partir do modo: ' + MODO_ENTRADA);
  Logger.log('Link de edição: ' + form.getEditUrl());
  Logger.log('Link público:   ' + form.getPublishedUrl());
}

function preencherForm(form) {
  var itens = (MODO_ENTRADA === 'json')
    ? normalizarJson(PERGUNTAS_JSON)
    : parseTexto(PERGUNTAS_TEXTO);

  form.setTitle(FORM_TITLE);
  form.setDescription(FORM_DESCRICAO);
  form.setCollectEmail(false);
  form.setProgressBar(true);

  construirItens(form, itens);
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
        return parseOpcao(l.replace(/^\d+\.\s*/, '').trim());
      });
    }

    itens.push(pergunta);
  });

  return itens;
}

function parseOpcao(texto) {
  var match = texto.match(/^(.+?)\s*->\s*(.+)$/);
  if (!match) return texto;
  return { valor: match[1].trim(), destino: match[2].trim() };
}

function parseTag(tag) {
  tag = tag.trim();
  if (!tag) return { tipo: 'multipla_escolha' };

  var tokens = tag.split(',').map(function (t) { return t.trim(); }).filter(Boolean);
  var outro = false;
  var tipoToken = null;
  tokens.forEach(function (t) {
    if (/^outro$/i.test(t)) {
      outro = true;
    } else {
      tipoToken = t;
    }
  });

  if (!tipoToken) return { tipo: 'multipla_escolha', outro: outro };

  var partes = tipoToken.split('|').map(function (p) { return p.trim(); });
  var chave = partes[0].toLowerCase();

  if (chave === 'caixa') return { tipo: 'caixa_selecao', outro: outro };
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
  return { tipo: 'multipla_escolha', outro: outro };
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
        outro: !!q.other,
        opcoes: (q.options || []).map(function (op) {
          if (typeof op === 'string') return op;
          return { valor: op.value, destino: op.goTo };
        })
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

function valoresSimples(opcoes) {
  return (opcoes || []).map(function (op) {
    return (typeof op === 'string') ? op : op.valor;
  });
}

function temDestino(opcoes) {
  return (opcoes || []).some(function (op) {
    return typeof op === 'object' && op.destino;
  });
}

function construirItens(form, itens) {
  var labels = {};
  var pendentesBranch = [];

  itens.forEach(function (item) {
    switch (item.tipo) {
      case 'secao':
        labels[item.titulo] = form.addPageBreakItem().setTitle(item.titulo);
        break;
      case 'caixa_selecao':
        if (temDestino(item.opcoes)) {
          throw new Error('Caixa de seleção não suporta navegação condicional (Google Forms só permite pular página em múltipla escolha/dropdown): "' + item.texto + '"');
        }
        var caixa = form.addCheckboxItem()
          .setTitle(item.texto)
          .setChoiceValues(valoresSimples(item.opcoes))
          .setRequired(item.obrigatoria);
        if (item.outro) caixa.showOtherOption(true);
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
        var multipla = form.addMultipleChoiceItem()
          .setTitle(item.texto)
          .setRequired(item.obrigatoria);
        if (item.outro) multipla.showOtherOption(true);
        if (temDestino(item.opcoes)) {
          pendentesBranch.push({ item: multipla, opcoes: item.opcoes });
        } else {
          multipla.setChoiceValues(valoresSimples(item.opcoes));
        }
        break;
    }
  });

  pendentesBranch.forEach(function (pendente) {
    var choices = pendente.opcoes.map(function (op) {
      if (typeof op === 'string') {
        return pendente.item.createChoice(op, FormApp.PageNavigationType.CONTINUE);
      }
      var destino = /^FIM$/i.test(op.destino) ? FormApp.PageNavigationType.SUBMIT : labels[op.destino];
      if (!destino) {
        throw new Error('Seção de destino "' + op.destino + '" não encontrada (pergunta: "' + pendente.item.getTitle() + '"). Confira se existe um bloco "Seção: ' + op.destino + '" com esse título exato.');
      }
      return pendente.item.createChoice(op.valor, destino);
    });
    pendente.item.setChoices(choices);
  });
}
