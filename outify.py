import json
import logging

import spotipy
import argparse
import os
import re
from time import sleep
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
from tkinter import filedialog

import utils
from utils import *
from YT import YT

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--playlist", help='Only import this playlist')
parser.add_argument("--playlist-prefix", default='outify-')
parser.add_argument("--auto", action='store_true')
parser.add_argument("--only-self", action='store_true')
parser.add_argument("--search-limit", type=int, default=10)
args=parser.parse_args()

dir = args.dir
playlist_prefix = args.playlist_prefix
auto = args.auto
single_playlist = args.playlist
only_self = args.only_self
overrides = {
    'skip_for_current_playlist': auto
}
search_limit = args.search_limit

scope = "user-library-read,playlist-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

self_id=sp.current_user()['id']
logging.debug(f"self profile id is {self_id}")

exts = ['.mp3', '.m4a']
dialog_file_types = [ ("Audio files", ".mp3 .m4a") ]

suffixes_regex='( - | \\().*(remaster|radio edit|original mix|version).*\\)?'
exts_regex= '(\\.mp3|\\.m4a)'

database = {}

database_path = dir + '/.outify_database.json'
if os.path.isfile(database_path):
    database_file = open(database_path, 'r')
    database = json.load(database_file)

if 'songs_to_files' in database:
    songs_to_files = database['songs_to_files']
else:
    songs_to_files = {}
    database['songs_to_files'] = songs_to_files


YT = YT(dir, search_limit)
can_yt = YT.can_run_basic()

def before_exit():
    database_file = open(database_path, 'w')
    json.dump(database, database_file)


def find_existing_song(dir, artist, album, track, title):
    for ext in exts:
        ext_path=find_existing_song_ext(dir, artist, album, track, title, ext)
        if ext_path:
            return ext_path
    artist_dir_exists = os.path.isdir(dir + '/' + artist)
    if artist_dir_exists:
        recursive_track = find_recursive_track(dir + '/' + artist, track, title)
        if recursive_track:
            return recursive_track[len(dir)+1:]
    return None


def clean_title(title):
    suffix=re.search(suffixes_regex, title, re.IGNORECASE)
    if suffix:
        return re.sub(suffixes_regex, '', title, flags=re.IGNORECASE)
    return title

def find_recursive_track(dir, track, title):
    dir_content = os.listdir(dir)
    for file in dir_content:
        sub_dir = dir + '/' + file
        if os.path.isdir(sub_dir):
            recursive_dir_found = find_recursive_track(sub_dir, track, title)
            if recursive_dir_found:
                return recursive_dir_found
        else:
            regexp_compatible_title = title.replace("\\", "\\\\").replace("*", "\\*").replace("(", "\\(").replace(")", "\\)")
            regexp = '^([0-9\\- ]+ )?' + regexp_compatible_title + '(' + suffixes_regex + ')?' + exts_regex + '$'
            if re.search(regexp, file, re.IGNORECASE):
                return dir + '/' + file

    return None


def find_existing_song_ext(dir, artist, album, track, title, ext):
    test_path = f"{artist}/{album}/{track} {title}{ext}"
    if os.path.exists(dir + '/' + test_path):
        return test_path
    test_path = f"{artist}/{album}/0{track} {title}{ext}"
    if os.path.exists(dir + '/' + test_path):
        return test_path
    test_path = f"{artist}/{album}/{title}{ext}"
    if os.path.exists(dir + '/' + test_path):
        return test_path
    return False


def artists_combinations(artist_objects):
    list_length = len(artist_objects)
    if list_length == 1:
        return artist_objects
    combine_chars= [' & ', ', ']
    possibilites = []
    if list_length == 2:
        possibilites.append(artist_objects[0])
        possibilites.append(artist_objects[1])
        for char in combine_chars:
            possibilites.append(artist_objects[0] + char + artist_objects[1])
            possibilites.append(artist_objects[1] + char + artist_objects[0])
    elif list_length > 4:
        print(f"\n{WARNING}List too long for combinations, will only use 4 first artists: {artist_objects}{ENDC}")
        return artists_combinations(artist_objects[0:4])
    else:
        # not optimal but works for now
        for i in range(0, list_length):
            current = artist_objects[i]
            part = artist_objects[0:i] + artist_objects[i + 1:len(artist_objects)]
            new_combinations = artists_combinations(part)
            possibilites = possibilites + new_combinations
            for nc in new_combinations:
                for char in combine_chars:
                    possibilites.append(nc + char + current)
                    possibilites.append(current + char + nc)
            possibilites = list(set(possibilites))
        # to clear duplicates
        possibilites = list(set(possibilites))

    return possibilites


def get_manual_song(dir, title, album, artists, track, year, album_cover_url):
    while True:
        print(f"\nSong {artists} - {title} not found, what do you want to do ? ")
        print("s - skip song")
        print("m - enter manual path")
        print("d - open file dialog")
        print("q - stop for now, quit")
        print("sp - skip all missing song in this playlist")
        if can_yt:
            print("y - from Youtube URL (you may also directly paste Youtube URL)")
            print("ys - search from Youtube music")
        choice = input("Enter s, m, q, sp, y, ys or d\n")
        if choice == 's':
            print('Skipped')
            return None
        elif choice == 'm':
            path = input("Enter file path\n")
            if path.startswith(dir + '/'):
                return path[len(dir)+1:]
            else:
                return path
        elif choice == 'd':
            root = tk.Tk()
            root.withdraw()

            file_path = filedialog.askopenfilename(initialdir=dir, filetypes=dialog_file_types)
            if file_path:
                if file_path.startswith(dir + '/'):
                    return file_path[len(dir)+1:]
                else:
                    return file_path
        elif choice == 'y' and can_yt:
            url = input("Enter Youtube url\n")
            file = YT.download(url, artists, album, track, title, year, album_cover_url)
            if file:
                return file
            else:
                print(f"{WARNING}Error while downloading Youtube file, try again{ENDC}")
        elif can_yt and YT.is_youtube_url(choice):
            file = YT.download(choice, artists, album, track, title, year, album_cover_url)
            if file:
                return file
            else:
                print(f"{WARNING}Error while downloading Youtube file, try again{ENDC}")
        elif can_yt and choice == 'ys':
            file = YT.search_yt_music(artists, album, track, title, year, album_cover_url)
            if file:
                return file
        elif choice == 'q':
            before_exit()
            exit(0)
        elif choice == 'sp':
            overrides['skip_for_current_playlist'] = True
            print(f"{WARNING} skip all following missing files from this playlist{ENDC}")
            return None
        else:
            print(f"Wrong choice {choice}")

if single_playlist:
    print(f"Will only process playlist named {single_playlist}")

playlists = sp.current_user_playlists()
while playlists:
    for i, playlist in enumerate(playlists['items']):
        if single_playlist:
            if playlist['name'] != single_playlist:
                continue
            else:
                print('Importing single playlist ' + single_playlist)
        print(f"{i + 1 + playlists['offset']:4d} - {playlist['name']} - has {playlist['tracks']['total']} songs")
        if only_self:
            is_self = playlist['owner']['id'] == self_id
            if not is_self:
                print('Skip not self playlist')
                continue

        # reset overrides
        overrides['skip_for_current_playlist'] = auto

        playlist_file_name=playlist_prefix + playlist['name'].replace('/', '_') + '.m3u'
        playlist_file=open(dir + '/' + playlist_file_name, 'w')
        playlist_file.write('#EXTM3U\n')

        playlist_tracks = sp.playlist_items(playlist['uri'])
        found=0
        while playlist_tracks:
            total = playlist_tracks['total']
            offset = playlist_tracks['offset']
            for i, track_item in enumerate(playlist_tracks['items']):
                track = track_item['track']
                if not track:
                    continue
                album= track['album']['name']
                title= track['name']
                track_number= track['track_number']
                artist_names= list(map(lambda artist: artist['name'], track['artists']))
                possibilities = artists_combinations(artist_names)
                print(f"\rSearching for {offset + i + 1}/{total} {possibilities[0]} - {title}", end='')
                current_found = False
                for artist in possibilities:
                    existing_file = find_existing_song(dir, artist, album, track_number, title)
                    if existing_file:
                        playlist_file.write(existing_file)
                        playlist_file.write('\n')
                        found = found + 1
                        current_found = True
                        break
                    else:
                        ctitle = clean_title(title)
                        if ctitle != title:
                            existing_file = find_existing_song(dir, artist, album, track_number, ctitle)
                            if existing_file:
                                playlist_file.write(existing_file)
                                playlist_file.write('\n')
                                found = found + 1
                                current_found = True
                                break

                if not current_found:
                    existing_in_mapping = songs_to_files.get(track['id'], None)
                    if existing_in_mapping:
                        if os.path.exists(existing_in_mapping):
                            playlist_file.write(existing_in_mapping)
                            playlist_file.write('\n')
                            found = found + 1
                            current_found = True
                        elif os.path.exists(dir + '/' + existing_in_mapping):
                            playlist_file.write(existing_in_mapping)
                            playlist_file.write('\n')
                            found = found + 1
                            current_found = True

                skip_for_current_playlist = overrides['skip_for_current_playlist']

                if not current_found:
                    if not skip_for_current_playlist:
                        year = track['album']['release_date']
                        album_cover_url = track['album']['images'][0]['url']
                        manual_value = get_manual_song(dir, title, album, artist_names, track_number, year, album_cover_url)
                        if manual_value:
                            playlist_file.write(manual_value)
                            found = found + 1
                            songs_to_files[track['id']] = manual_value
                            playlist_file.write('\n')
                    else:
                        print(f"{WARNING} Song not found {ENDC}")


            if playlist_tracks['next']:
                playlist_tracks = sp.next(playlist_tracks)
            else:
                playlist_tracks = None

        playlist_file.close()
        if found == 0:
            print('\rNo tracks found, delete playlist')
            os.remove(dir + '/' + playlist_file_name)
        else:
            print(f"\rFound {found} tracks")


    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None

before_exit()