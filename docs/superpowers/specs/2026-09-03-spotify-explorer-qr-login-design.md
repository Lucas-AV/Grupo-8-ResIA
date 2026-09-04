# Spotify Explorer — Login via QR code (pareamento cross-device)

**Data:** 2026-09-03
**Branch:** `feature/spotify-explorer-qr-login` (a partir da `main`)

## Objetivo

`spotify_explorer` hoje é um dev tool local single-user: quem abre o
navegador clica em "Conectar Spotify" e autoriza no mesmo dispositivo,
com os tokens guardados na sessão Flask (cookie) daquele navegador.

Cenário real que motiva essa feature: **demo/kiosk** — o dev tool
rodando numa tela compartilhada (PC ou TV numa demonstração), e cada
pessoa que for explorar escaneia um QR code com o próprio celular pra
autorizar com a própria conta Spotify, sem digitar nada no dispositivo
compartilhado. A tela destrava sozinha assim que alguém autoriza.

**Fora de escopo:** contas de usuário persistentes/multiusuário (a
tela continua sendo "uma sessão logada por vez", só muda *como* ela é
autorizada); qualquer mudança em `agente_conversacional` (é um app
totalmente separado, mesmo já tendo um padrão parecido — ver
"Prior art" abaixo); resolver alcance fora da rede local (sem
ngrok/túnel embutido — documentado como pré-requisito, não resolvido
em código).

## Prior art no próprio repo

`agente_conversacional/spotify_auth/` já resolve um problema parecido
(login Spotify correlacionado por um id, com polling de status):
`PendingAuth` (correlaciona `state` do PKCE com `session_id`) e
`SessionStore._purge_expired_locked` (purga preguiçosa por TTL). Essa
feature reaproveita esses padrões — não o código em si (são apps
Flask vs. FastAPI diferentes), mas a forma: um "relay" efêmero em
memória, chave aleatória (`secrets.token_urlsafe`), TTL curto,
purge preguiçosa no read.

## Arquitetura

```
Kiosk (navegador A)                         Celular (navegador B)
      |                                              |
      | GET /login/qr                                |
      |--------------------------------------------->|
      | <- HTML com QR (SVG) + poll loop              |
      |                                              |
      |                          escaneia o QR
      |                                              |
      |                                   GET /login?pair=<code>
      |                                              |
      |                          <- redirect pro Spotify (fluxo
      |                             OAuth existente, inalterado)
      |                                              |
      |                          autoriza no Spotify
      |                                              |
      |                                   GET /callback?code=...&state=...
      |                                              |
      |                          exchange_code() (existente) +
      |                          relay pro PairingStore (novo)
      |                                              |
      | GET /api/pair/<code>/status (poll a cada ~2s) |
      | <- {"status": "completed"}                    |
      | (essa resposta já grava os tokens na sessão   |
      |  do kiosk e consome o código)                 |
      |                                              |
      | JS redireciona pro app normal (FRONTEND_URL)  |
```

O ponto central: o `PairingStore` é só um **relay efêmero e de uso
único**. Assim que o poll do kiosk consome o código, os tokens já
estão na sessão Flask normal do kiosk — dali em diante,
`get_valid_user_token`, `/api/me`, etc. funcionam exatamente como
funcionam hoje, sem saber que existe QR code. Isso mantém o blast
radius pequeno: `user_auth.py` ganha uma função utilitária nova
(reaproveitada por dois call sites), mas nada do fluxo de token
existente muda de comportamento.

## `pairing_store.py` (novo módulo)

```python
import secrets
import threading
import time

_TTL_SECONDS = 5 * 60


class PairingStore:
    def __init__(self, clock=time.time):
        self._clock = clock
        self._lock = threading.RLock()
        self._entries = {}  # code -> {"created_at": float, "tokens": dict | None}

    def create(self):
        with self._lock:
            self._purge_expired_locked()
            code = secrets.token_urlsafe(16)
            self._entries[code] = {"created_at": self._clock(), "tokens": None}
            return code

    def get_status(self, code):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is None:
                return "not_found"
            return "completed" if entry["tokens"] is not None else "pending"

    def mark_completed(self, code, tokens):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is not None:
                entry["tokens"] = tokens

    def consume(self, code):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is None or entry["tokens"] is None:
                return None
            del self._entries[code]
            return entry["tokens"]

    def _purge_expired_locked(self):
        now = self._clock()
        expired = [c for c, e in self._entries.items() if now - e["created_at"] >= _TTL_SECONDS]
        for c in expired:
            del self._entries[c]
```

`mark_completed` em código desconhecido/expirado é um no-op de
propósito — se o celular demorar demais e o código expirar entre o
`/login?pair=` e o `/callback`, o relay simplesmente não acontece; o
QR do kiosk já vai ter se renovado sozinho (client-side, ao detectar
`expired`) e a pessoa escaneia de novo.

Instância única em `app.py`, module-level dentro de `register_routes`
(mesmo padrão de `_pending_auth`/`_token_store` em
`agente_conversacional`), não precisa ser injetável — é um dev tool
local, sem múltiplos workers.

## `user_auth.py` — extrair `_store_tokens_in_session`

Hoje `exchange_code` grava direto na sessão:

```python
session["user_access_token"] = payload["access_token"]
session["user_refresh_token"] = payload["refresh_token"]
session["user_token_expires_at"] = time.time() + payload["expires_in"] - 30
```

Extrai isso pra uma função reaproveitável, chamada tanto por
`exchange_code` (sessão do próprio celular, comportamento inalterado)
quanto pelo novo endpoint de status (sessão do kiosk, gravando um
payload vindo do `PairingStore` em vez de vindo direto da Spotify):

```python
def apply_tokens_to_session(payload):
    session["user_access_token"] = payload["access_token"]
    session["user_refresh_token"] = payload["refresh_token"]
    session["user_token_expires_at"] = payload["expires_at"]
```

Nota: `exchange_code` hoje calcula `expires_at` inline
(`time.time() + payload["expires_in"] - 30`) a partir do payload cru
da Spotify (`expires_in`, segundos relativos). Pra reaproveitar a
mesma função nos dois call sites, `exchange_code` passa a computar
`expires_at` **antes** de chamar `apply_tokens_to_session`, e é esse
valor absoluto (`expires_at`) — não o `expires_in` relativo da
Spotify — que fica guardado no `PairingStore` e é repassado pro
kiosk. Isso evita literalmente recalcular "daqui a X segundos" duas
vezes (uma vez no exchange, outra no relay) com um deslocamento de
tempo entre elas.

`exchange_code` também passa a **retornar** o payload
(`{"access_token", "refresh_token", "expires_at"}`) em vez de só
gravar na sessão e retornar `None` — mudança de contrato, mas o
único call site existente (`/callback` em `app.py`) ignora o valor de
retorno hoje, então isso não quebra nada; só passa a ser usável pelo
novo código em `/callback`.

## `app.py` — rotas novas/alteradas

`pairing_store = PairingStore()` instanciado uma vez dentro de
`register_routes(app)`, mesmo lugar/padrão de `_pending_auth`/
`_token_store` em `agente_conversacional`. `render_qr_page` e
`render_pair_error_page` vivem no novo módulo `qr_page.py` (mesmo
papel que `consent.py` tem em `agente_conversacional`) e são
importadas em `app.py`.

```python
    @app.route("/login/qr")
    def login_qr():
        code = pairing_store.create()
        pair_url = f"{request.host_url}login?pair={code}"
        svg = segno.make(pair_url).svg_data_uri(scale=6)
        return render_qr_page(svg, code)  # helper em novo módulo qr_page.py, HTML inline (mesmo estilo de consent.py do agente_conversacional)

    @app.route("/login")
    def login():
        pair_code = request.args.get("pair")
        if pair_code is not None:
            status = pairing_store.get_status(pair_code)
            if status != "pending":
                return render_pair_error_page(status), 400
            session["pairing_code"] = pair_code
        return redirect(
            user_auth.get_login_url(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_REDIRECT_URI"]
            )
        )

    @app.route("/callback")
    def callback():
        error = request.args.get("error")
        if error:
            return redirect(f"{app.config['FRONTEND_URL']}?{urlencode({'auth_error': error})}")

        try:
            tokens = user_auth.exchange_code(
                request.args.get("code"),
                request.args.get("state"),
                app.config["SPOTIFY_CLIENT_ID"],
                app.config["SPOTIFY_CLIENT_SECRET"],
                app.config["SPOTIFY_REDIRECT_URI"],
            )
        except ValueError as exc:
            return redirect(f"{app.config['FRONTEND_URL']}?{urlencode({'auth_error': str(exc)})}")

        pair_code = session.pop("pairing_code", None)
        if pair_code is not None:
            pairing_store.mark_completed(pair_code, tokens)

        return redirect(app.config["FRONTEND_URL"])

    @app.route("/api/pair/<code>/status")
    def pair_status(code):
        status = pairing_store.get_status(code)
        if status != "completed":
            return jsonify({"status": status})
        tokens = pairing_store.consume(code)
        user_auth.apply_tokens_to_session(tokens)
        return jsonify({"status": "completed"})
```

`request.host_url` dentro de `/login/qr` reflete o host que o
**kiosk** usou pra abrir essa página (ex.: `http://192.168.1.50:5000/`
se foi aberta pelo IP de rede local) — é esse mesmo endereço que o QR
codifica, então o celular só consegue escanear e completar se
estiver na mesma rede. Isso é intencional e documentado como
pré-requisito no README, não resolvido em código (sem ngrok/túnel).

## Página `/login/qr` (HTML inline, novo módulo `qr_page.py`)

Mesmo estilo de `agente_conversacional/spotify_auth/consent.py`: uma
função Python que retorna uma string HTML, sem template engine nova.
Contém: o SVG do QR embutido inline, texto "Escaneie pra conectar",
um poll em JS puro (`fetch` a cada ~2s em
`/api/pair/<code>/status`), e client-side:
- `completed` → `window.location.href = FRONTEND_URL` (valor
  embutido no HTML no momento do render, igual o resto do app já faz
  com `FRONTEND_URL`)
- `expired`/`not_found` → recarrega a própria página
  (`window.location.reload()`), que gera um código novo do zero —
  implementa o "expira em 5 min, gera novo sozinho" sem precisar de
  lógica extra de retry no JS

Não faz parte da SPA Vue — é uma rota Flask simples, igual `/login` e
`/callback` já são hoje.

## Nova dependência

`segno` (`>=1.6,<2`) — geração de QR code em Python puro, sem Pillow/
extensão C. Gera SVG diretamente (`svg_data_uri`), sem precisar
salvar arquivo em disco nem servir uma rota de imagem separada — o
SVG vai embutido inline no HTML de `/login/qr`.

## Segurança

- Código de pareamento: `secrets.token_urlsafe(16)`, mesma entropia
  já usada pro `oauth_state` existente.
- Uso único: `consume()` remove a entrada após o kiosk ler
  `completed` — um QR fotografado/reaproveitado depois não funciona
  mais (segunda leitura cai em `not_found`).
- TTL de 5 min, checado de forma preguiçosa (mesmo padrão de
  `agente_conversacional`), sem thread/cron de limpeza.
- `/login?pair=<inválido/expirado>` nunca chega a redirecionar pro
  Spotify — mostra erro local na hora.
- Nenhum dado novo sensível: o `PairingStore` guarda os mesmos
  access/refresh tokens que a sessão Flask já guarda hoje, só que por
  até 5 minutos e em memória (perdido no restart, mesma postura
  "sem persistência" do resto da ferramenta).
- O fluxo OAuth do celular em si (consentimento Spotify, CSRF via
  `state`) é o mesmo de sempre — pareamento só adiciona um relay
  paralelo pro *resultado*, não muda como o celular se autentica.

## Testes

Backend ganha testes reais em `pytest`, seguindo o padrão já
estabelecido no projeto:

- `pairing_store.py`: testes unitários diretos (create/pending/
  completed/consume/expira via clock injetável, mesmo truque de
  `clock` já usado em `SessionStore` do `agente_conversacional`)
- `GET /login/qr`: 200, corpo contém um SVG, cria uma entrada pending
  no store
- `GET /login?pair=<válido>`: redireciona pro Spotify igual `/login`
  sem `pair`, e grava `pairing_code` na sessão
- `GET /login?pair=<inválido/expirado>`: não redireciona pro Spotify,
  mostra página de erro
- `GET /callback` com `pairing_code` na sessão (mock de
  `exchange_code`): relay chega no `PairingStore` (`get_status` vira
  `completed`)
- `GET /callback` sem `pairing_code` na sessão: comportamento
  idêntico ao de hoje, sem tocar no `PairingStore`
- `GET /api/pair/<code>/status`: pending → completed (grava sessão do
  chamador, `/api/me` funciona em seguida) → segunda chamada no mesmo
  código vira `not_found`

Frontend: nenhuma mudança na SPA Vue (a página QR é Flask puro) — sem
testes JS novos, verificação é `npm run build` continuar passando
(garantia de que nada quebrou) mais um item novo no checklist de
smoke test manual do README, incluindo o teste real com celular na
mesma rede.
