# Questionário: Hábitos Musicais dos Usuários

Roteiro para montar no Google Forms. Objetivo: coletar dados de
preferência/comportamento de escuta que o `dataset.csv` (Kaggle) não tem —
ele só traz metadados agregados por faixa, sem histórico ou avaliação por
usuário (ver `README.md`, seção "Base de dados"). Essas respostas servem
como dataset complementar para treinar/avaliar o agente de recomendação.

Tempo estimado de resposta: 5–7 min. Anônimo, sem perguntas sensíveis.

---

## Configuração do Form

- **Título:** Pesquisa de hábitos musicais — Projeto ResIA
- **Descrição:** "Estamos construindo um agente de recomendação de músicas
  como projeto acadêmico. Suas respostas (anônimas) ajudam a calibrar as
  recomendações com base em hábitos reais de escuta. Leva menos de 5
  minutos."
- Ativar "Coletar e-mails": **não** (manter anônimo, exceto seção final opt-in)
- Ativar barra de progresso: sim
- Dividir em **4 seções** (quebras de seção abaixo)

---

## Seção 1 — Perfil rápido

| # | Pergunta | Tipo Google Forms | Opções | Obrigatória |
|---|---|---|---|---|
| 1.1 | Qual sua faixa etária? | Múltipla escolha | <18 / 18–24 / 25–34 / 35–44 / 45–54 / 55+ | Sim |
| 1.2 | Quais serviços de streaming de música você usa? | Caixas de seleção | Spotify / YouTube Music / Apple Music / Deezer / Amazon Music / Outro / Não uso streaming | Sim |
| 1.3 | Com que frequência você escuta música? | Múltipla escolha | Várias vezes ao dia / 1x ao dia / Algumas vezes na semana / Raramente | Sim |
| 1.4 | Em média, quantas horas por dia você passa ouvindo música? | Múltipla escolha | <1h / 1–2h / 2–4h / 4h+ | Não |

*Por quê:* segmenta respostas por perfil de consumo (proxy pro `popularity`
e volume de escuta).

---

## Seção 2 — Contexto de escuta

| # | Pergunta | Tipo Google Forms | Opções | Obrigatória |
|---|---|---|---|---|
| 2.1 | Em quais situações você mais ouve música? | Caixas de seleção | Trabalhando/estudando / Se exercitando / No transporte / Relaxando/dormindo / Em festas/eventos sociais / Tarefas domésticas / Outro | Sim |
| 2.2 | O que mais influencia sua escolha de música no momento? | Caixas de seleção (máx. 3 — orientar no texto da pergunta) | Meu humor / A atividade que estou fazendo / Recomendação do app / Indicação de amigos / Redes sociais (TikTok, Reels) / Rádio / Playlists prontas que já conheço | Sim |
| 2.3 | Você costuma ouvir músicas em português, inglês, ou ambos? | Múltipla escolha | Majoritariamente português / Majoritariamente inglês / Equilibrado entre os dois / Outros idiomas / Não presto atenção ao idioma | Não |

*Por quê:* contexto de uso é o que dataset de faixas não captura — ajuda a
priorizar features tipo `energy`/`valence` por situação de escuta.

---

## Seção 3 — Preferências musicais

| # | Pergunta | Tipo Google Forms | Opções | Obrigatória |
|---|---|---|---|---|
| 3.1 | Quais gêneros você mais ouve? (marque até 5) | Caixas de seleção | Pop / Rock / Sertanejo / Funk / Hip-Hop/Rap / Eletrônica/House / MPB/Samba/Pagode/Forró / R&B/Soul / Outro | Sim |
| 3.2 | Dentre os marcados acima, qual é o seu gênero favorito? | Resposta curta | — | Sim |
| 3.3 | O que mais te atrai em uma música? (marque até 3) | Caixas de seleção | Letra/mensagem · Melodia · Ritmo/batida · Voz/interpretação do artista · Instrumental/produção · Dá pra dançar · Dá pra treinar · Clima/sonoridade geral · Fama do artista/hit do momento | Sim |
| 3.4 | Desses, qual é o MAIS importante pra você gostar de uma música? | Múltipla escolha (mesma lista de 3.3) | Letra/mensagem · Melodia · Ritmo/batida · Voz/interpretação do artista · Instrumental/produção · Dá pra dançar · Dá pra treinar · Clima/sonoridade geral · Fama do artista/hit do momento | Sim |
| 3.5 | Como você descreveria seu gosto musical? | Escala linear (1–5) | 1 = "sempre as mesmas bandas/estilos" · 5 = "gosto de descobrir algo novo toda semana" | Sim |
| 3.6 | Você prefere músicas mais... | Escala linear (1–5) | 1 = calmas/acústicas · 5 = agitadas/eletrônicas | Não |
| 3.7 | Você prefere músicas mais... | Escala linear (1–5) | 1 = tristes/melancólicas · 5 = alegres/animadas | Não |
| 3.8 | Você costuma pular músicas com conteúdo explícito (palavrão)? | Múltipla escolha | Sim, sempre / Às vezes / Não, indiferente / Prefiro conteúdo explícito | Não |
| 3.9 | Você prefere faixas curtas (~2–3 min) ou mais longas (5 min+)? | Múltipla escolha | Prefiro curtas / Prefiro longas / Indiferente | Não |
| 3.10 | O que faz você repetir a mesma música várias vezes? (opcional, resposta livre) | Parágrafo | — | Não |

*Por quê:* 3.1 mapeia direto para `track_genre`; 3.2 identifica gênero
âncora por usuário (não existe no dataset — só popularidade agregada por
faixa); 3.3/3.4 cobrem o que o dataset **não** tem (letra, vocal, produção
— o dataset só descreve áudio bruto); 3.6/3.7 são proxies autorreportados
de `energy` e `valence`; 3.8 mapeia `explicit`; 3.9 mapeia `duration_ms`;
3.10 é sinal qualitativo de "repeat listen" (não capturado por
`popularity`, que é agregado entre todos os usuários).

---

## Seção 4 — Descoberta e recomendação

| # | Pergunta | Tipo Google Forms | Opções | Obrigatória |
|---|---|---|---|---|
| 4.1 | Como você geralmente descobre músicas novas? | Caixas de seleção | Recomendações do app (Discover Weekly, Radio, etc.) / Redes sociais / Amigos/família / Rádio tradicional / Trilhas de filmes/séries/jogos / Playlists editoriais | Sim |
| 4.2 | O quanto você confia nas recomendações automáticas do seu app de streaming? | Escala linear (1–5) | 1 = "nunca acerta" · 5 = "sempre acerta" | Sim |
| 4.3 | O que mais te frustra nas recomendações atuais? (resposta aberta, opcional) | Parágrafo | — | Não |
| 4.4 | Você toparia testar uma versão beta do nosso agente de recomendação e dar feedback? | Múltipla escolha | Sim / Não / Talvez | Sim |
| 4.5 | Se sim, deixe seu e-mail para contato (opcional) | Resposta curta | — | Não |

*Por quê:* 4.1–4.3 mapeiam dores reais (dá insumo pro roadmap de
modelagem); 4.4/4.5 recrutam testadores beta sem forçar identificação de
quem não quer.

---

## Notas de implementação no Google Forms

- Perguntas 3.1, 3.3, 2.1 e 2.2 usam **caixas de seleção**: no Forms,
  adicionar a opção "Outro" quando indicado na tabela.
- Escalas lineares (3.5–3.7, 4.2): configurar de 1 a 5, com rótulos de
  texto nos extremos (campo "Rótulo 1" / "Rótulo 5" do Forms).
- 3.4 reusa as mesmas opções de 3.3, mas como **múltipla escolha** (uma
  resposta só) — força o usuário a priorizar em vez de marcar tudo de novo.
- E-mail (4.5) só deve ser pedido *depois* de confirmar interesse em 4.4 —
  usar a opção de seção condicional do Forms ("Ir para a seção com base na
  resposta") se quiser pular 4.5 quando a resposta de 4.4 for "Não".
- Nenhuma pergunta de identificação direta (nome, CPF) — mantém a coleta
  compatível com uso de dados anônimos em projeto acadêmico.
