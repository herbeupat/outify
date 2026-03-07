import os
import time
import urllib

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, PictureType


def do_tag_file(album: str, artists: list[str], effective_output: bool, file_path_temp_mp3: str,
                image_url: str | None, title: str, track: int, year: str | None, albumartist: str | None):
    try:
        tag_file = EasyID3(file_path_temp_mp3)
    except mutagen.id3.ID3NoHeaderError:
        tag_file = mutagen.File(file_path_temp_mp3, easy=True)
        tag_file.add_tags()

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