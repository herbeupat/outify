import argparse
from utils import *
import os 

from Playlist import Playlist
from mutagen.easyid3 import EasyID3

parser=argparse.ArgumentParser(description="Sort tracks per year, creating one playlist per year")
parser.add_argument("--dir", required=True)
parser.add_argument("--playlist-prefix", default='yaer-')
args=parser.parse_args()

dir = args.dir

playlists = {}

def read_dir(dir_name):
    for file in os.listdir(dir_name):
        sub= dir_name + '/' + file
        if os.path.isdir(sub):
            read_dir(sub)
        elif file.endswith('.mp3'):
            try:
                tag_file = EasyID3(sub)
                if date in tag_file
                year = tag_file['date']
                if year and len(year) > 0:
                    effective_year = year[0]
                    if len(effective_year) > 4:
                        effective_year = effective_year[0:4]
                    
                    print(f"File {file} is from {effective_year}")
                    if effective_year in playlists:
                        playlist = playlists[effective_year]
                    else:
                        playlist = Playlist(dir, effective_year + ".m3u")
                        playlists[effective_year] = playlist
                    playlist.add_song(sub)
            except:
                print(f"Error while reading tags from {sub}")
        else:
            print(f"Unsupported file format {file}")


read_dir(dir)