import time
from unittest.mock import Mock, patch

import pytest
from flask import Flask, session

import user_auth


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    return flask_app


def test_get_login_url_contains_client_id_scope_redirect_and_state(app):
    with app.test_request_context():
        url = user_auth.get_login_url("client-id", "http://127.0.0.1:5000/callback")

        assert "client_id=client-id" in url
        assert "user-top-read" in url
        assert "user-library-read" in url
        assert "user-read-recently-played" in url
        assert "redirect_uri=" in url
        assert "state=" in url
        assert session["oauth_state"] in url


@patch("user_auth.requests.post")
def test_exchange_code_stores_tokens_in_session(mock_post, app):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    with app.test_request_context():
        session["oauth_state"] = "abc"

        user_auth.exchange_code(
            "code123", "abc", "client-id", "client-secret",
            "http://127.0.0.1:5000/callback",
        )

        assert session["user_access_token"] == "at"
        assert session["user_refresh_token"] == "rt"


def test_exchange_code_rejects_mismatched_state(app):
    with app.test_request_context():
        session["oauth_state"] = "expected"

        with pytest.raises(ValueError):
            user_auth.exchange_code(
                "code123", "wrong-state", "client-id", "client-secret",
                "http://127.0.0.1:5000/callback",
            )


def test_get_valid_user_token_returns_cached_when_not_expired(app):
    with app.test_request_context():
        session["user_access_token"] = "cached-at"
        session["user_token_expires_at"] = time.time() + 1000

        token = user_auth.get_valid_user_token("client-id", "client-secret")

        assert token == "cached-at"


@patch("user_auth.requests.post")
def test_get_valid_user_token_refreshes_when_expired(mock_post, app):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "new-at", "expires_in": 3600},
    )

    with app.test_request_context():
        session["user_access_token"] = "old-at"
        session["user_refresh_token"] = "rt"
        session["user_token_expires_at"] = time.time() - 10

        token = user_auth.get_valid_user_token("client-id", "client-secret")

        assert token == "new-at"


@patch("user_auth.requests.post")
def test_get_valid_user_token_clears_session_when_refresh_fails(mock_post, app):
    mock_post.return_value = Mock(status_code=400, json=lambda: {"error": "invalid_grant"})

    with app.test_request_context():
        session["user_access_token"] = "old-at"
        session["user_refresh_token"] = "revoked-rt"
        session["user_token_expires_at"] = time.time() - 10

        with pytest.raises(user_auth.NotLoggedInError):
            user_auth.get_valid_user_token("client-id", "client-secret")

        assert "user_access_token" not in session


def test_get_valid_user_token_raises_when_not_logged_in(app):
    with app.test_request_context():
        with pytest.raises(user_auth.NotLoggedInError):
            user_auth.get_valid_user_token("client-id", "client-secret")
