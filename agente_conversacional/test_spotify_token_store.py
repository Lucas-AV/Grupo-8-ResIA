import sqlite3

from cryptography.fernet import Fernet

from spotify_auth.token_store import TokenStore


def _make_store(tmp_path):
    return TokenStore(db_path=str(tmp_path / "tokens.db"), encryption_key=Fernet.generate_key())


def test_save_then_get_round_trips_plaintext_values(tmp_path):
    store = _make_store(tmp_path)

    store.save("sess-1", "access-abc", "refresh-xyz", 1234.5)
    tokens = store.get("sess-1")

    assert tokens == {"access_token": "access-abc", "refresh_token": "refresh-xyz", "expires_at": 1234.5}


def test_get_returns_none_for_unknown_session(tmp_path):
    store = _make_store(tmp_path)

    assert store.get("nunca-logou") is None


def test_save_overwrites_existing_session_tokens(tmp_path):
    store = _make_store(tmp_path)

    store.save("sess-1", "access-old", "refresh-old", 100.0)
    store.save("sess-1", "access-new", "refresh-new", 200.0)

    assert store.get("sess-1") == {"access_token": "access-new", "refresh_token": "refresh-new", "expires_at": 200.0}


def test_delete_removes_session_tokens(tmp_path):
    store = _make_store(tmp_path)
    store.save("sess-1", "access-abc", "refresh-xyz", 1234.5)

    store.delete("sess-1")

    assert store.get("sess-1") is None


def test_tokens_are_encrypted_at_rest(tmp_path):
    db_path = tmp_path / "tokens.db"
    store = TokenStore(db_path=str(db_path), encryption_key=Fernet.generate_key())

    store.save("sess-1", "access-abc-plaintext", "refresh-xyz-plaintext", 1234.5)

    conn = sqlite3.connect(str(db_path))
    raw_access_token = conn.execute("SELECT access_token FROM spotify_tokens WHERE session_id = ?", ("sess-1",)).fetchone()[0]
    conn.close()

    assert b"access-abc-plaintext" not in raw_access_token
