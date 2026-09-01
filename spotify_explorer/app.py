import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

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
    register_routes(app)
    return app


def register_routes(app):
    @app.route("/")
    def index():
        missing_credentials = not (
            app.config["SPOTIFY_CLIENT_ID"] and app.config["SPOTIFY_CLIENT_SECRET"]
        )
        return render_template(
            "index.html",
            missing_credentials=missing_credentials,
            auth_error=request.args.get("auth_error"),
        )

    @app.route("/api/search", methods=["POST"])
    def search():
        data = request.get_json(force=True)
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


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
