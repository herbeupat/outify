import spotipy
import argparse
import os
from time import sleep
from spotipy.oauth2 import SpotifyOAuth

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--playlist-prefix", default='outify-')
args=parser.parse_args()

dir = args.dir
playlist_prefix = args.playlist_prefix

scope = "user-library-read,playlist-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


def find_existing_song(dir, artist, album, track, title):
    exts = ['.mp3', '.m4a']
    for ext in exts:
        ext_path=find_existing_song_ext(dir, artist, album, track, title, ext)
        if ext_path:
            return ext_path
    artist_dir_exists = os.path.isdir(dir + '/' + artist)
    if artist_dir_exists:
        return find_recursive_track(dir + '/' + artist, track, title, exts)
    return None


def find_recursive_track(dir, track, title, exts):
    dir_content = os.listdir(dir)
    for file in dir_content:
        sub_dir = dir + '/' + file
        if os.path.isdir(sub_dir):
            recursive_dir_found = find_recursive_track(sub_dir, track, title, exts)
            if recursive_dir_found:
                return recursive_dir_found
        else:
            lowerfile = file.lower()
            for ext in exts:
                title_ext = title + ext
                str_track = str(track)
                lower_title_ext = title_ext.lower()
                if lowerfile == lower_title_ext:
                    return dir + '/' + title_ext
                elif lowerfile == str_track + ' ' + lower_title_ext:
                    return dir + '/' + str_track + ' ' + title_ext
                elif lowerfile == '0' + str_track + ' ' + lower_title_ext:
                    return dir + '/' + '0' + str_track + ' ' + title_ext

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


playlists = sp.current_user_playlists()
while playlists:
    for i, playlist in enumerate(playlists['items']):
        playlist_file_name=playlist_prefix + playlist['name'].replace('/', '_') + '.m3u'
        playlist_file=open(dir + '/' + playlist_file_name, 'w')
        playlist_file.write('#EXTM3U\n')

        print(f"{i + 1 + playlists['offset']:4d} {playlist['name']}")
        playlist_tracks = sp.playlist_items(playlist['uri'])
        print(f"Has {playlist_tracks['total']} songs")
        found=0
        while playlist_tracks:
            for i, track_item in enumerate(playlist_tracks['items']):
                track = track_item['track']
                if not track:
                    continue
                artist= track['artists'][0]['name']
                album= track['album']['name']
                title= track['name']
                track_number= track['track_number']
                existing_file = find_existing_song(dir, artist, album, track_number, title)
                if existing_file:
                    playlist_file.write(existing_file)
                    playlist_file.write('\n')
                    found = found + 1
            if playlist_tracks['next']:
                print('next')
                playlist_tracks = sp.next(playlist_tracks)
            else:
                playlist_tracks = None

        playlist_file.close()
        if found == 0:
            print('No tracks found, delete playlist')
            os.remove(dir + '/' + playlist_file_name)
        else:
            print(f"Found {found} tracks")
        exit(0)


    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None