import logging
import os
import shutil
import subprocess
import time
from typing import Callable

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, PictureType
import urllib.request

from simple_term_menu import TerminalMenu
from ytmusicapi import YTMusic
import re

from utils import *

class YT:

    def __init__(self, base_dir, search_limit, force_sync_download: bool, cookies_from_browser: str | None):
        self.base_dir = base_dir
        self.ytmusic = YTMusic()
        self.search_limit = search_limit
        self.batch_output = False # not working, have to investigate that
        self.force_sync_download = force_sync_download
        self.logger = logging.getLogger(__name__)
        self.cookies_from_browser = cookies_from_browser


    def set_batch_output(self, value: bool):
        self.batch_output = value


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


    def try_download(self, url: str, artists: list[str], album: str, track: int, title: str, year: str | None, image_url: str | None, output:bool) -> str | None:
        try:
            return self.download(url, artists, album, track, title, year, image_url, output)
        except Exception as e:
            print(f"{WARNING} Error while downloading video {url}: {e}")
            return None


    def download(self, url: str, artists: list[str], album: str, track: int, title: str, year: str | None, image_url: str | None, output:bool) -> str | None:
        self.logger.debug(f"Start download {url}")
        artist = artists[0]
        artist_dir = self.base_dir + os.sep + sanitize_file_name(artist)
        effective_output = output or self.batch_output
        if not os.path.exists(artist_dir):
            os.mkdir(artist_dir)
        elif os.path.isfile(artist_dir):
            if effective_output:
                print(f"{WARNING}F ile with artist name {artist_dir} exists, cannot create directory{ENDC}")
            return None
        album_dir = artist_dir + os.sep + sanitize_file_name(album)
        if not os.path.exists(album_dir):
            os.mkdir(album_dir)
        elif os.path.isfile(album_dir):
            if effective_output:
                print(f"{WARNING}File with album name {album_dir} exists, cannot create directory{ENDC}")
            return None
        file_path_mp3 = f'{album_dir}{os.sep}{track:02d} {sanitize_file_name(title)}.mp3' if track > 0 else f'{album_dir}{os.sep}{sanitize_file_name(title)}.mp3'
        if os.path.isfile(file_path_mp3):
            return file_path_mp3

        if effective_output:
            print(f"Downloading file for {artist} - {title}")
        
        file_path_temp_mp3 = self.just_download(url, effective_output)
        if file_path_temp_mp3 is None:
            return None

        if effective_output:
            print('Tagging file')
        self.do_tag_file(album, artists, effective_output, file_path_temp_mp3, image_url, title, track, year, None)

        shutil.move(file_path_temp_mp3, file_path_mp3)

        return file_path_mp3


    def just_download(self, url: str, effective_output: bool) -> str:
        ts = time.time() 
        file_path_temp_m4a = f"/tmp/outify.{ts}.m4a"
        file_path_temp_mp3 = f'/tmp/outify.{ts}.mp3'

        yt_dlp_args = ["yt-dlp", "-f", "140", "-o", file_path_temp_m4a, "--quiet"]
        if self.cookies_from_browser:
            yt_dlp_args.append("--cookies-from-browser")
            yt_dlp_args.append(self.cookies_from_browser)
        yt_dlp_args.append(url)
        yt_dlp_result = subprocess.run(yt_dlp_args) #, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if yt_dlp_result.returncode != 0:
            self.logger.debug(yt_dlp_result.stderr)
            if effective_output:
                print(f"{WARNING} error while downloading {url}")
            return None
        if effective_output:
            print('Converting file')
        ffmpeg_result = subprocess.run(["ffmpeg", "-i", file_path_temp_m4a, "-c:a", "libmp3lame", "-b:a", "192k", "-hide_banner", "-loglevel", "warning", file_path_temp_mp3])
        if ffmpeg_result.returncode != 0:
            self.logger.debug(ffmpeg_result.stderr)
            if effective_output:
                print(f"{WARNING} error while converting {url}")
            return None
        os.remove(file_path_temp_m4a)
        return file_path_temp_mp3


    def do_tag_file(self, album: str, artists: list[str], effective_output: bool, file_path_temp_mp3: str,
                    image_url: str | None, title: str, track: int, year: str | None, albumartist: str | None):

        tag_file = EasyID3(file_path_temp_mp3)
        tag_file["albumartist"] = albumartist if albumartist else artists[0]
        tag_file["artist"] = ", ".join(artists)
        tag_file["album"] = album
        tag_file["title"] = title
        if year:
            tag_file["date"] = year
        if track > 0:
            tag_file["tracknumber"] = str(track)
        tag_file.save()

        if image_url:
            if effective_output:
                print('Tagging album cover')
            ts = time.time() 
            cover_temp_file = f"/tmp/outify_cover{ts}.jpg"
            urllib.request.urlretrieve(image_url, cover_temp_file)
            raw_image = open(cover_temp_file, 'rb').read()
            tag_file = ID3(file_path_temp_mp3)
            tag_file.add(APIC(
                mime='image/jpg',
                type=PictureType.COVER_FRONT,
                data=raw_image
            ))
            tag_file.save()
            os.remove(cover_temp_file)

    def search_yt_music(self, artists: list[str], album: str, track: int, title: str, year: str | None, image_url: str | None) -> Callable[[], None] | None:
        search_results = self.ytmusic.search(artists[0] + " " + title, filter='songs', limit=self.search_limit)
        options = []
        if len(search_results) == 0:
            print(f"{WARNING} No result {ENDC}")
            return None
        for i, item in enumerate(search_results):
            video_artists=list(map(lambda artist: artist['name'], item['artists'] if 'artists' in item else []))
            option = f"{i + 1: 2d} {item['title']} - {', '.join(video_artists)}"
            options.append(option)
        options.append("[a] abort")
        terminal_menu = TerminalMenu(options, title=f"Choose a song to download for {title} - {', '.join(artists)}")
        selected = terminal_menu.show()
        if selected is None or (selected == len(options) - 1):
            return None

        url = 'https://music.youtube.com/watch?v=' + search_results[selected]['videoId']

        if self.force_sync_download:
            self.logger.debug(f"Force sync download of {url}")
            return self.try_download(url, artists, album, track, title, year, image_url, True)
        else:
            self.logger.debug(f"Async download of {url}")
            def return_function():
                return self.try_download(url, artists, album, track, title, year, image_url, False)
            return return_function


    def search_yt_album(self, artist: str, album: str, tracks: list[str], year: str | None, image_url: str | None, output: bool):
        print(f"Will download {artist} - {album} - {len(tracks)} tracks - {year} - {image_url}")
        search_results = self.ytmusic.search(artist + " " + album, filter='albums', limit=self.search_limit)

        options = []
        if len(search_results) == 0:
            print(f"{WARNING} No result {ENDC}")
            return None
        for i, item in enumerate(search_results):
            option = item['title']
            options.append(option)

        terminal_menu = TerminalMenu(options, title=f"Choose an album to download {artist} - {album}")
        selected = terminal_menu.show()
        if selected is None:
            return None

        url = 'https://music.youtube.com/playlist?list=' + search_results[selected]['playlistId']

        artist_dir = self.base_dir + os.sep + sanitize_file_name(artist)
        effective_output = output or self.batch_output

        if not os.path.exists(artist_dir):
            os.mkdir(artist_dir)
        elif os.path.isfile(artist_dir):
            if effective_output:
                print(f"{WARNING}File with artist name {artist_dir} exists, cannot create directory{ENDC}")
            return None

        album_dir = artist_dir + os.sep + sanitize_file_name(album)
        if not os.path.exists(album_dir):
            os.mkdir(album_dir)
        elif os.path.isfile(album_dir):
            if effective_output:
                print(f"{WARNING}File with album name {album_dir} exists, cannot create directory{ENDC}")
            return None

        ts = time.time()
        tmp_dir = f"/tmp/{ts}"
        os.mkdir(tmp_dir)
        file_format = tmp_dir + os.sep + "%(playlist_index)s %(title)s.%(ext)s"

        yt_dlp_args = ["yt-dlp", "-f", "140", "-o", file_format]
        if self.cookies_from_browser:
            yt_dlp_args.append("--cookies-from-browser")
            yt_dlp_args.append(self.cookies_from_browser)
        yt_dlp_args.append(url)
        subprocess.run(yt_dlp_args)

        for file in os.listdir(tmp_dir):
            print(f"Convert {file}")
            file_path_temp_m4a = tmp_dir + os.sep + file
            file_path_temp_mp3 = tmp_dir + os.sep + file.replace(".m4a", ".mp3")
            subprocess.run(
                ["ffmpeg", "-i", file_path_temp_m4a, "-c:a", "libmp3lame", "-b:a", "192k", "-hide_banner", "-loglevel",
                 "warning", file_path_temp_mp3])
            os.remove(file_path_temp_m4a)

        for file in os.listdir(tmp_dir):
            print(f"Tag {file}")
            track_index = int(file[0:file.index(" ")]) - 1
            file_path_temp_mp3 = tmp_dir + os.sep + file
            title = tracks[track_index] if len(tracks) > track_index else file[file.index(" ") + 1:]

            self.do_tag_file(album, [artist], output, file_path_temp_mp3, image_url, title, track_index + 1, ts, year)

            file_path_mp3 = album_dir + os.sep + file
            shutil.move(file_path_temp_mp3, file_path_mp3)

        return url


    def replace_file(self, original_file: str, url: str):
        original_file_tag = EasyID3(original_file)
        artists = original_file_tag["artist"]
        try:
            albumartist = original_file_tag["albumartist"][0]
        except:
            albumartist = artists[0]
        try:
            album = original_file_tag["album"][0]
        except:
            album = "Unknown album"
        title = original_file_tag["title"][0]
        #date = original_file_tag["date"]
        try:
            date = original_file_tag["date"][0]
        except:
            date = None
        try:
            tracknumber = original_file_tag["tracknumber"][0]
            effective_track = int(tracknumber)
        except:
            effective_track = 0
        
        print(f"Original file data: {artists} {albumartist} {album} {title} {date} {effective_track}")

        new_file = self.just_download(url, True)
        if new_file is None:
            print("Cannot download file, abort")
            return 
        self.do_tag_file(album, artists, True, new_file, None, title, effective_track, date, albumartist)

        image_tag_file = ID3(original_file)
        orginal_image_data = image_tag_file.getall("APIC")
        if orginal_image_data:
            new_file_tag = ID3(new_file)
            new_file_tag.setall('APIC', orginal_image_data)
            new_file_tag.save()

        shutil.move(new_file, original_file)
