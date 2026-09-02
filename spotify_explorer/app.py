import os
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_from_directory

import spotify_client
import user_auth

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

    def _user_data_route(path, params=None):
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        body, status = spotify_client.call_api(path, token, params=params)
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


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
