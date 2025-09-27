import argparse
import spotipy
from simple_term_menu import TerminalMenu

from spotipy.oauth2 import SpotifyOAuth

from YT import YT

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--artist", required=True)
parser.add_argument("--album", required=True)
parser.add_argument("--year")
parser.add_argument("--cookies-from-browser", help='Set option "--cookies-from-browser" for yt-dlp')
args=parser.parse_args()

dir = args.dir

scope = "user-library-read,playlist-read-private"
scope = ''
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
except:
    print('Cannot initialize Spotipy, will ignore getting metadata from it')
    sp = None

yt_instance = YT(dir, 10, True, args.cookies_from_browser)

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

if sp:
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

    effective_artist = album_tracks['artists'][0]['name']
    effective_album = album_tracks['name']
    release_date = album_tracks['release_date']
    album_cover = album_tracks['images'][0]['url']
else:
    effective_artist = args.artist
    effective_album = args.album
    yt_tracks = []
    release_date = args.year
    album_cover = None

yt = yt_instance.search_yt_album(effective_artist, effective_album, yt_tracks, release_date, album_cover, True)