import os
from datetime import date
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_from_directory

import spotify_client
import user_auth

import segno

import pairing_store
import qr_page

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-not-for-production")
    app.config["SPOTIFY_CLIENT_ID"] = os.environ.get("SPOTIFY_CLIENT_ID", "")
    app.config["SPOTIFY_CLIENT_SECRET"] = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    app.config["SPOTIFY_REDIRECT_URI"] = os.environ.get(
        "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"
    )
    app.config["FRONTEND_URL"] = os.environ.get("FRONTEND_URL", "/")
    app.config["FRONTEND_DIST_DIR"] = os.path.join(app.static_folder, "frontend")
    register_routes(app)
    return app


def register_routes(app):
    pairing = pairing_store.PairingStore()

    @app.route("/")
    def index():
        index_path = os.path.join(app.config["FRONTEND_DIST_DIR"], "index.html")
        if not os.path.exists(index_path):
            return (
                "<h1>Frontend não buildado</h1>"
                "<p>Rode <code>cd spotify_explorer/frontend && npm install && npm run build</code> "
                "e recarregue esta página.</p>"
            ), 200
        return send_from_directory(app.config["FRONTEND_DIST_DIR"], "index.html")

    @app.route("/api/config")
    def api_config():
        missing_credentials = not (
            app.config["SPOTIFY_CLIENT_ID"] and app.config["SPOTIFY_CLIENT_SECRET"]
        )
        return jsonify({"missing_credentials": missing_credentials})

    @app.route("/api/search", methods=["POST"])
    def search():
        data = request.get_json(silent=True) or {}
        body, status = spotify_client.api_get(
            "/search",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params={
                "q": data.get("q", ""),
                "type": data.get("type", "track"),
                "limit": data.get("limit", 10),
            },
        )
        return jsonify(body), status

    @app.route("/api/track/<track_id>")
    def track(track_id):
        body, status = spotify_client.api_get(
            f"/tracks/{track_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/audio-features/<track_id>")
    def audio_features(track_id):
        body, status = spotify_client.api_get(
            f"/audio-features/{track_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/audio-analysis/<track_id>")
    def audio_analysis(track_id):
        body, status = spotify_client.api_get(
            f"/audio-analysis/{track_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>")
    def artist(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>/top-tracks")
    def artist_top_tracks(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}/top-tracks",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params={"market": request.args.get("market", "US")},
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>/albums")
    def artist_albums(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}/albums",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>/related-artists")
    def artist_related_artists(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}/related-artists",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/recommendations")
    def recommendations():
        body, status = spotify_client.api_get(
            "/recommendations",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params=request.args.to_dict(),
        )
        return jsonify(body), status

    @app.route("/api/album/<album_id>")
    def album(album_id):
        body, status = spotify_client.api_get(
            f"/albums/{album_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/playlist/<playlist_id>")
    def playlist(playlist_id):
        body, status = spotify_client.api_get(
            f"/playlists/{playlist_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/new-releases")
    def new_releases():
        body, status = spotify_client.api_get(
            "/browse/new-releases",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params={"limit": request.args.get("limit", "20")},
        )
        return jsonify(body), status

    @app.route("/login/qr")
    def login_qr():
        code = pairing.create()
        pair_url = f"{request.host_url}login?pair={code}"
        svg_data_uri = segno.make(pair_url).svg_data_uri(scale=6)
        return qr_page.render_qr_page(svg_data_uri, code, app.config["FRONTEND_URL"])

    @app.route("/login")
    def login():
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
            user_auth.exchange_code(
                request.args.get("code"),
                request.args.get("state"),
                app.config["SPOTIFY_CLIENT_ID"],
                app.config["SPOTIFY_CLIENT_SECRET"],
                app.config["SPOTIFY_REDIRECT_URI"],
            )
        except ValueError as exc:
            return redirect(f"{app.config['FRONTEND_URL']}?{urlencode({'auth_error': str(exc)})}")

        return redirect(app.config["FRONTEND_URL"])

    @app.route("/logout")
    def logout():
        user_auth.logout()
        return redirect(app.config["FRONTEND_URL"])

    @app.route("/api/me")
    def me():
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        body, status = spotify_client.call_api("/me", token)
        return jsonify(body), status

    def _user_data_route(path, params=None, method="GET", json_body=None):
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        kwargs = {"params": params}
        if method != "GET":
            kwargs["method"] = method
        if json_body is not None:
            kwargs["json_body"] = json_body
        body, status = spotify_client.call_api(path, token, **kwargs)
        return jsonify(body), status

    @app.route("/api/me/top/tracks")
    def top_tracks():
        return _user_data_route(
            "/me/top/tracks",
            params={
                "time_range": request.args.get("time_range", "medium_term"),
                "limit": request.args.get("limit", "20"),
            },
        )

    @app.route("/api/me/top/artists")
    def top_artists():
        return _user_data_route(
            "/me/top/artists",
            params={
                "time_range": request.args.get("time_range", "medium_term"),
                "limit": request.args.get("limit", "20"),
            },
        )

    @app.route("/api/me/tracks")
    def saved_tracks():
        return _user_data_route(
            "/me/tracks",
            params={
                "limit": request.args.get("limit", "20"),
                "offset": request.args.get("offset", "0"),
            },
        )

    @app.route("/api/me/player/recently-played")
    def recently_played():
        return _user_data_route(
            "/me/player/recently-played",
            params={"limit": request.args.get("limit", "20")},
        )

    @app.route("/api/me/player")
    def player():
        return _user_data_route("/me/player")

    @app.route("/api/me/player/queue")
    def player_queue():
        return _user_data_route("/me/player/queue")

    @app.route("/api/me/following")
    def following():
        return _user_data_route(
            "/me/following",
            params={
                "type": "artist",
                "limit": request.args.get("limit", "20"),
            },
        )

    @app.route("/api/me/playlists")
    def my_playlists():
        return _user_data_route(
            "/me/playlists",
            params={
                "limit": request.args.get("limit", "20"),
                "offset": request.args.get("offset", "0"),
            },
        )

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

    @app.route("/api/me/playlists/related", methods=["POST"])
    def create_related_playlist():
        data = request.get_json(silent=True) or {}
        track_id = data.get("track_id")
        track_name = data.get("track_name", "")
        if not track_id:
            return jsonify({"error": "missing_track_id"}), 400

        # duplicated from _user_data_route: this route branches between 3 sequential
        # calls, so it can't reuse the single-call helper
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        rec_body, rec_status = spotify_client.call_api(
            "/recommendations", token, params={"seed_tracks": track_id, "limit": "20"}
        )
        if rec_status != 200:
            return jsonify({"step": "recommendations", "error": rec_body}), rec_status
        if not rec_body.get("tracks"):
            return jsonify({"step": "recommendations", "error": rec_body}), 502

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


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
