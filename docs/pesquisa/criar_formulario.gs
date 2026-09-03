/**
 * Cria/edita o Google Form "Pesquisa de hábitos musicais — Projeto ResIA"
 * a partir do roteiro em docs/pesquisa/questionario-habitos-musicais.md.
 *
 * Como usar (primeira vez):
 * 1. Abra https://script.google.com > Novo projeto.
 * 2. Apague o conteúdo padrão e cole este arquivo inteiro.
 * 3. Selecione a função `criarFormulario` no menu de execução e clique
 *    em "Executar". Na primeira vez, autorize o script (ele só cria
 *    formulários na sua conta, não acessa mais nada).
 * 4. Veja o resultado em "Execuções" (ou Visualizar > Registros): o log
 *    mostra o link de edição e o link público do formulário.
 *
 * Como usar (já criou o form e quer atualizar as perguntas):
 * 1. Copie o ID do formulário: é o trecho entre "/d/" e "/edit" no link
 *    de edição que apareceu no log (docs.google.com/forms/d/ESSE_ID/edit).
 * 2. Cole o ID na constante FORM_ID abaixo.
 * 3. Edite as perguntas dentro de `preencherFormulario`.
 * 4. Rode a função `editarFormulario`. Ela apaga todas as perguntas do
 *    form existente e recria a partir do código — sem gerar um novo link.
 */

// Cole aqui o ID do formulário já criado (fica vazio até você rodar
// criarFormulario() e copiar o ID do link de edição gerado no log).
var FORM_ID = '';

function criarFormulario() {
  var form = FormApp.create('Pesquisa de hábitos musicais — Projeto ResIA');
  preencherFormulario(form);

  Logger.log('Formulário criado.');
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
  preencherFormulario(form);

  Logger.log('Formulário atualizado.');
  Logger.log('Link de edição: ' + form.getEditUrl());
  Logger.log('Link público:   ' + form.getPublishedUrl());
}

function preencherFormulario(form) {
  form.setTitle('Pesquisa de hábitos musicais — Projeto ResIA');
  form.setDescription(
    'Estamos construindo um agente de recomendação de músicas como ' +
    'projeto acadêmico. Suas respostas (anônimas) ajudam a calibrar as ' +
    'recomendações com base em hábitos reais de escuta. Leva menos de 7 minutos.'
  );
  form.setCollectEmail(false);
  form.setProgressBar(true);
  form.setShuffleQuestions(false);

  // ---------- Seção 1 — Perfil rápido ----------
  form.addPageBreakItem().setTitle('Seção 1 — Perfil rápido');

  form.addMultipleChoiceItem()
    .setTitle('Qual sua faixa etária?')
    .setChoiceValues(['<18', '18–24', '25–34', '35–44', '45–54', '55+'])
    .setRequired(true);

  var usaStreaming = form.addMultipleChoiceItem()
    .setTitle('Você usa algum serviço de streaming de música (Spotify, YouTube Music, etc.)?')
    .setRequired(true);

  var pageDetalheStreaming = form.addPageBreakItem().setTitle('Seção 1 — Detalhe do streaming');

  form.addCheckboxItem()
    .setTitle('Quais serviços de streaming de música você usa?')
    .setChoiceValues(['Spotify', 'YouTube Music', 'Apple Music', 'Deezer', 'Amazon Music'])
    .showOtherOption(true)
    .setRequired(true);

  var pageFrequencia = form.addPageBreakItem().setTitle('Seção 1 — Frequência de escuta');

  usaStreaming.setChoices([
    usaStreaming.createChoice('Sim', pageDetalheStreaming),
    usaStreaming.createChoice('Não', pageFrequencia)
  ]);

  form.addMultipleChoiceItem()
    .setTitle('Com que frequência você escuta música?')
    .setChoiceValues(['Várias vezes ao dia', '1x ao dia', 'Algumas vezes na semana', 'Raramente'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Em média, quantas horas por dia você passa ouvindo música?')
    .setChoiceValues(['<1h', '1–2h', '2–4h', '4h+'])
    .setRequired(false);

  // ---------- Seção 2 — Contexto de escuta ----------
  form.addPageBreakItem().setTitle('Seção 2 — Contexto de escuta');

  form.addCheckboxItem()
    .setTitle('Em quais situações você mais ouve música?')
    .setChoiceValues(['Trabalhando/estudando', 'Se exercitando', 'No transporte', 'Relaxando/dormindo', 'Em festas/eventos sociais', 'Tarefas domésticas'])
    .showOtherOption(true)
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('O que mais influencia sua escolha de música no momento? (marque até 3)')
    .setChoiceValues(['Meu humor', 'A atividade que estou fazendo', 'Recomendação do app', 'Indicação de amigos', 'Redes sociais (TikTok, Reels)', 'Rádio', 'Playlists prontas que já conheço'])
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Em qual(is) idioma(s) você mais ouve música?')
    .setChoiceValues(['Majoritariamente português', 'Majoritariamente inglês', 'Equilibrado entre português e inglês', 'Não presto atenção ao idioma'])
    .showOtherOption(true)
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Você costuma ouvir playlists prontas (do app/editoriais) ou prefere montar as suas próprias?')
    .setChoiceValues(['Só playlists prontas', 'Mistura playlists prontas e próprias', 'Só playlists próprias', 'Não uso playlists'])
    .setRequired(false);

  // ---------- Seção 3 — Preferências musicais ----------
  form.addPageBreakItem().setTitle('Seção 3 — Preferências musicais');

  form.addCheckboxItem()
    .setTitle('Quais gêneros você mais ouve? (marque até 5)')
    .setChoiceValues(['Pop', 'Rock', 'Sertanejo', 'Funk', 'Hip-Hop/Rap', 'Eletrônica/House', 'MPB/Samba/Pagode/Forró', 'R&B/Soul'])
    .showOtherOption(true)
    .setRequired(true);

  form.addTextItem()
    .setTitle('Dentre os marcados acima, qual é o seu gênero favorito?')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Cite até 3 artistas ou bandas que você mais ouve atualmente (opcional)')
    .setRequired(false);

  var atracoes = ['Letra/mensagem', 'Melodia', 'Ritmo/batida', 'Voz/interpretação do artista', 'Instrumental/produção', 'Dá pra dançar', 'Dá pra treinar', 'Clima/sonoridade geral', 'Fama do artista/hit do momento'];

  form.addCheckboxItem()
    .setTitle('O que mais te atrai em uma música? (marque até 3)')
    .setChoiceValues(atracoes)
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Desses, qual é o MAIS importante pra você gostar de uma música?')
    .setChoiceValues(atracoes)
    .showOtherOption(true)
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Como você descreveria seu gosto musical?')
    .setBounds(1, 5)
    .setLabels('Sempre as mesmas bandas/estilos', 'Gosto de descobrir algo novo toda semana')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Você prefere músicas mais calmas/acústicas ou agitadas/eletrônicas?')
    .setBounds(1, 5)
    .setLabels('Calmas/acústicas', 'Agitadas/eletrônicas')
    .setRequired(false);

  form.addScaleItem()
    .setTitle('Você prefere músicas mais tristes/melancólicas ou alegres/animadas?')
    .setBounds(1, 5)
    .setLabels('Tristes/melancólicas', 'Alegres/animadas')
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Você costuma pular músicas com conteúdo explícito (palavrão)?')
    .setChoiceValues(['Sim, sempre', 'Às vezes', 'Não, indiferente', 'Prefiro conteúdo explícito'])
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Você prefere faixas curtas (~2–3 min) ou mais longas (5 min+)?')
    .setChoiceValues(['Prefiro curtas', 'Prefiro longas', 'Indiferente'])
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('O que faz você repetir a mesma música várias vezes? (opcional)')
    .setRequired(false);

  // ---------- Seção 4 — Descoberta e recomendação ----------
  form.addPageBreakItem().setTitle('Seção 4 — Descoberta e recomendação');

  form.addCheckboxItem()
    .setTitle('Como você geralmente descobre músicas novas?')
    .setChoiceValues(['Recomendações do app (Discover Weekly, Radio, etc.)', 'Redes sociais', 'Amigos/família', 'Rádio tradicional', 'Trilhas de filmes/séries/jogos', 'Playlists editoriais'])
    .showOtherOption(true)
    .setRequired(true);

  form.addScaleItem()
    .setTitle('O quanto você confia nas recomendações automáticas do seu app de streaming?')
    .setBounds(1, 5)
    .setLabels('Nunca acerta', 'Sempre acerta')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('O que mais te frustra nas recomendações atuais? (opcional)')
    .setRequired(false);

  var testariaBeta = form.addMultipleChoiceItem()
    .setTitle('Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback?')
    .setRequired(true);

  var pageContato = form.addPageBreakItem().setTitle('Contato');

  form.addTextItem()
    .setTitle('Deixe seu e-mail para contato (opcional)')
    .setRequired(false);

  testariaBeta.setChoices([
    testariaBeta.createChoice('Sim', pageContato),
    testariaBeta.createChoice('Talvez', pageContato),
    testariaBeta.createChoice('Não', FormApp.PageNavigationType.SUBMIT)
  ]);
}
