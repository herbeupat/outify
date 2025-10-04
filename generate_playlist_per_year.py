import argparse

from mutagen.mp4 import MP4

from utils import *
import os 

from Playlist import Playlist
from mutagen.easyid3 import EasyID3

parser=argparse.ArgumentParser(description="Sort tracks per year, creating one playlist per year")
parser.add_argument("--dir", required=True)
parser.add_argument("--playlist-prefix", default='year-')
args=parser.parse_args()

dir = args.dir
prefix = args.playlist_prefix
count = 0

playlists = {}
songs_without_year = Playlist(dir, prefix + '-no-year.m3u')

def read_dir(dir_name):
    global count
    for file in os.listdir(dir_name):
        sub= dir_name + '/' + file
        if os.path.isdir(sub):
            read_dir(sub)
        elif file.endswith('.mp3') or file.endswith('.m4a'):
            count = count + 1
            if count % 100 == 0:
                print(f"Has found {count} files")
            try:
                effective_year = None
                if file.endswith('.mp3'):
                    tag_file = EasyID3(sub)
                    if 'date' in tag_file.keys():
                        year = tag_file['date']
                        effective_year = year[0]
                elif file.endswith('.m4a'):
                    tag_file = MP4(sub)
                    if '\xa9day' in tag_file.keys():
                        year = tag_file['\xa9day']
                        effective_year = year[0]
                if effective_year:
                    if len(effective_year) > 4:
                        effective_year = effective_year[0:4]

                    # print(f"File {file} is from {effective_year}")
                    if effective_year in playlists:
                        playlist = playlists[effective_year]
                    else:
                        playlist = Playlist(dir, prefix + effective_year + ".m3u")
                        playlists[effective_year] = playlist
                    playlist.add_song(sub)
                else:
                    songs_without_year.add_song(sub)

            except Exception as e:
                print(f"Error while reading tags from {sub}: {e}")
        # else:
        #     print(f"Unsupported file format {file}")


read_dir(dir)
print(f"Parse over, {count} songs found, will write playlists to disk")

for playlist in playlists:
    playlists[playlist].write_to_disk()
songs_without_year.write_to_disk()