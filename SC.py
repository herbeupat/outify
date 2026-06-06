import logging
import os
import shutil
import subprocess
import time

from Tagger import do_tag_file
from utils import *


class SC:

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)

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
        do_tag_file(album, artists, effective_output, file_path_temp_mp3, image_url, title, track, year, None)

        shutil.move(file_path_temp_mp3, file_path_mp3)

        return file_path_mp3


    def just_download(self, url: str, effective_output: bool) -> str | None:
        ts = time.time() 
        file_path_temp_mp3 = f'/tmp/outify.{ts}.mp3'

        accepted_formats_base_output = str(subprocess.run(["yt-dlp", "-F", url], stdout=subprocess.PIPE).stdout).split("\\n")
        accepted_formats = list(filter(lambda line: line.startswith("hls_mp3_"), accepted_formats_base_output))

        if len(accepted_formats) == 0:
            print(f"{WARNING} Cannot find mp3 download for {url}")
            return None

        effective_format = accepted_formats[0].split(" ")[0]
        print(f"Download format {effective_format}")

        yt_dlp_args = ["yt-dlp", "-f", effective_format, "-o", file_path_temp_mp3, "--quiet", url]
        yt_dlp_result = subprocess.run(yt_dlp_args)
        if yt_dlp_result.returncode != 0:
            self.logger.debug(yt_dlp_result.stderr)
            if effective_output:
                print(f"{WARNING} error while downloading {url}")
            return None
        return file_path_temp_mp3
