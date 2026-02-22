import argparse

from YT import YT
from Playlist import Playlist

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--artist", "-a", required=True)
parser.add_argument("--album", "-l", required=True)
parser.add_argument("--title", "-t", required=True)
parser.add_argument("--year", "-y")
parser.add_argument("--cookies-from-browser", help='Set option "--cookies-from-browser" for yt-dlp')
parser.add_argument("--add-to-playlist", "-p", action='append')
parser.add_argument("url")
args=parser.parse_args()

dir = args.dir
add_to_playlist = args.add_to_playlist


yt_instance = YT(dir, 10, True, args.cookies_from_browser)
downloaded_file_path = yt_instance.download(args.url, [args.artist], args.album, 0, args.title, args.year, None, True)

if downloaded_file_path and add_to_playlist:
    for playlist_file in add_to_playlist:
        print(f"Adding song to playlist {playlist_file}")
        playlist = Playlist(dir, playlist_file, True)
        playlist.add_song(downloaded_file_path)
        playlist.write_to_disk()