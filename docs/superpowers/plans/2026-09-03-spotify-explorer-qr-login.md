# Spotify Explorer — Login via QR code Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a kiosk/demo screen running `spotify_explorer` show a QR code that a visitor scans with their own phone to authorize their own Spotify account — the kiosk screen polls and logs itself in automatically once the phone completes the OAuth flow, with zero typing on the shared device.

**Architecture:** A new short-lived, one-shot `PairingStore` (in-memory, TTL 5 min) relays tokens from whichever device completes the OAuth flow (the phone) to whichever device is polling a pairing code (the kiosk). Once the kiosk's poll consumes a completed entry, tokens land in the kiosk's normal Flask session exactly the way they do today — the pairing mechanism is a temporary side-channel, not a replacement for the existing session-cookie-based auth. The existing single-device `/login` flow is untouched when no `pair` param is present.

**Tech Stack:** Flask (backend, unchanged framework), `segno` (new dependency — pure-Python QR code generation, SVG data URI, no Pillow). No frontend/Vue changes — the QR page is plain server-rendered HTML, matching how `/login`/`/callback` already work today.

---

## Task 1: `PairingStore`

**Files:**
- Create: `spotify_explorer/pairing_store.py`
- Test: `spotify_explorer/test_pairing_store.py`

- [ ] **Step 1: Write the failing tests**

Create `spotify_explorer/test_pairing_store.py`:

```python
from pairing_store import PairingStore


def test_create_returns_a_pending_code():
    store = PairingStore()
    code = store.create()
    assert store.get_status(code) == "pending"


def test_unknown_code_is_not_found():
    store = PairingStore()
    assert store.get_status("nope") == "not_found"


def test_mark_completed_then_status_is_completed():
    store = PairingStore()
    code = store.create()
    store.mark_completed(code, {"access_token": "at"})
    assert store.get_status(code) == "completed"


def test_mark_completed_on_unknown_code_is_a_no_op():
    store = PairingStore()
    store.mark_completed("nope", {"access_token": "at"})
    assert store.get_status("nope") == "not_found"


def test_consume_returns_tokens_and_removes_entry():
    store = PairingStore()
    code = store.create()
    store.mark_completed(code, {"access_token": "at"})

    tokens = store.consume(code)

    assert tokens == {"access_token": "at"}
    assert store.get_status(code) == "not_found"


def test_consume_on_pending_code_returns_none_and_keeps_entry():
    store = PairingStore()
    code = store.create()

    tokens = store.consume(code)

    assert tokens is None
    assert store.get_status(code) == "pending"


def test_consume_on_unknown_code_returns_none():
    store = PairingStore()
    assert store.consume("nope") is None


def test_entry_expires_after_ttl():
    fake_time = [1000.0]
    store = PairingStore(clock=lambda: fake_time[0])
    code = store.create()

    fake_time[0] += 5 * 60

    assert store.get_status(code) == "not_found"


def test_entry_still_valid_just_before_ttl():
    fake_time = [1000.0]
    store = PairingStore(clock=lambda: fake_time[0])
    code = store.create()

    fake_time[0] += 5 * 60 - 1

    assert store.get_status(code) == "pending"


def test_codes_are_unique_and_url_safe():
    store = PairingStore()
    code1 = store.create()
    code2 = store.create()
    assert code1 != code2
    assert len(code1) > 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_pairing_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pairing_store'`

- [ ] **Step 3: Implement**

Create `spotify_explorer/pairing_store.py`:

```python
import secrets
import threading
import time

_TTL_SECONDS = 5 * 60


class PairingStore:
    """Relay efêmero e de uso único: correlaciona um código de pareamento
    (mostrado como QR num dispositivo) com os tokens que outro dispositivo
    produz ao completar o OAuth. TTL curto, purge preguiçosa no read —
    mesmo padrão de agente_conversacional/sessions/store.py."""

    def __init__(self, clock=time.time):
        self._clock = clock
        self._lock = threading.RLock()
        self._entries = {}

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

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_pairing_store.py -v`
Expected: PASS — all 10 tests

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/pairing_store.py spotify_explorer/test_pairing_store.py
git commit -m "feat: add PairingStore for QR-code login pairing"
```

---

## Task 2: `user_auth.py` — extract `apply_tokens_to_session`, `exchange_code` returns tokens

**Files:**
- Modify: `spotify_explorer/user_auth.py:47-84`
- Test: `spotify_explorer/test_user_auth.py`

- [ ] **Step 1: Write the failing test**

Append to `spotify_explorer/test_user_auth.py`:

```python
@patch("user_auth.requests.post")
def test_exchange_code_returns_the_token_payload(mock_post, app):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    with app.test_request_context():
        session["oauth_state"] = "abc"

        tokens = user_auth.exchange_code(
            "code123", "abc", "client-id", "client-secret",
            "http://127.0.0.1:5000/callback",
        )

        assert tokens["access_token"] == "at"
        assert tokens["refresh_token"] == "rt"
        assert isinstance(tokens["expires_at"], float)


def test_apply_tokens_to_session_writes_all_three_keys(app):
    with app.test_request_context():
        user_auth.apply_tokens_to_session(
            {"access_token": "at2", "refresh_token": "rt2", "expires_at": 12345.0}
        )

        assert session["user_access_token"] == "at2"
        assert session["user_refresh_token"] == "rt2"
        assert session["user_token_expires_at"] == 12345.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_user_auth.py -k "returns_the_token_payload or apply_tokens_to_session" -v`
Expected: FAIL — `exchange_code` returns `None` (no `tokens[...]` to index), `apply_tokens_to_session` doesn't exist (`AttributeError`)

- [ ] **Step 3: Implement**

In `spotify_explorer/user_auth.py`, replace lines 47-84 (the whole `exchange_code` function body from the `def` line through the final `session[...]` assignments):

```python
def apply_tokens_to_session(tokens):
    session["user_access_token"] = tokens["access_token"]
    session["user_refresh_token"] = tokens["refresh_token"]
    session["user_token_expires_at"] = tokens["expires_at"]


def exchange_code(code, state, client_id, client_secret, redirect_uri):
    if state != session.get("oauth_state"):
        raise ValueError("state inválido — possível CSRF, tente logar novamente")

    try:
        response = requests.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {_basic_auth_header(client_id, client_secret)}"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
    except requests.exceptions.RequestException as exc:
        raise CodeExchangeError({"error": "connection_error", "error_description": str(exc)}, 502)

    if response.status_code != 200:
        try:
            error_body = response.json()
        except ValueError:
            error_body = {
                "error": "invalid_response",
                "error_description": "resposta da Spotify não é JSON",
            }
        raise CodeExchangeError(error_body, response.status_code)

    try:
        payload = response.json()
    except ValueError:
        raise CodeExchangeError(
            {"error": "invalid_response", "error_description": "resposta da Spotify não é JSON"},
            response.status_code,
        )

    tokens = {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "expires_at": time.time() + payload["expires_in"] - 30,
    }
    apply_tokens_to_session(tokens)
    return tokens
```

Everything except the final three lines (previously three direct `session[...]` writes, now built into a `tokens` dict, applied via `apply_tokens_to_session`, and returned) is byte-identical to what's there today — this is why every existing `exchange_code` test (state mismatch, connection error, non-200, non-JSON body) keeps passing unchanged: none of them inspect the return value, and the CSRF/error-handling logic isn't touched.

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new. `test_exchange_code_stores_tokens_in_session` (pre-existing) must still pass unmodified — it only checks `session["user_access_token"]`/`session["user_refresh_token"]`, which `apply_tokens_to_session` still sets identically.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/user_auth.py spotify_explorer/test_user_auth.py
git commit -m "feat: extract apply_tokens_to_session, have exchange_code return its tokens"
```

---

## Task 3: `qr_page.py` — HTML renderers

**Files:**
- Create: `spotify_explorer/qr_page.py`
- Test: `spotify_explorer/test_qr_page.py`

- [ ] **Step 1: Write the failing tests**

Create `spotify_explorer/test_qr_page.py`:

```python
import qr_page


def test_render_qr_page_embeds_svg_code_and_frontend_url():
    html = qr_page.render_qr_page("data:image/svg+xml;base64,AAA", "code123", "http://example.com/")

    assert "data:image/svg+xml;base64,AAA" in html
    assert 'const code = "code123";' in html
    assert 'const frontendUrl = "http://example.com/";' in html
    assert "/api/pair/${code}/status" in html


def test_render_qr_page_redirects_to_frontend_on_completed():
    html = qr_page.render_qr_page("data:x", "code123", "http://example.com/")

    assert 'data.status === "completed"' in html
    assert "window.location.href = frontendUrl" in html


def test_render_qr_page_reloads_on_expired_or_not_found():
    html = qr_page.render_qr_page("data:x", "code123", "http://example.com/")

    assert 'data.status === "expired"' in html
    assert 'data.status === "not_found"' in html
    assert "window.location.reload()" in html


def test_render_pair_error_page_for_expired():
    html = qr_page.render_pair_error_page("expired")

    assert "expirou" in html
    assert '<a href="/login/qr">' in html


def test_render_pair_error_page_for_not_found():
    html = qr_page.render_pair_error_page("not_found")

    assert "não é válido" in html


def test_render_pair_error_page_for_unknown_status_has_generic_message():
    html = qr_page.render_pair_error_page("weird_status")

    assert "Não foi possível continuar" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_qr_page.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qr_page'`

- [ ] **Step 3: Implement**

Create `spotify_explorer/qr_page.py`:

```python
def render_qr_page(svg_data_uri, code, frontend_url):
    return f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Conectar com Spotify (QR)</title></head>
<body>
<h1>Escaneie pra conectar</h1>
<img src="{svg_data_uri}" alt="QR code para login com Spotify" width="300" height="300">
<p id="status">Aguardando alguém escanear...</p>
<script>
const code = "{code}";
const frontendUrl = "{frontend_url}";

async function poll() {{
  const response = await fetch(`/api/pair/${{code}}/status`);
  const data = await response.json();
  if (data.status === "completed") {{
    window.location.href = frontendUrl;
    return;
  }}
  if (data.status === "expired" || data.status === "not_found") {{
    window.location.reload();
    return;
  }}
  setTimeout(poll, 2000);
}}

poll();
</script>
</body>
</html>"""


def render_pair_error_page(status):
    mensagens = {
        "expired": "Esse QR code expirou. Peça um novo.",
        "not_found": "Esse QR code não é válido. Peça um novo.",
    }
    mensagem = mensagens.get(status, "Não foi possível continuar com esse QR code.")
    return f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>QR code inválido</title></head>
<body>
<h1>{mensagem}</h1>
<p><a href="/login/qr">Gerar novo QR code</a></p>
</body>
</html>"""
```

`code` only ever contains URL-safe base64 characters (from `secrets.token_urlsafe`) and `frontend_url` comes from server config, not user input — neither can contain a `"` that would break out of the JS string literals, so no escaping is needed here.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_qr_page.py -v`
Expected: PASS — all 6 tests

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/qr_page.py spotify_explorer/test_qr_page.py
git commit -m "feat: add qr_page HTML renderers for the QR login page and pairing errors"
```

---

## Task 4: `GET /login/qr` route

**Files:**
- Modify: `spotify_explorer/app.py` (imports, `register_routes` setup, new route before `/login`)
- Modify: `spotify_explorer/requirements.txt`
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Add the new dependency**

In `spotify_explorer/requirements.txt`, add:

```
segno>=1.6,<2
```

Run: `pip install segno` (or `pip install -r spotify_explorer/requirements.txt`) so the import in Step 3 works locally.

- [ ] **Step 2: Write the failing tests**

Add near the top of `spotify_explorer/test_app_auth.py` (it needs `re` — add `import re` as the first line of the file, above the existing `import app as app_module`):

```python
def test_login_qr_returns_html_with_qr_and_poll_code(client):
    response = client.get("/login/qr")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "data:image/svg+xml" in body
    assert "/api/pair/" in body

    match = re.search(r'const code = "([^"]+)"', body)
    assert match is not None
    assert len(match.group(1)) > 10


def test_login_qr_generates_a_fresh_code_each_time(client):
    first = client.get("/login/qr").get_data(as_text=True)
    second = client.get("/login/qr").get_data(as_text=True)

    first_code = re.search(r'const code = "([^"]+)"', first).group(1)
    second_code = re.search(r'const code = "([^"]+)"', second).group(1)

    assert first_code != second_code
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "login_qr" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 4: Implement**

In `spotify_explorer/app.py`, add these imports right after `import user_auth` (line 9):

```python
import segno

import pairing_store
import qr_page
```

At the very top of `register_routes(app)` (right after the `def register_routes(app):` line, before the first `@app.route`), add:

```python
    pairing = pairing_store.PairingStore()
```

(Named `pairing`, not `pairing_store`, to avoid shadowing the module import of the same name.)

Then add the new route right before the existing `@app.route("/login")` (line 164):

```python
    @app.route("/login/qr")
    def login_qr():
        code = pairing.create()
        pair_url = f"{request.host_url}login?pair={code}"
        svg_data_uri = segno.make(pair_url).svg_data_uri(scale=6)
        return qr_page.render_qr_page(svg_data_uri, code, app.config["FRONTEND_URL"])
```

- [ ] **Step 5: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new

- [ ] **Step 6: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/requirements.txt spotify_explorer/test_app_auth.py
git commit -m "feat: add GET /login/qr route showing a scannable pairing QR code"
```

---

## Task 5: `GET /login` gains `?pair=` support

**Files:**
- Modify: `spotify_explorer/app.py:164-170` (the `login()` route)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
def test_login_with_valid_pair_code_stashes_it_in_session_and_redirects_to_spotify(client):
    qr_response = client.get("/login/qr")
    code = re.search(r'const code = "([^"]+)"', qr_response.get_data(as_text=True)).group(1)

    response = client.get(f"/login?pair={code}")

    assert response.status_code == 302
    assert response.location.startswith("https://accounts.spotify.com/authorize")
    with client.session_transaction() as sess:
        assert sess["pairing_code"] == code


def test_login_with_unknown_pair_code_shows_error_without_redirecting_to_spotify(client):
    response = client.get("/login?pair=does-not-exist")

    assert response.status_code == 400
    assert b"login/qr" in response.data


def test_login_without_pair_param_behaves_exactly_like_before(client):
    response = client.get("/login")

    assert response.status_code == 302
    assert response.location.startswith("https://accounts.spotify.com/authorize")
    with client.session_transaction() as sess:
        assert "pairing_code" not in sess
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "test_login_with or test_login_without" -v`
Expected: FAIL — `pair` param is currently ignored entirely, so the "unknown pair code" test gets a 302 instead of 400, and the "valid pair code" test's session assertion fails (`pairing_code` never gets set)

- [ ] **Step 3: Implement**

In `spotify_explorer/app.py`, add `session` to the existing Flask import line (line 6):

```python
from flask import Flask, jsonify, redirect, request, send_from_directory, session
```

Then replace the `login()` route (lines 164-170):

```python
    @app.route("/login")
    def login():
        pair_code = request.args.get("pair")
        if pair_code is not None:
            status = pairing.get_status(pair_code)
            if status != "pending":
                return qr_page.render_pair_error_page(status), 400
            session["pairing_code"] = pair_code
        return redirect(
            user_auth.get_login_url(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_REDIRECT_URI"]
            )
        )
```

When `pair` is absent (the existing, unpaired flow), this is byte-identical to the current route — the `if pair_code is not None` block is simply skipped.

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new. `test_login_redirects_to_spotify_authorize` (pre-existing, no `pair` param) must still pass unmodified.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add ?pair= support to GET /login"
```

---

## Task 6: `GET /api/pair/<code>/status` route

**Files:**
- Modify: `spotify_explorer/app.py` (new route)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
def test_pair_status_for_fresh_code_is_pending(client):
    qr_response = client.get("/login/qr")
    code = re.search(r'const code = "([^"]+)"', qr_response.get_data(as_text=True)).group(1)

    response = client.get(f"/api/pair/{code}/status")

    assert response.status_code == 200
    assert response.get_json() == {"status": "pending"}


def test_pair_status_for_unknown_code_is_not_found(client):
    response = client.get("/api/pair/does-not-exist/status")

    assert response.status_code == 200
    assert response.get_json() == {"status": "not_found"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "pair_status" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Implement**

In `spotify_explorer/app.py`, add this route right after the existing `callback()` route, before `/logout` — keeps the file's auth-related routes grouped together in a natural order (`/login/qr`, `/login`, `/callback`, `/api/pair/<code>/status`, `/logout`):

```python
    @app.route("/api/pair/<code>/status")
    def pair_status(code):
        status = pairing.get_status(code)
        if status != "completed":
            return jsonify({"status": status})
        tokens = pairing.consume(code)
        user_auth.apply_tokens_to_session(tokens)
        return jsonify({"status": "completed"})
```

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add GET /api/pair/<code>/status polling route"
```

---

## Task 7: `GET /callback` relays tokens to the pairing store

**Files:**
- Modify: `spotify_explorer/app.py:172-189` (the `callback()` route)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
def test_callback_without_pairing_code_behaves_like_before(client, monkeypatch):
    def fake_exchange_code(code, state, client_id, client_secret, redirect_uri):
        return {"access_token": "at", "refresh_token": "rt", "expires_at": 9999999999.0}

    monkeypatch.setattr(app_module.user_auth, "exchange_code", fake_exchange_code)

    response = client.get("/callback?code=abc&state=xyz")

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_callback_relays_tokens_so_kiosk_status_poll_completes_and_logs_in(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True

    kiosk = flask_app.test_client()
    phone = flask_app.test_client()

    qr_response = kiosk.get("/login/qr")
    code = re.search(r'const code = "([^"]+)"', qr_response.get_data(as_text=True)).group(1)

    phone.get(f"/login?pair={code}")

    def fake_exchange_code(code_param, state, client_id, client_secret, redirect_uri):
        return {"access_token": "at", "refresh_token": "rt", "expires_at": 9999999999.0}

    monkeypatch.setattr(app_module.user_auth, "exchange_code", fake_exchange_code)

    phone.get("/callback?code=abc&state=xyz")

    status_response = kiosk.get(f"/api/pair/{code}/status")
    assert status_response.get_json() == {"status": "completed"}

    with kiosk.session_transaction() as sess:
        assert sess["user_access_token"] == "at"
        assert sess["user_refresh_token"] == "rt"

    second_poll = kiosk.get(f"/api/pair/{code}/status")
    assert second_poll.get_json() == {"status": "not_found"}
```

This is the full end-to-end simulation: `kiosk` and `phone` are two independent test clients (two independent cookie jars, exactly like two real devices) sharing the same underlying Flask app (and therefore the same in-memory `pairing` store) — proving the relay genuinely crosses from the phone's session to the kiosk's session, not just that both happen to see the same data because they're the same client.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "callback_relays or callback_without_pairing_code" -v`
Expected: `test_callback_relays_tokens_so_kiosk_status_poll_completes_and_logs_in` FAILs — the kiosk's poll stays `pending` forever since nothing relays the phone's tokens yet. `test_callback_without_pairing_code_behaves_like_before` should already PASS (it doesn't yet depend on any new behavior) — that's expected, it's here as a regression guard for the next step.

- [ ] **Step 3: Implement**

In `spotify_explorer/app.py`, replace the `callback()` route (lines 172-189):

```python
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
            pairing.mark_completed(pair_code, tokens)

        return redirect(app.config["FRONTEND_URL"])
```

The only changes: `user_auth.exchange_code(...)`'s return value is now captured (`tokens = ...` instead of a bare call), and two new lines relay it to `pairing` when a `pairing_code` was stashed in the session by `/login?pair=`. When there's no `pairing_code` (the existing, unpaired flow), `session.pop("pairing_code", None)` returns `None` and the relay is skipped — behavior is identical to today.

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new. This completes all backend work in this plan. Pay particular attention to the 4 pre-existing `/callback` tests (`test_callback_exchanges_code_and_redirects_home`, `test_callback_with_spotify_error_redirects_with_auth_error`, `test_callback_with_bad_state_redirects_with_auth_error`, `test_callback_redirects_to_configured_frontend_url`) — all 4 must still pass completely unmodified.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: relay tokens from /callback into the pairing store"
```

---

## Task 8: Update `spotify_explorer/README.md`

**Files:**
- Modify: `spotify_explorer/README.md`

- [ ] **Step 1: Add a new "Login via QR code" section**

Read the current `spotify_explorer/README.md` first to find a natural insertion point (e.g. right after the existing setup/login instructions, before or alongside "O que cada aba faz"). Add:

```markdown
## Login via QR code (kiosk/demo)

Além do login direto (`/login`, no mesmo dispositivo), dá pra abrir
`GET /login/qr` numa tela compartilhada (kiosk, TV, PC de demo) — ela
mostra um QR code que qualquer pessoa pode escanear com o próprio
celular pra autorizar com a própria conta Spotify. A tela do kiosk
fica fazendo polling sozinha e destrava automaticamente assim que
alguém completa o login pelo celular.

**Pré-requisito:** o celular precisa estar na **mesma rede local** que
a máquina rodando o `spotify_explorer` — o QR codifica o endereço que
o navegador do kiosk usou pra abrir a página (`request.host_url`), e
esse endereço só é alcançável de outro dispositivo se for um IP de
rede local (ex.: `http://192.168.x.x:5000/`), não `127.0.0.1`. Não há
suporte a túnel (ngrok ou similar) embutido — pra demo fora da rede
local, seria preciso configurar isso manualmente.

O código do QR expira em 5 minutos e é de uso único — depois de
consumido (ou expirado), a tela do kiosk gera um QR novo sozinha.
```

- [ ] **Step 2: Add to the smoke-test checklist**

Find the "## Checklist de smoke test manual" section and add:

```markdown
- [ ] `GET /login/qr` mostra um QR code de verdade e escaneável (teste
      com celular na mesma rede local)
- [ ] Escanear o QR e autorizar no celular faz a tela do kiosk
      destravar sozinha (sem recarregar manualmente)
- [ ] Um QR não escaneado por 5 minutos expira e a tela gera um novo
      sozinha
- [ ] Escanear o mesmo QR duas vezes (ou escanear um já usado) não
      funciona da segunda vez
```

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: document QR-code login for kiosk/demo scenarios"
```

---

## Task 9: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd spotify_explorer && pytest -v`
Expected: all tests pass, including every new test added across Tasks 1-7

- [ ] **Step 2: Run the full frontend build**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds with no errors (this feature makes no Vue changes, so this just confirms nothing broke)

- [ ] **Step 3: Confirm no other backend route's behavior changed**

Run: `git diff main -- spotify_explorer/app.py spotify_explorer/user_auth.py`
Expected: every hunk in `app.py` is either a new import, the new `pairing = pairing_store.PairingStore()` line, a new route, or one of the two narrowly-scoped, intentional changes to `login()`/`callback()` described in Tasks 5 and 7 — nothing else should show a diff. Every hunk in `user_auth.py` should be exactly the `exchange_code`/`apply_tokens_to_session` refactor from Task 2 — no other function should show a diff.

- [ ] **Step 4: Manual smoke test (requires a phone on the same LAN)**

Start the backend (`cd spotify_explorer && python app.py`, bound to `0.0.0.0` or the machine's LAN IP so a phone can reach it — not `127.0.0.1`) and the frontend dev server if testing the full app, then open `http://<lan-ip>:5000/login/qr` from a second device (or a laptop simulating the "kiosk"), and scan the QR with a phone that has its own Spotify login. Walk the 4 new checklist items added to `spotify_explorer/README.md` in Task 8. This is a genuinely new user-facing flow — treat any surprise (QR doesn't scan, phone can't reach the host, kiosk doesn't auto-redirect) as a real finding, not just a checkbox to tick.
