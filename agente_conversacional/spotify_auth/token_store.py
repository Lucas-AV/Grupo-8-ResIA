import os
import sqlite3

from cryptography.fernet import Fernet

_DEFAULT_DB_PATH = "spotify_tokens.db"


class TokenStore:
    """Armazenamento de tokens OAuth por sessao, criptografado em repouso (ticket 5.4)."""

    def __init__(self, db_path=None, encryption_key=None):
        self._db_path = db_path or os.environ.get("SPOTIFY_TOKEN_DB_PATH", _DEFAULT_DB_PATH)
        self._fernet = Fernet(encryption_key or os.environ["SPOTIFY_TOKEN_ENCRYPTION_KEY"])
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS spotify_tokens (
                    session_id TEXT PRIMARY KEY,
                    access_token BLOB NOT NULL,
                    refresh_token BLOB NOT NULL,
                    expires_at REAL NOT NULL
                )"""
            )

    def save(self, session_id, access_token, refresh_token, expires_at):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO spotify_tokens (session_id, access_token, refresh_token, expires_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET
                     access_token = excluded.access_token,
                     refresh_token = excluded.refresh_token,
                     expires_at = excluded.expires_at""",
                (
                    session_id,
                    self._fernet.encrypt(access_token.encode("utf-8")),
                    self._fernet.encrypt(refresh_token.encode("utf-8")),
                    expires_at,
                ),
            )

    def get(self, session_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT access_token, refresh_token, expires_at FROM spotify_tokens WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        access_token, refresh_token, expires_at = row
        return {
            "access_token": self._fernet.decrypt(access_token).decode("utf-8"),
            "refresh_token": self._fernet.decrypt(refresh_token).decode("utf-8"),
            "expires_at": expires_at,
        }

    def delete(self, session_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM spotify_tokens WHERE session_id = ?", (session_id,))
