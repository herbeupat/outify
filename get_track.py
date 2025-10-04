import argparse

from YT import YT

parser=argparse.ArgumentParser(description="Outify")
parser.add_argument("--dir", required=True)
parser.add_argument("--artist", required=True)
parser.add_argument("--album", required=True)
parser.add_argument("--title", required=True)
parser.add_argument("--year")
parser.add_argument("--cookies-from-browser", help='Set option "--cookies-from-browser" for yt-dlp')
parser.add_argument("url")
args=parser.parse_args()

dir = args.dir



yt_instance = YT(dir, 10, True, args.cookies_from_browser)
#  url: str, artists: list[str], album: str, track: int, title: str, year: str | None, image_url: str | None, output:bool) -> str | None:
yt_instance.download(args.url, [args.artist], args.album, 0, args.title, args.year, None, True)