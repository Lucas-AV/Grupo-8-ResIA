# Spotify API Explorer

Dev tool interna do Grupo 8 pra explorar a Web API do Spotify: quais
endpoints existem, quais dados retornam, e quais restrições reais existem
hoje. Não faz parte do produto final — ver
`docs/superpowers/specs/2026-09-01-spotify-api-explorer-design.md` pro
design completo.

## Setup

1. Crie um app em https://developer.spotify.com/dashboard
2. Em "Redirect URIs" do app, adicione `http://127.0.0.1:5000/callback`
   (necessário mesmo se você só for usar as abas de catálogo, sem login)
3. Copie `.env.example` para `.env` dentro de `spotify_explorer/` e
   preencha `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` com os do seu
   app. Gere um valor aleatório para `FLASK_SECRET_KEY` (ex:
   `python -c "import secrets; print(secrets.token_hex(32))"`)
4. Instale as dependências:
   ```
   pip install -r requirements.txt -r spotify_explorer/requirements.txt
   ```
5. Rode:
   ```
   cd spotify_explorer
   python app.py
   ```
6. Abra `http://127.0.0.1:5000`

## Rodando os testes

```
cd spotify_explorer
pytest
```

Todos os testes usam `requests` mockado — nenhum bate na API real, então
não precisam de credenciais.

## O que cada aba faz

- **Search** — `GET /search` do catálogo (track/artist/album)
- **Track & Audio** — `GET /tracks/{id}`, `/audio-features/{id}`,
  `/audio-analysis/{id}`
- **Artist** — `GET /artists/{id}` + top-tracks + albums + related-artists
- **Recommendations** — `GET /recommendations` com seeds e parâmetros alvo
- **Meus dados** — requer login (Authorization Code Flow): top
  tracks/artists por `time_range`, faixas curtidas, tocadas recentemente

## Restrições conhecidas da API (não são bugs da ferramenta)

Desde nov/2024 apps novos sem "Extended Quota Mode" recebem 403 em
`audio-features`, `audio-analysis`, `recommendations` e
`related-artists`. A ferramenta mostra esse 403 como veio — é justamente
o dado que o grupo quer descobrir.

`/me/player/recently-played` devolve no máximo as últimas 50 faixas
tocadas — não é um histórico de 6 meses. Pra "mais ouvidas nos últimos ~6
meses", use a aba Meus dados com `time_range=medium_term`, que é um
ranking por frequência calculado pela Spotify, não uma lista cronológica.

## Checklist de smoke test manual

- [ ] App sobe sem `.env` preenchido e mostra o aviso de credenciais faltando
- [ ] Search retorna resultados reais pra uma query conhecida
- [ ] Track & Audio retorna a track; audio-features/audio-analysis
      retornam dado ou 403 (dependendo do nível de acesso do seu app)
- [ ] Artist retorna os 4 blocos de dados
- [ ] Recommendations retorna tracks (ou 403, mesma observação acima)
- [ ] Login funciona e volta pra `/` autenticado
- [ ] Top tracks/artists funciona nas 3 janelas de tempo
- [ ] Faixas curtidas e tocadas recentemente retornam dado real
- [ ] Logout funciona e volta ao estado deslogado
