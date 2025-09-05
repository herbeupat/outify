import tkinter as tk
from tkinter import filedialog

from simple_term_menu import TerminalMenu

from YT import YT
from utils import WARNING, ENDC

dialog_file_types = [ ("Audio files", ".mp3 .m4a") ]

class ManualSongSelector:
    def __init__(self, dir: str, search_limit: int):
        self.dir = dir
        self.yt_instance = YT(dir, search_limit)
        self.can_yt = self.yt_instance.can_run_basic()
        options = [
            "[m] enter manual path",
            "[d] open file dialog",
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
        while True:
            terminal_menu = TerminalMenu(self.menu_options, title=f"Song {artists} - {title} not found, what do you want to do ? ", cursor_index=self.last_index)
            selected = terminal_menu.show()
            self.last_index = selected
            choice = self.menu_options[selected][1:2]

            if choice == 's':
                print('Skipped')
                return None
            elif choice == 'm':
                path = input("Enter file path\n")
                if path.startswith(self.dir + '/'):
                    return path[len(self.dir) + 1:]
                else:
                    return path
            elif choice == 'd':
                root = tk.Tk()
                root.withdraw()

                file_path = filedialog.askopenfilename(initialdir=self.dir, filetypes=dialog_file_types)
                if file_path:
                    if file_path.startswith(self.dir + '/'):
                        return file_path[len(self.dir) + 1:]
                    else:
                        return file_path
            elif choice == 'y' and self.can_yt:
                url = input("Enter Youtube url\n")
                file = self.yt_instance.download(url, artists, album, track, title, year, album_cover_url, True)
                if file:
                    return file
                else:
                    print(f"{WARNING}Error while downloading Youtube file, try again{ENDC}")
            elif self.can_yt and YT.is_youtube_url(choice):
                file = self.yt_instance.download(choice, artists, album, track, title, year, album_cover_url, True)
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