# Spotify API Explorer — Controle de reprodução + Playlist relacionada

**Data:** 2026-09-03
**Branch:** `feature/spotify-playback-control-and-related-playlist` (a partir da `main`)

## Objetivo

Duas features novas, fora do escopo do Jira (confirmado pelo usuário),
que juntas cobrem as **primeiras ações de escrita real** na conta
Spotify do usuário logado — tudo que a ferramenta fez até aqui é
só-leitura:

1. **Controle de reprodução** — play/pause/next/previous/seek/volume/
   shuffle/repeat no dispositivo ativo do usuário, na aba Player (que
   hoje só lê o estado, não age).
2. **Gerar playlist relacionada** — a partir da música tocando agora,
   pede recomendações à Spotify e cria uma playlist privada de verdade
   na conta do usuário com o resultado.

Verificado antes de desenhar (evita repetir o erro de assumir
restrição sem checar): endpoints de controle de reprodução **não**
estão na lista de remoções de nov/2024 nem fev/2026. `POST
/users/{user_id}/playlists` foi removido em fev/2026, mas tem
substituto direto: `POST /me/playlists` (cria pro usuário autenticado,
sem precisar do user id) — é o que usamos aqui.

**Fora de escopo:** botão "tocar essa faixa" em outras abas (só a aba
Player ganha controles), quantidade de faixas configurável na playlist
gerada (fixo em 20), qualquer scope/token que não seja o do usuário já
logado.

## Backend — `spotify_client.call_api` ganha método HTTP configurável

Hoje `call_api` só faz GET. Vira:

```python
def call_api(path, token, params=None, method="GET", json_body=None):
    try:
        response = requests.request(
            method,
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
            json=json_body,
        )
    except requests.exceptions.RequestException as exc:
        return {"error": "connection_error", "error_description": str(exc)}, 502

    if response.status_code == 204:
        return {}, 204

    try:
        body = response.json()
    except ValueError:
        return (
            {"error": "invalid_response", "error_description": "resposta da Spotify não é JSON"},
            response.status_code,
        )

    retry_after = response.headers.get("Retry-After")
    if response.status_code == 429 and retry_after is not None:
        body["retry_after_seconds"] = retry_after
    return body, response.status_code
```

100% retrocompatível — todo call site atual usa só `path`/`token`/
`params`, que continuam funcionando exatamente igual (`method="GET"`
por padrão, `json=None` no `requests.request` equivale a não mandar
corpo).

`_user_data_route` em `app.py` ganha os mesmos dois parâmetros
opcionais, repassados pra `call_api`:

```python
def _user_data_route(path, params=None, method="GET", json_body=None):
    try:
        token = user_auth.get_valid_user_token(
            app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
        )
    except user_auth.NotLoggedInError as exc:
        return jsonify({"error": str(exc)}), 401

    body, status = spotify_client.call_api(path, token, params=params, method=method, json_body=json_body)
    return jsonify(body), status
```

## Backend — escopo OAuth novo

`user_auth.py`'s `SCOPES` ganha `user-modify-playback-state`. Quem já
tiver sessão logada precisa deslogar/logar de novo (mesmo aviso já
documentado no README pra Fase 2).

## Backend — 8 rotas de controle de reprodução

Todas thin wrappers de `_user_data_route`, todas `methods=["POST"]`
no nosso lado (nossa API não precisa espelhar os verbos reais da
Spotify — só precisa disparar o verbo certo pra ela):

```python
    @app.route("/api/me/player/play", methods=["POST"])
    def player_play():
        return _user_data_route("/me/player/play", method="PUT")

    @app.route("/api/me/player/pause", methods=["POST"])
    def player_pause():
        return _user_data_route("/me/player/pause", method="PUT")

    @app.route("/api/me/player/next", methods=["POST"])
    def player_next():
        return _user_data_route("/me/player/next", method="POST")

    @app.route("/api/me/player/previous", methods=["POST"])
    def player_previous():
        return _user_data_route("/me/player/previous", method="POST")

    @app.route("/api/me/player/seek", methods=["POST"])
    def player_seek():
        return _user_data_route(
            "/me/player/seek",
            params={"position_ms": request.args.get("position_ms", "0")},
            method="PUT",
        )

    @app.route("/api/me/player/volume", methods=["POST"])
    def player_volume():
        return _user_data_route(
            "/me/player/volume",
            params={"volume_percent": request.args.get("volume_percent", "50")},
            method="PUT",
        )

    @app.route("/api/me/player/shuffle", methods=["POST"])
    def player_shuffle():
        return _user_data_route(
            "/me/player/shuffle",
            params={"state": request.args.get("state", "false")},
            method="PUT",
        )

    @app.route("/api/me/player/repeat", methods=["POST"])
    def player_repeat():
        return _user_data_route(
            "/me/player/repeat",
            params={"state": request.args.get("state", "off")},
            method="PUT",
        )
```

`/play` e `/pause` não levam corpo — só retomam/pausam o que já está
tocando no dispositivo ativo (não escolhemos dispositivo nem faixa
específica, fora de escopo). Falhas reais da API (sem dispositivo
ativo, conta sem Premium, etc.) passam direto pro frontend como
qualquer outro erro já tratado na ferramenta — sem tratamento especial.

## Backend — 1 rota de orquestração pra playlist relacionada

```python
    @app.route("/api/me/playlists/related", methods=["POST"])
    def create_related_playlist():
        data = request.get_json(silent=True) or {}
        track_id = data.get("track_id")
        track_name = data.get("track_name", "")
        if not track_id:
            return jsonify({"error": "missing_track_id"}), 400

        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        rec_body, rec_status = spotify_client.call_api(
            "/recommendations", token, params={"seed_tracks": track_id, "limit": "20"}
        )
        if rec_status != 200 or not rec_body.get("tracks"):
            return jsonify({"step": "recommendations", "error": rec_body}), rec_status

        uris = [t["uri"] for t in rec_body["tracks"]]
        playlist_name = f"Relacionadas com {track_name} — {date.today().isoformat()}"

        create_body, create_status = spotify_client.call_api(
            "/me/playlists",
            token,
            method="POST",
            json_body={
                "name": playlist_name,
                "public": False,
                "description": "Gerado automaticamente pelo Spotify Explorer",
            },
        )
        if create_status not in (200, 201):
            return jsonify({"step": "create_playlist", "error": create_body}), create_status

        playlist_id = create_body["id"]
        add_body, add_status = spotify_client.call_api(
            f"/playlists/{playlist_id}/items", token, method="POST", json_body={"uris": uris}
        )
        if add_status not in (200, 201):
            return jsonify({"step": "add_items", "playlist": create_body, "error": add_body}), add_status

        return jsonify({"playlist": create_body, "added_tracks": len(uris)}), 200
```

`from datetime import date` novo no topo de `app.py`. Usa `POST
/playlists/{id}/items` (não `/tracks`) — é o nome pós-renomeação de
fev/2026 que a ferramenta já lida no lado de leitura (`PlaylistTab.vue`).
Se `/recommendations` falhar (bem provável — 403 desde nov/2024 pra
apps sem Extended Quota Mode), a rota para ali e devolve o erro real,
**sem criar playlist nenhuma** — evita deixar uma playlist vazia órfã
na conta do usuário.

## Frontend — `PlayerTab.vue` ganha controles

Botões de transporte (⏮ ⏯ ⏭) ao lado do "Atualizar" já existente;
sliders de seek e volume (`<input type="range">`, evento `change` —
só dispara ao soltar, não a cada tick do arrasto); botão de shuffle
(toggle); botão de repeat (cicla `off → context → track → off`).
Cada controle chama seu endpoint e, no sucesso, dispara **um**
`fetchPlayer()` automático em seguida (não polling — só essa vez, pra
refletir o resultado da ação).

```js
async function callControl(path, params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `/api/me/player/${path}?${query}` : `/api/me/player/${path}`;
  await fetchJSON(url, { method: "POST" });
  await fetchPlayer();
}
```

Play/pause reutiliza `nowPlaying`/`result.data.player.is_playing` pra
decidir qual dos dois chamar. Seek lê o valor final do slider em
`position_ms` (calculado a partir da duração da faixa atual e da
posição percentual do slider). Volume manda `volume_percent`
diretamente (0-100). Shuffle manda `state=true|false` (string, como a
API espera). Repeat cicla local e manda o próximo estado.

## Frontend — botão "Gerar playlist relacionada"

No bloco de "tocando agora" da aba Player, ao lado do
`TrackPreview`. Desabilitado se `nowPlaying` for nulo. Ao clicar,
chama `POST /api/me/playlists/related` com `{track_id: nowPlaying.id,
track_name: nowPlaying.name}`. Sucesso: mostra link "Abrir playlist no
Spotify" (`external_urls.spotify` do objeto `playlist` retornado) e
"N faixas adicionadas". Erro: mostra o corpo real do erro (mesmo
padrão de exibição de erro já usado no resto da ferramenta) — inclui
o `step` em que falhou pra facilitar diagnóstico manual.

## Testes

Backend: rotas novas ganham testes reais em `pytest` (mockado, mesmo
padrão das rotas já existentes) — inclui um teste da rota de
orquestração cobrindo o caminho feliz e o caminho "recommendations
falha, não cria playlist". Frontend: sem suíte JS (convenção já
estabelecida), `npm run build` + smoke test manual — esse smoke test
precisa ser contra a conta/dispositivo reais do usuário, já que é a
primeira feature que escreve de verdade.
