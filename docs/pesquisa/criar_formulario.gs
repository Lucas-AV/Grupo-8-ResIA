/**
 * Cria o Google Form "Pesquisa de hábitos musicais — Projeto ResIA"
 * a partir do roteiro em docs/pesquisa/questionario-habitos-musicais.md.
 *
 * Como usar:
 * 1. Abra https://script.google.com > Novo projeto.
 * 2. Apague o conteúdo padrão e cole este arquivo inteiro.
 * 3. Selecione a função `criarFormulario` no menu de execução e clique
 *    em "Executar". Na primeira vez, autorize o script (ele só cria
 *    formulários na sua conta, não acessa mais nada).
 * 4. Veja o resultado em "Execuções" (ou Visualizar > Registros): o log
 *    mostra o link de edição e o link público do formulário.
 */
function criarFormulario() {
  var form = FormApp.create('Pesquisa de hábitos musicais — Projeto ResIA');

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

  form.addCheckboxItem()
    .setTitle('Quais serviços de streaming de música você usa?')
    .setChoiceValues(['Spotify', 'YouTube Music', 'Apple Music', 'Deezer', 'Amazon Music', 'Outro', 'Não uso streaming'])
    .setRequired(true);

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
    .setChoiceValues(['Trabalhando/estudando', 'Se exercitando', 'No transporte', 'Relaxando/dormindo', 'Em festas/eventos sociais', 'Tarefas domésticas', 'Outro'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('O que mais influencia sua escolha de música no momento? (marque até 3)')
    .setChoiceValues(['Meu humor', 'A atividade que estou fazendo', 'Recomendação do app', 'Indicação de amigos', 'Redes sociais (TikTok, Reels)', 'Rádio', 'Playlists prontas que já conheço'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Você costuma ouvir músicas em português, inglês, ou ambos?')
    .setChoiceValues(['Majoritariamente português', 'Majoritariamente inglês', 'Equilibrado entre os dois', 'Outros idiomas', 'Não presto atenção ao idioma'])
    .setRequired(false);

  // ---------- Seção 3 — Preferências musicais ----------
  form.addPageBreakItem().setTitle('Seção 3 — Preferências musicais');

  form.addCheckboxItem()
    .setTitle('Quais gêneros você mais ouve? (marque até 5)')
    .setChoiceValues(['Pop', 'Rock', 'Sertanejo', 'Funk', 'Hip-Hop/Rap', 'Eletrônica/House', 'MPB/Samba/Pagode/Forró', 'R&B/Soul', 'Outro'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Dentre os marcados acima, qual é o seu gênero favorito?')
    .setRequired(true);

  var atracoes = ['Letra/mensagem', 'Melodia', 'Ritmo/batida', 'Voz/interpretação do artista', 'Instrumental/produção', 'Dá pra dançar', 'Dá pra treinar', 'Clima/sonoridade geral', 'Fama do artista/hit do momento'];

  form.addCheckboxItem()
    .setTitle('O que mais te atrai em uma música? (marque até 3)')
    .setChoiceValues(atracoes)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Desses, qual é o MAIS importante pra você gostar de uma música?')
    .setChoiceValues(atracoes)
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Como você descreveria seu gosto musical?')
    .setBounds(1, 5)
    .setLabels('Sempre as mesmas bandas/estilos', 'Gosto de descobrir algo novo toda semana')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Você prefere músicas mais...')
    .setBounds(1, 5)
    .setLabels('Calmas/acústicas', 'Agitadas/eletrônicas')
    .setRequired(false);

  form.addScaleItem()
    .setTitle('Você prefere músicas mais...')
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
    .setRequired(true);

  form.addScaleItem()
    .setTitle('O quanto você confia nas recomendações automáticas do seu app de streaming?')
    .setBounds(1, 5)
    .setLabels('Nunca acerta', 'Sempre acerta')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('O que mais te frustra nas recomendações atuais? (opcional)')
    .setRequired(false);

  form.addMultipleChoiceItem()
    .setTitle('Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback?')
    .setChoiceValues(['Sim', 'Não', 'Talvez'])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Se sim, deixe seu e-mail para contato (opcional)')
    .setRequired(false);

  Logger.log('Formulário criado.');
  Logger.log('Link de edição: ' + form.getEditUrl());
  Logger.log('Link público:   ' + form.getPublishedUrl());
}
