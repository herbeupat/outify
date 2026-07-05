import argparse
import configparser
import hmac
import os
import sys
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, request

from Playlist import Playlist
from YT import YT

app = Flask(__name__)
yt_instance: YT | None = None
base_dir: str | None = None
api_username: str | None = None
api_password: str | None = None
api_base_url: str | None = None
FORM_PATH = Path(__file__).resolve().parent / "html/track_form.html"


@app.get("/")
def index():
    effective_base_url = api_base_url or request.host_url.rstrip("/")
    html = FORM_PATH.read_text().replace("{{API_BASE_URL}}", effective_base_url)
    return Response(html, mimetype="text/html")


def load_settings(settings_path: Path) -> tuple[str, str, str, str | None]:
    if not settings_path.is_file():
        sys.exit(f"Settings file not found: {settings_path}.")
    config = configparser.ConfigParser()
    config.read(settings_path)
    if not config.has_option("defaults", "dir"):
        sys.exit(f"{settings_path} must contain a [defaults] section with a 'dir' option.")
    if not config.has_section("api") or not config.has_option("api", "username") or not config.has_option("api", "password"):
        sys.exit(f"{settings_path} must contain an [api] section with 'username' and 'password'.")
    return (
        config.get("defaults", "dir"),
        config.get("api", "username"),
        config.get("api", "password"),
        config.get("api", "base_url", fallback=None),
    )


def require_auth(view):
    @wraps(view)
    def wrapped(*view_args, **view_kwargs):
        assert api_username is not None and api_password is not None
        auth = request.authorization
        valid = (
            auth is not None
            and hmac.compare_digest(auth.username or "", api_username)
            and hmac.compare_digest(auth.password or "", api_password)
        )
        if not valid:
            return (
                jsonify({"error": "Unauthorized"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Outify API"'},
            )
        return view(*view_args, **view_kwargs)

    return wrapped


@app.get("/playlists")
@require_auth
def list_playlists():
    names = [
        entry.removesuffix(".m3u")
        for entry in os.listdir(base_dir)
        if entry.endswith(".m3u") and os.path.isfile(os.path.join(base_dir, entry))
    ]
    return jsonify(sorted(names))


@app.post("/track")
@require_auth
def download_track():
    body = request.get_json(silent=True) or {}

    missing = [field for field in ("artist", "album", "title", "url") if not body.get(field)]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    artist = body["artist"]
    album = body["album"]
    title = body["title"]
    url = body["url"]
    year = body.get("year")
    track = int(body.get("track", 0))
    cover = body.get("cover")
    add_to_playlist = body.get("add_to_playlist")
    cookies_from_browser = body.get("cookies_from_browser")

    if add_to_playlist is not None and not isinstance(add_to_playlist, list):
        return jsonify({"error": "add_to_playlist must be a list of playlist file names"}), 400

    request_yt_instance = YT(base_dir, 10, True, cookies_from_browser)
    downloaded_file_path = request_yt_instance.download(url, [artist], album, track, title, year, cover, False)

    if downloaded_file_path is None:
        return jsonify({"error": "Download failed"}), 500

    if add_to_playlist:
        for playlist_file in add_to_playlist:
            playlist = Playlist(base_dir, playlist_file, True)
            playlist.add_song(downloaded_file_path)
            playlist.write_to_disk()

    return jsonify({"file_path": downloaded_file_path})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Outify API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--settings", default=str(Path(__file__).resolve().parent / "settings.ini"))
    args = parser.parse_args()

    base_dir, api_username, api_password, api_base_url = load_settings(Path(args.settings))

    app.run(host=args.host, port=args.port)
