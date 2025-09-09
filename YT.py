import os
import shutil
import subprocess
from typing import Callable

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, PictureType
import urllib.request

from simple_term_menu import TerminalMenu
from ytmusicapi import YTMusic
import re

from utils import *

class YT:

    def __init__(self, base_dir, search_limit):
        self.base_dir = base_dir
        self.ytmusic = YTMusic()
        self.search_limit = search_limit

    def can_run_basic(self) -> bool:
        has_yt_dlp = shutil.which('yt-dlp') is not None
        if not has_yt_dlp:
            print(f"{WARNING} cannot find yt-dlp in path, YT won't work")
        has_ffmpeg = shutil.which('ffmpeg') is not None
        if not has_ffmpeg:
            print(f"{WARNING} cannot find ffmpeg in path, YT won't work")
        return has_yt_dlp and has_ffmpeg


    @staticmethod
    def is_youtube_url(url: str):
        return url.startswith('https://music.youtube.com/watch?v=') or url.startswith("https://www.youtube.com/watch?")


    def download(self, url: str, artists: list[str], album: str, track: int, title: str, year: str, image_url: str | None, output:bool) -> str | None:
        artist = artists[0]
        artist_dir = self.base_dir + os.sep + sanitize_file_name(artist)
        if not os.path.exists(artist_dir):
            os.mkdir(artist_dir)
        elif os.path.isfile(artist_dir):
            if output:
                print(f"{WARNING}File with artist name {artist_dir} exists, cannot create directory{ENDC}")
            return None
        album_dir = artist_dir + os.sep + sanitize_file_name(album)
        if not os.path.exists(album_dir):
            os.mkdir(album_dir)
        elif os.path.isfile(album_dir):
            if output:
                print(f"{WARNING}File with album name {album_dir} exists, cannot create directory{ENDC}")
            return None
        file_path_mp3 = f'{album_dir}{os.sep}{track:02d} {sanitize_file_name(title)}.mp3'
        if os.path.isfile(file_path_mp3):
            return file_path_mp3

        file_path_temp_m4a = "/tmp/outify.m4a"
        file_path_temp_mp3 = '/tmp/outify.mp3'

        if output:
            print('Downloading file')
        subprocess.run(["yt-dlp", "-f", "140", "-o", file_path_temp_m4a, "--quiet", url]        )
        if output:
            print('Converting file')
        subprocess.run(["ffmpeg", "-i", file_path_temp_m4a, "-c:a", "libmp3lame", "-b:a", "192k", "-hide_banner", "-loglevel", "warning", file_path_temp_mp3])

        if output:
            print('Tagging file')
        tag_file = EasyID3(file_path_temp_mp3)
        tag_file["albumartist"] = artists[0]
        tag_file["artist"] = ", ".join(artists)
        tag_file["album"] = album
        tag_file["title"] = title
        tag_file["date"] = year
        tag_file["tracknumber"] = str(track)
        tag_file.save()

        if image_url:
            if output:
                print('Tagging album cover')
            cover_temp_file = "/tmp/outify_cover.jpg"
            urllib.request.urlretrieve(image_url, cover_temp_file)
            raw_image = open(cover_temp_file, 'rb').read()
            tag_file = ID3(file_path_temp_mp3)
            tag_file.add(APIC(
                mime='image/jpg',
                type=PictureType.COVER_FRONT,
                data = raw_image
            ))
            tag_file.save()
            os.remove(cover_temp_file)

        shutil.move(file_path_temp_mp3, file_path_mp3)

        os.remove(file_path_temp_m4a)

        return file_path_mp3


    def search_yt_music(self, artists: list[str], album: str, track: int, title: str, year: str, image_url: str | None) -> Callable[[], None] | None:
        search_results = self.ytmusic.search(artists[0] + " " + title, filter='songs', limit=self.search_limit)
        options = []
        if len(search_results) == 0:
            print(f"{WARNING} No result {ENDC}")
            return None
        for i, item in enumerate(search_results):
            video_artists=list(map(lambda artist: artist['name'], item['artists']))
            option = f"{i + 1: 2d} {item['title']} - {', '.join(video_artists)} {item['videoId']}"
            options.append(option)
        options.append("[a] abort")
        terminal_menu = TerminalMenu(options, title=f"Choose a song to download for {title} - {', '.join(artists)}")
        selected = terminal_menu.show()
        print(selected)
        if selected == len(options) - 1:
            return None

        url = 'https://music.youtube.com/watch?v=' + search_results[selected]['videoId']
        print(url)
        def return_function():
            self.download(url, artists, album, track, title, year, image_url, False)
        return return_function

