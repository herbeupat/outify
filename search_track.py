import argparse

from TD import TD
from YT import YT
from Playlist import Playlist
from utils import WARNING, ENDC

parser=argparse.ArgumentParser(description="Search track and download it")
parser.add_argument("--dir", required=True)
parser.add_argument("--source", "-s", choices=("td", "yt"), default="yt")
parser.add_argument("--add-to-playlist", "-p", action='append')
parser.add_argument("--cookies-from-browser", help='Set option "--cookies-from-browser" for yt-dlp')
parser.add_argument("query")
args=parser.parse_args()

dir = args.dir
source = args.source
add_to_playlist = args.add_to_playlist
query = args.query

if source == "td":
    print(f"{WARNING}TD not supported yet{ENDC}")
elif source == "yt":
    yt_instance = YT(dir, 10, True, args.cookies_from_browser)
    downloaded_file_path = yt_instance.search_and_download(query)
else:
    print(f"{WARNING}unknown source {source}{ENDC}")
    exit(-1)




if downloaded_file_path and add_to_playlist:
    for playlist_file in add_to_playlist:
        print(f"Adding song to playlist {playlist_file}")
        playlist = Playlist(dir, playlist_file, True)
        playlist.add_song(downloaded_file_path)
        playlist.write_to_disk()