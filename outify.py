import json
import logging

import spotipy
import argparse
import os
import re
from spotipy.oauth2 import SpotifyOAuth

from ManualSongSelector import ManualSongSelector
from Playlist import Playlist
from utils import *

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--playlist", help='Only import this playlist')
parser.add_argument("--playlist-prefix", default='outify-')
parser.add_argument("--auto", action='store_true')
parser.add_argument("--only-self", action='store_true')
parser.add_argument("--force-sync-download", action='store_true')
parser.add_argument("--debug", action='store_true')
parser.add_argument("--search-limit", type=int, default=10)
args=parser.parse_args()

dir = args.dir
playlist_prefix = args.playlist_prefix
auto = args.auto
single_playlist = args.playlist
force_sync_download = args.force_sync_download
debug = args.debug

logger = logging.getLogger(__name__)
level = logging.DEBUG if args.debug else logging.INFO
logging.basicConfig(filename='outify.log', level=level)


only_self = args.only_self
overrides = {
    'skip_for_current_playlist': auto
}
search_limit = args.search_limit

scope = "user-library-read,playlist-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

self_id=sp.current_user()['id']

logger.debug(f"self profile id is {self_id}")

suffixes_regex='( - | \\(| \\[).*(remaster|radio edit|original mix|version).*\\)?\\]?'
exts_regex= '(\\.mp3|\\.m4a)'

database = {}

session_cache={}
exclude_cache=[]

database_path = dir + '/.outify_database.json'
if os.path.isfile(database_path):
    database_file = open(database_path, 'r')
    database = json.load(database_file)

if 'songs_to_files' in database:
    songs_to_files = database['songs_to_files']
else:
    songs_to_files = {}
    database['songs_to_files'] = songs_to_files

if 'exclude_cache' in database:
    exclude_cache = database['exclude_cache']
else:
    exclude_cache = []
    database['exclude_cache'] = exclude_cache

manual_song = ManualSongSelector(dir, search_limit, force_sync_download)

def before_exit():
    database_file = open(database_path, 'w')
    json.dump(database, database_file)


def find_existing_song(dir: str, artist: str, album: str, track, title: str) -> str | None:
    for ext in exts:
        ext_path=find_existing_song_ext(dir, artist, album, track, title, ext)
        if ext_path:
            return ext_path
    artist_dir_exists = os.path.isdir(dir + '/' + artist)
    if artist_dir_exists:
        recursive_track = find_recursive_track(dir + '/' + artist, title)
        if recursive_track:
            return recursive_track[len(dir)+1:]
    return None


def clean_title(title: str) -> str:
    suffix=re.search(suffixes_regex, title, re.IGNORECASE)
    if suffix:
        return re.sub(suffixes_regex, '', title, flags=re.IGNORECASE)
    return title

def find_recursive_track(dir: str, title: str) -> str | None:
    dir_content = os.listdir(dir)
    for file in dir_content:
        sub_dir = dir + '/' + file
        if os.path.isdir(sub_dir):
            recursive_dir_found = find_recursive_track(sub_dir, title)
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
        manual_song.set_batch_output(False)

        current_playlist = Playlist(dir, playlist_prefix + sanitize_file_name(playlist['name']) + '.m3u')
        playlist_tracks = sp.playlist_items(playlist['uri'])
        while playlist_tracks:
            total = playlist_tracks['total']
            offset = playlist_tracks['offset']
            for i, track_item in enumerate(playlist_tracks['items']):
                track = track_item['track']
                if not track:
                    continue

                track_id = track['id']
                if track_id is None:
                    track_id = track['uri'] # for Spotify local files
                if track_id in exclude_cache:
                    print(f"\n{WARNING}Excluded song{ENDC} {title}, will be skipped")
                    continue
                
                album= track['album']['name']
                title= track['name']
                track_number= track['track_number']
                artist_names= list(map(lambda artist: artist['name'], track['artists']))
                possibilities = artists_combinations(artist_names)
                print(f"\rSearching for {offset + i + 1}/{total} {possibilities[0]} - {title}", end='')
                current_found = None
                from_cache = session_cache.get(track_id)
                if from_cache:
                    if from_cache == 'NOT_FOUND':
                        continue
                    current_found = from_cache
                    current_playlist.add_song(current_found)
                    continue

                for artist in possibilities:
                    current_found = find_existing_song(dir, artist, album, track_number, title)
                    if current_found:
                        break
                    else:
                        ctitle = clean_title(title)
                        if ctitle != title:
                            current_found = find_existing_song(dir, artist, album, track_number, ctitle)
                            if current_found:
                                break

                if not current_found:
                    existing_in_mapping = songs_to_files.get(track_id, None)
                    if existing_in_mapping:
                        if os.path.exists(existing_in_mapping):
                            current_found = existing_in_mapping
                        elif os.path.exists(dir + '/' + existing_in_mapping):
                            current_found = existing_in_mapping

                skip_for_current_playlist = overrides['skip_for_current_playlist']

                if not current_found:
                    if not skip_for_current_playlist:
                        year = track['album']['release_date']
                        album_cover_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                        current_found = manual_song.get_manual_song(title, album, artist_names, track_number, year, album_cover_url)
                        logger.debug(f"Current found value is {current_found}")
                        if current_found == 'BEFORE_EXIT':
                            manual_song.set_batch_output(True)
                            current_playlist.write_to_disk()
                            before_exit()
                            exit(0)
                        elif current_found == 'SKIP_FOR_CURRENT_PLAYLIST':
                            overrides['skip_for_current_playlist'] = True
                        elif current_found == 'EXCLUDE_TRACK':
                            exclude_cache.append(track_id) 
                        elif callable(current_found):
                            current_playlist.add_waiting_song(current_found)
                            current_found = None
                        elif current_found:
                            songs_to_files[track_id] = current_playlist.format_file_name(current_found)

                    else:
                        print(f"{WARNING} Song not found {ENDC}")

                if current_found:
                    current_playlist.add_song(current_found)
                    session_cache[track_id] = current_found
                else:
                    session_cache[track_id] = 'NOT_FOUND'


            if playlist_tracks['next']:
                playlist_tracks = sp.next(playlist_tracks)
            else:
                manual_song.set_batch_output(True)
                current_playlist.write_to_disk()
                playlist_tracks = None




    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None

before_exit()