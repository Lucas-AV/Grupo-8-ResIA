# Roteiro do pitch — 5 minutos

O pitch apresenta o problema, mostra por que o momento de mercado é favorável
e prova que o MelodIA já possui uma base técnica controlável. O foco está no
valor para a pessoa usuária, não nos detalhes de implementação.

## Distribuição das falas

| Pessoa | Parte | Tempo |
| --- | --- | ---: |
| Pessoa 1 | Abertura e fechamento | 45 s |
| Pessoa 2 | Problema | 35 s |
| Pessoa 3 | Mercado | 40 s |
| Pessoa 4 | Experiência proposta | 45 s |
| Pessoa 5 | Segurança da recomendação e dados | 70 s |
| Pessoa 6 | Demonstração ao vivo | 65 s |
| **Total** |  | **300 s** |

Troquem “Pessoa 1” a “Pessoa 6” pelos nomes da equipe antes do primeiro ensaio.

## Slide a slide

### 1. MelodIA — 15 segundos — Pessoa 1

**Objetivo:** apresentar o produto em uma frase.

**Fala sugerida:** “O MelodIA é um agente de recomendação musical. A pessoa
descreve o que quer ouvir em uma conversa simples e recebe músicas reais do
catálogo, com uma explicação curta do resultado.”

**Passagem:** “O ponto de partida foi um problema comum em catálogos grandes.”

### 2. Descobrir ainda dá trabalho — 35 segundos — Pessoa 2

**Objetivo:** tornar o problema reconhecível.

**Fala sugerida:** “Serviços de música oferecem milhares de opções, mas a
descoberta costuma depender de listas prontas e rankings. Quando alguém quer
algo específico, como uma música animada sem conteúdo explícito, precisa
traduzir esse desejo para filtros e telas. O MelodIA reduz esse esforço por
meio da conversa.”

**Passagem:** “Esse problema aparece em um mercado que continua crescendo.”

### 3. O Brasil cresce acima da média — 40 segundos — Pessoa 3

**Objetivo:** apresentar oportunidade sem exagero.

**Fala sugerida:** “O mercado global de música gravada cresceu 6,4% em 2025.
No Brasil, o crescimento foi de 14,1%, mais que o dobro da média global. O país
também avançou do décimo para o oitavo lugar no ranking mundial entre 2023 e
2025. O cenário favorece experiências que ajudem as pessoas a aproveitar
melhor o catálogo que já existe.”

**Passagem:** “Nossa resposta é uma experiência direta.”

### 4. Um pedido vira uma lista explicada — 45 segundos — Pessoa 4

**Objetivo:** mostrar a jornada da pessoa usuária.

**Fala sugerida:** “A pessoa escreve um pedido comum. O sistema identifica
gênero, energia, clima e preferências. Em seguida, consulta o catálogo local e
monta uma lista. O texto final explica a seleção. O login com Spotify é
opcional e pode acrescentar o histórico de escuta, mas a experiência funciona
sem conta conectada.”

**Passagem:** “O ponto mais importante está em como controlamos a resposta.”

### 5. A escolha das faixas fica sob controle — 35 segundos — Pessoa 5

**Objetivo:** explicar confiança sem jargão.

**Fala sugerida:** “O modelo de linguagem ajuda a entender o pedido e a
escrever a resposta. Ele não escolhe músicas livremente. Um motor em Python
seleciona as faixas e uma checagem confirma que o texto só citou itens dessa
lista. Se o modelo falhar, o sistema responde por um modelo de texto simples e
continua funcionando.”

**Passagem:** “Esse motor usa uma base que o grupo conhece e mede.”

### 6. Uma base ampla, com limites conhecidos — 35 segundos — Pessoa 5

**Objetivo:** apresentar evidência e transparência.

**Fala sugerida:** “O conjunto processado reúne 128.830 registros, que
representam 97.534 faixas únicas em 118 gêneros. Existem 31.296 registros
repetidos porque a mesma faixa pode aparecer em mais de um gênero. A análise
preserva essa informação; a recomendação evita repetir a música no resultado.”

**Passagem:** “Agora mostramos o fluxo funcionando.”

### 7. Demonstração ao vivo — 65 segundos — Pessoa 6

**Objetivo:** provar o fluxo principal sem depender de serviços externos.

1. Mostrar a tela já aberta, com o backend pronto.
2. Digitar: **“quero um pagode animado”**.
3. Apontar a resposta e os cards de faixas reais.
4. Mostrar rapidamente diversidade e cobertura, se estiverem visíveis.
5. Explicar: “Esse pedido simples passa pelo roteador e funciona mesmo sem
   modelo de linguagem ou login no Spotify.”

Se a aplicação não responder em dez segundos, interromper a tentativa e exibir
o clipe reserva. Não investigar o erro diante da banca.

**Passagem:** “A demonstração resume o diferencial do projeto.”

### 8. Descoberta com controle e transparência — 30 segundos — Pessoa 1

**Objetivo:** fechar com diferencial e próximo passo.

**Fala sugerida:** “O MelodIA une conversa simples, busca verificável e
medidas de diversidade. O próximo passo é observar interações reais para
melhorar a personalização sem perder transparência. O projeto já reúne dados,
produto, arquitetura e testes para sustentar essa evolução. Obrigado.”

## Plano B do pitch

- Aplicação indisponível: usar o clipe reserva de 45 segundos.
- Vídeo sem áudio: narrar o mesmo passo sobre capturas estáticas.
- LLM indisponível: manter o pedido determinístico e explicar o fallback.
- Tempo abaixo de 4:30: ampliar apenas a explicação do slide 6.
- Tempo acima de 5:00: retirar a frase sobre login Spotify no slide 4.
