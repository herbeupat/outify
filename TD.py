import base64
import json
import os
import shutil
import subprocess
import time

import requests
from typing import Callable

from simple_term_menu import TerminalMenu

from Tagger import do_tag_file
from utils import WARNING, ENDC, sanitize_file_name


class TD:

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.base_url = 'https://wolf.qqdl.site'

    def search_td_music(self, artists: list[str], album: str, track: int, title: str, year: str | None, image_url: str | None) -> Callable[[], None] | None:
        search_url = f"{self.base_url}/search/?s={title} {' '.join(artists)}"
        search_response = requests.get(search_url)
        items = search_response.json()["data"]["items"]
        if len(items) == 0:
            print(f"{WARNING} No result {ENDC}")
            return None
        options = []
        for i, item in enumerate(items):

            item_artists = list(map(lambda artist: artist['name'], item['artists'] if 'artists' in item else []))
            artists_ = f"{i + 1: 2d} {item['title']} - {', '.join(item_artists)}"
            option = artists_
            options.append(option)
        options.append("[a] abort")
        terminal_menu = TerminalMenu(options, title=f"Choose a song to download for {title} - {', '.join(artists)}")
        selected = terminal_menu.show()

        if selected is None or (selected == len(options) - 1):
            return None

        track_id = items[selected]["id"]
        track_info_url = f"{self.base_url}/track/?id={track_id}&quality=HIGH"
        track_info = requests.get(track_info_url).json()
        if "data" not in track_info:
            print(f"{WARNING} Selected track has no data item {ENDC}")
            return None
        track_info_data = track_info["data"]
        if "manifest" not in track_info_data:
            print(f"{WARNING} Selected track has no manifest {ENDC}")
            return None
        manifest_base64 = track_info_data["manifest"]
        manifest_raw = base64.b64decode(manifest_base64).decode("utf-8")
        manifest = json.loads(manifest_raw)
        urls = manifest["urls"]
        if len(urls) == 0:
            return None
        def return_function():
            return self.download(urls[0], artists, album, track, title, year, image_url)
        return return_function

    def download(self, m4a_url, artists: list[str], album: str, track: int, title: str, year: str | None, image_url: str | None):
        m4a_file = requests.get(m4a_url)
        ts = time.time()
        file_path_temp_m4a = f"/tmp/outify.{ts}.m4a"
        file_temp = open(file_path_temp_m4a, 'wb')
        file_temp.write(m4a_file.content)
        file_temp.close()

        file_path_temp_mp3 = f"/tmp/outify.{ts}.mp3"
        ffmpeg_result = subprocess.run(
            ["ffmpeg", "-i", file_path_temp_m4a, "-c:a", "libmp3lame", "-b:a", "192k", "-hide_banner", "-loglevel",
             "warning", file_path_temp_mp3])
        if ffmpeg_result.returncode != 0:
            return None

        do_tag_file(album, artists, False, file_path_temp_mp3, image_url, title, track, year, None)

        artist = artists[0]
        artist_dir = self.base_dir + os.sep + sanitize_file_name(artist)
        if not os.path.exists(artist_dir):
            os.mkdir(artist_dir)
        elif os.path.isfile(artist_dir):
            return None
        album_dir = artist_dir + os.sep + sanitize_file_name(album)
        if not os.path.exists(album_dir):
            os.mkdir(album_dir)
        elif os.path.isfile(album_dir):
            return None

        file_path_mp3 = f'{album_dir}{os.sep}{track:02d} {sanitize_file_name(title)}.mp3' if track > 0 else f'{album_dir}{os.sep}{sanitize_file_name(title)}.mp3'
        shutil.move(file_path_temp_mp3, file_path_mp3)
        os.remove(file_path_temp_m4a)

        return file_path_mp3