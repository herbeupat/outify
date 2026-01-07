import argparse

from YT import YT

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--track", required=True)
parser.add_argument("url")
parser.add_argument("--cookies-from-browser", help='Set option "--cookies-from-browser" for yt-dlp')

args=parser.parse_args()

track = args.track
url = args.url



yt_instance = YT("/tmp", 10, True, args.cookies_from_browser)
yt_instance.replace_file(track, url)