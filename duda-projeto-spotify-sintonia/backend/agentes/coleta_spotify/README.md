# Agente de coleta Spotify

`coletar_sinais_spotify` é a porta de entrada para o restante do backend obter um `ColetaSpotify` estruturado. Ela seleciona o cliente real ou demo, preserva a origem de cada atributo e devolve perfil, top tracks e top artists.

O agente não recomenda músicas e não decide cluster: essas responsabilidades serão ligadas aos módulos de clustering e orquestração nas fases seguintes. Ao gerar recomendações, a lista de `track_id` coletada deverá alimentar o filtro de novidade para impedir faixas já conhecidas.
