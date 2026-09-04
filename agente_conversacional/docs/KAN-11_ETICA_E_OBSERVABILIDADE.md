# KAN-11 — Ética e observabilidade

## O que foi entregue

- Cada turno do chat cria um log curto com o caminho seguido (roteador ou IA),
  resultado das etapas e tempo total. O log não inclui mensagem, sessão, token
  ou informações de conta.
- A tela mostra, abaixo de cada recomendação, quantos gêneros aparecem e qual
  parte da seleção ainda é nova para a conversa. Também explica, em linguagem
  simples, que popularidade é apenas um dos sinais usados no ranking.
- Ao finalizar um login Spotify, o sistema mede a proporção de faixas do
  histórico que encontrou no catálogo local e registra apenas números
  agregados. Se essa etapa falhar, o login continua normalmente, sem
  personalização adicional.

## Como verificar

1. Envie uma recomendação e procure no log uma linha que começa com `turno`.
2. Confira o resumo de gêneros e faixas novas abaixo dos cards retornados.
3. Em um login Spotify com histórico disponível, procure por
   `cobertura_matching_oauth` no log.

## Privacidade

Essas observações foram desenhadas para diagnóstico da demonstração. Elas não
registram texto da conversa, identificador de sessão, token do Spotify, nomes
de faixas ou dados da conta.
