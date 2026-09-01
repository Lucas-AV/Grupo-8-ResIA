# Fluxo dos agentes

1. O Orquestrador recebe mensagem e estado resumido.
2. Classifica a intenção e seleciona as ferramentas necessárias.
3. Coleta Spotify fornece apenas sinais autorizados.
4. ETL aplica os mesmos contratos e normalizações do treinamento.
5. Clustering consulta artefatos do núcleo ML e produz um perfil interpretável.
6. O futuro recomendador filtra conhecidas, rejeitadas, curtidas e já exibidas antes do ranking.
7. Conversacional apresenta fatos e explicações, sem inventar músicas.
8. Confiança/HITL avalia a saída completa.
9. Abaixo de 90%, a saída fica bloqueada e um caso é registrado.

TODO(Fases 2–4): implementar os passos sem voltar a concentrar tudo no frontend.

