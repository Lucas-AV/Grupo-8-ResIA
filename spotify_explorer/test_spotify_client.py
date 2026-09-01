import time
from unittest.mock import Mock, patch

import pytest
import requests

import spotify_client


def setup_function():
    spotify_client._token_cache["access_token"] = None
    spotify_client._token_cache["expires_at"] = 0


@patch("spotify_client.requests.post")
def test_get_app_token_requests_new_token_when_none_cached(mock_post):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "abc123", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    token = spotify_client.get_app_token("client-id", "client-secret")

    assert token == "abc123"
    mock_post.assert_called_once()


@patch("spotify_client.requests.post")
def test_get_app_token_reuses_cached_token_before_expiry(mock_post):
    spotify_client._token_cache["access_token"] = "cached-token"
    spotify_client._token_cache["expires_at"] = time.time() + 1000

    token = spotify_client.get_app_token("client-id", "client-secret")

    assert token == "cached-token"
    mock_post.assert_not_called()


@patch("spotify_client.requests.post")
def test_get_app_token_refreshes_after_expiry(mock_post):
    spotify_client._token_cache["access_token"] = "old-token"
    spotify_client._token_cache["expires_at"] = time.time() - 10
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "new-token", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    token = spotify_client.get_app_token("client-id", "client-secret")

    assert token == "new-token"
    mock_post.assert_called_once()


@patch("spotify_client.requests.get")
def test_call_api_returns_json_and_status_on_success(mock_get):
    mock_get.return_value = Mock(status_code=200, json=lambda: {"id": "track1"}, headers={})

    body, status = spotify_client.call_api("/tracks/track1", "user-or-app-token")

    assert status == 200
    assert body == {"id": "track1"}
    args, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer user-or-app-token"


@patch("spotify_client.requests.get")
def test_call_api_returns_error_body_and_status_on_failure(mock_get):
    mock_get.return_value = Mock(
        status_code=403,
        json=lambda: {"error": {"status": 403, "message": "Forbidden"}},
        headers={},
    )

    body, status = spotify_client.call_api("/audio-features/track1", "token")

    assert status == 403
    assert body["error"]["message"] == "Forbidden"


@patch("spotify_client.requests.get")
def test_call_api_includes_retry_after_on_429(mock_get):
    mock_get.return_value = Mock(
        status_code=429,
        json=lambda: {"error": {"status": 429, "message": "rate limited"}},
        headers={"Retry-After": "5"},
    )

    body, status = spotify_client.call_api("/search", "token")

    assert status == 429
    assert body["retry_after_seconds"] == "5"
    assert body["error"]["message"] == "rate limited"


@patch("spotify_client.call_api")
@patch("spotify_client.get_app_token", return_value="fake-app-token")
def test_api_get_uses_app_token_and_delegates_to_call_api(mock_get_token, mock_call_api):
    mock_call_api.return_value = ({"tracks": []}, 200)

    body, status = spotify_client.api_get(
        "/search", "client-id", "client-secret", params={"q": "test"}
    )

    assert (body, status) == ({"tracks": []}, 200)
    mock_get_token.assert_called_once_with("client-id", "client-secret")
    mock_call_api.assert_called_once_with("/search", "fake-app-token", params={"q": "test"})


@patch("spotify_client.requests.post")
def test_get_app_token_raises_apptokenerror_on_failure(mock_post):
    mock_post.return_value = Mock(
        status_code=400,
        json=lambda: {"error": "invalid_client", "error_description": "Invalid client secret"},
    )

    with pytest.raises(spotify_client.AppTokenError) as exc_info:
        spotify_client.get_app_token("bad-client-id", "bad-secret")

    assert exc_info.value.status_code == 400
    assert exc_info.value.body["error"] == "invalid_client"


@patch("spotify_client.requests.post")
def test_api_get_returns_error_tuple_when_token_request_fails(mock_post):
    mock_post.return_value = Mock(
        status_code=400,
        json=lambda: {"error": "invalid_client", "error_description": "Invalid client secret"},
    )

    body, status = spotify_client.api_get("/search", "bad-client-id", "bad-secret")

    assert status == 400
    assert body["error"] == "invalid_client"


@patch("spotify_client.requests.post", side_effect=requests.exceptions.ConnectionError("boom"))
def test_get_app_token_raises_apptokenerror_on_connection_error(mock_post):
    with pytest.raises(spotify_client.AppTokenError) as exc_info:
        spotify_client.get_app_token("client-id", "client-secret")

    assert exc_info.value.status_code == 502
    assert exc_info.value.body["error"] == "connection_error"


@patch("spotify_client.requests.post")
def test_get_app_token_raises_apptokenerror_on_non_json_success_body(mock_post):
    mock_post.return_value = Mock(status_code=200, json=Mock(side_effect=ValueError("bad json")))

    with pytest.raises(spotify_client.AppTokenError) as exc_info:
        spotify_client.get_app_token("client-id", "client-secret")

    assert exc_info.value.status_code == 200
    assert exc_info.value.body["error"] == "invalid_response"


@patch("spotify_client.requests.get", side_effect=requests.exceptions.ConnectionError("boom"))
def test_call_api_returns_error_tuple_on_connection_error(mock_get):
    body, status = spotify_client.call_api("/search", "token")

    assert status == 502
    assert body["error"] == "connection_error"


@patch("spotify_client.requests.get")
def test_call_api_returns_error_tuple_on_non_json_body(mock_get):
    mock_get.return_value = Mock(status_code=200, json=Mock(side_effect=ValueError("bad json")), headers={})

    body, status = spotify_client.call_api("/search", "token")

    assert status == 200
    assert body["error"] == "invalid_response"
