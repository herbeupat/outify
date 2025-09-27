import argparse
import os
import shutil
from pathlib import Path

from utils import WARNING, ENDC

parser=argparse.ArgumentParser(description="Copy files from m3u files to destination dir, keeping structure, also copying m3u")
parser.add_argument("--source-dir", required=True)
parser.add_argument("--dest-dir", required=True)

parser.add_argument("m3u", action="extend", nargs="+")

args=parser.parse_args()
m3us = args.m3u
source_dir = args.source_dir
dest_dir = args.dest_dir

if not os.path.isdir(source_dir):
    print(f"{source_dir} does not exists or is not a directory")
    exit(-1)
if not os.path.isdir(dest_dir):
    print(f"{dest_dir} does not exists or is not a directory")
    exit(-1)


print(f"Will copy songs from {len(m3us)} m3u files from {source_dir} to {dest_dir}")

for m3u in m3us:
    try:
        source_m3u = source_dir + os.sep + m3u
        if not os.path.isfile(source_m3u):
            print(f"{WARNING}{m3u} does not exists in {source_dir} or is not a file")
            continue
        print(f"Processing {m3u}")
        playlist_file = open(source_m3u, 'r')
        for line in playlist_file:
            try:
                correct_line = line.strip() # because of trailing \n
                if correct_line == '#EXTM3U':
                    continue
                source_file = source_dir + os.sep + correct_line
                if not os.path.isfile(source_file):
                    continue
                dest_file = dest_dir + os.sep + correct_line
                if os.path.isfile(dest_file):
                    continue
                dest_file_parent_dir = Path(dest_file).parent
                if not dest_file_parent_dir.exists():
                    os.makedirs(dest_file_parent_dir.absolute())
                shutil.copy(source_file, dest_file)
            except:
                print(f"{WARNING}Error while copying {line}{ENDC}")


        shutil.copy(source_m3u, dest_dir + os.sep + m3u)
    except:
        print(f"{WARNING} Error while reading {m3u}{ENDC}")

