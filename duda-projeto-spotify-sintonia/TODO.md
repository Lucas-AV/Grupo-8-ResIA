# Pendências por fase

Este arquivo registra trabalho futuro sem manter o código quebrado da versão antiga dentro dos módulos ativos.

## Fase 1 — Dados e notebook

- [ ] Baixar e validar o Spotify Tracks Dataset oficial do Kaggle.
- [ ] Implementar ETL reproduzível e salvar metadados de processamento.
- [ ] Executar EDA, hipóteses e plots no notebook obrigatório.
- [ ] Tratar duplicidades de `track_id` associadas a múltiplos gêneros.

## Fase 2 — Clustering e recomendação

- [ ] Treinar e comparar clustering de faixas por atributos de áudio.
- [ ] Nomear os clusters com perfis interpretáveis.
- [ ] Classificar o perfil do usuário nos clusters.
- [ ] Reescrever o recomendador; a busca textual determinística antiga foi rejeitada por repetir resultados.
- [ ] Calibrar afinidade, novidade, diversidade e confiança separadamente.

## Fase 3 — Chatbot e Spotify

- [ ] Implementar o Orquestrador e o agente Conversacional com memória estruturada.
- [ ] Reescrever a coleta Spotify com paginação e proveniência dos sinais.
- [ ] Impedir músicas conhecidas, rejeitadas, curtidas ou já exibidas de voltarem indevidamente.
- [ ] Integrar o frontend ao backend sem colocar regras de negócio no React.

## Fase 4 — Confiança, revisão e QA

- [ ] Aplicar o limiar de 90% a toda resposta, insight, explicação e recomendação.
- [ ] Completar o ciclo humano: revisar, corrigir, devolver e registrar aprendizado.
- [ ] Criar testes de repetição, novidade, diálogo multivolta, confiança e regressão.

