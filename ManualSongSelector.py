import logging
import tkinter as tk
from tkinter import filedialog

from simple_term_menu import TerminalMenu

from YT import YT
from utils import WARNING, ENDC, exts
import os

dialog_file_types = [ ("Audio files", ".mp3 .m4a") ]

class ManualSongSelector:
    def __init__(self, dir: str, search_limit: int, force_sync_download: bool):
        self.dir = dir
        self.yt_instance = YT(dir, search_limit, force_sync_download)
        self.can_yt = self.yt_instance.can_run_basic()
        self.logger = logging.getLogger(__name__)
        options = [
            "[m] enter manual path",
            "[d] open file dialog",
            "[l] list all files in directories named with the artist(s)",
            "[q] stop for now and quit",
            "[s] skip song",
            "[t] skip all missing songs in this playlist",
        ]
        if self.can_yt:
            options.append("[y] from Youtube URL (you may also directly paste Youtube URL)")
            options.append("[z] search from Youtube music")
        self.menu_options = options
        self.last_index = 0

    def get_manual_song(self, title, album, artists, track, year, album_cover_url):
        song = f"{', '.join(artists)} - {title} (From album: {album} year: ({year}))"
        print("")
        while True:
            terminal_menu = TerminalMenu(self.menu_options, title=f"Song {song} not found, what do you want to do ? ", cursor_index=self.last_index)
            selected = terminal_menu.show()
            if selected is None:
                os.system("reset")
                continue
            self.last_index = selected
            choice = self.menu_options[selected][1:2]

            if choice == 's':
                print('Skipped')
                return None
            elif choice == 'm':
                os.system('reset') # required because conflict with the menu
                path = input(f"Enter file path for {song}\n")
                if os.path.exists(path):
                    if path.startswith(self.dir + '/'):
                        return path[len(self.dir) + 1:]
                    else:
                        return path
                else:
                    print(f"{WARNING} invalid path {path} {ENDC}")
                    continue
            elif choice == 'd':
                root = tk.Tk()
                root.withdraw()
                print(f"Choose a file for {song}")
                file_path = filedialog.askopenfilename(initialdir=self.dir, filetypes=dialog_file_types)
                if file_path:
                    return file_path
            elif choice == 'l':
                file = self.get_from_artists_files(artists, song)
                if file:
                    return file
            elif choice == 'y' and self.can_yt:
                os.system('reset') # required because conflict with the menu
                url = input("Enter Youtube url\n")
                file = self.yt_instance.try_download(url, artists, album, track, title, year, album_cover_url, True)
                if file:
                    return file
                else:
                    print(f"{WARNING}Error while downloading Youtube file, try again{ENDC}")
            elif self.can_yt and choice == 'z':
                file = self.yt_instance.search_yt_music(artists, album, track, title, year, album_cover_url)
                if file:
                    return file
            elif choice == 'q':
                return 'BEFORE_EXIT'
            elif choice == 't':
                return 'SKIP_FOR_CURRENT_PLAYLIST'
            else:
                print(f"Wrong choice {choice}")


    def get_from_artists_files(self, artists: list[str], song: str) -> str | None:
        possibilities = []
        lower_artists = list(map(lambda artist: artist.lower(), artists))

        for subdir in os.listdir(self.dir):
            subdir_path = self.dir + os.sep + subdir
            if os.path.isdir(subdir_path):
                lower = subdir.lower()
                for artist in lower_artists:
                    if lower.startswith(artist):
                        possibilities = possibilities + self.get_files_inside(subdir_path)

        if len(possibilities) == 0:
            print('No artist directory found')
            return None

        terminal_menu = TerminalMenu(possibilities, title=f"Select a file for {song}:")
        selected = terminal_menu.show()
        if selected is None:
            return None
        return possibilities[selected]

    def get_files_inside(self, dir: str) -> list[str]:
        accumulator = []
        for sub in os.listdir(dir):
            sub_path = dir + os.sep + sub
            if os.path.isfile(sub_path):
                if any(map(lambda ext: sub_path.endswith(ext), exts)):
                    accumulator.append(sub_path)
            elif os.path.isdir(sub_path):
                accumulator = accumulator + self.get_files_inside(sub_path)
        return accumulator

    def set_batch_output(self, value: bool):
        self.yt_instance.set_batch_output(value)