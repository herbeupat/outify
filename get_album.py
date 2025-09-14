import argparse
import spotipy
from simple_term_menu import TerminalMenu

from spotipy.oauth2 import SpotifyOAuth

from YT import YT

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--artist", required=True)
parser.add_argument("--album", required=True)
args=parser.parse_args()

dir = args.dir

scope = "user-library-read,playlist-read-private"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

yt_instance = YT(dir, 10, True)

def select_album(artist_name: str, album_name: str)-> dict | None:
    album_search_response = sp.search(artist_name + ' ' + album_name, type=['album'])
    possibilities = []
    for album in album_search_response['albums']['items']:
        possibilities.append(album['name'])

    terminal_menu = TerminalMenu(possibilities, title="Choose an album")
    selected = terminal_menu.show()
    if selected is None:
        return None
    return album_search_response['albums']['items'][selected]


selected_album = select_album(args.artist, args.album)
if selected_album is None:
    print('No album selected')
    exit(0)

album_tracks = sp.album(selected_album['id'])
yt_tracks = []
for i, track in enumerate(album_tracks['tracks']['items']):
    track_number = i + 1
    yt_tracks.append(track['name'])
    print(f"{track_number} {track['name']}")

yt = yt_instance.search_yt_album(args.artist, args.album, yt_tracks, album_tracks['release_date'], album_tracks['images'][0]['url'], True)