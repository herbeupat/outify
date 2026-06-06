import configparser
import io
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
from urllib.parse import urlparse

from Playlist import Playlist
from SC import SC
from YT import YT
from utils import sanitize_file_name

dialog_playlist_types = [("M3U playlists", "*.m3u")]
SETTINGS_PATH = Path(__file__).resolve().parent / "settings.ini"


def is_soundcloud_url(url: str) -> bool:
    hostname = urlparse(url).hostname
    if not hostname:
        return False
    hostname = hostname.lower()
    return hostname == "soundcloud.com" or hostname.endswith(".soundcloud.com")


class GetTrackGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Outify — Get Track")
        self.root.minsize(520, 640)

        self.playlists: list[str] = []
        self._build_form()
        self._load_settings()
        self._build_output()
        self._build_actions()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _select_all_text(event):
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        return "break"

    def _labeled_entry(self, parent: ttk.Frame, label: str, row: int, **entry_kwargs) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        entry = ttk.Entry(parent, **entry_kwargs)
        entry.grid(row=row, column=1, sticky="ew", pady=4)
        entry.bind("<Control-a>", self._select_all_text)
        entry.bind("<Control-A>", self._select_all_text)
        return entry

    def _build_form(self):
        form = ttk.Frame(self.root, padding=12)
        form.grid(row=0, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.dir_entry = self._labeled_entry(form, "Music library (--dir) *", 0)
        ttk.Button(form, text="Browse…", command=self._browse_dir).grid(row=0, column=2, padx=(8, 0), pady=4)

        self.artist_entry = self._labeled_entry(form, "Artist (-a) *", 1)
        self.album_entry = self._labeled_entry(form, "Album (-l) *", 2)
        self.title_entry = self._labeled_entry(form, "Title (-t) *", 3)
        self.year_entry = self._labeled_entry(form, "Year (-y)", 4)
        self.track_entry = self._labeled_entry(form, "Track (-k)", 5, width=8)

        self.cookies_entry = self._labeled_entry(form, "Cookies from browser", 6)
        ttk.Label(
            form,
            text='yt-dlp "--cookies-from-browser" value (e.g. chrome)',
            font=("", 8),
        ).grid(row=7, column=1, sticky="w", pady=(0, 4))

        self.cover_entry = self._labeled_entry(form, "Cover URL (-c)", 8)

        self.url_entry = self._labeled_entry(form, "URL *", 9)

        playlist_frame = ttk.LabelFrame(form, text="Add to playlist (-p)", padding=8)
        playlist_frame.grid(row=10, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        playlist_frame.columnconfigure(0, weight=1)

        self.playlist_listbox = tk.Listbox(playlist_frame, height=4)
        self.playlist_listbox.grid(row=0, column=0, sticky="nsew")
        self.playlist_listbox.bind("<Delete>", lambda _event: self._remove_playlist())

        playlist_buttons = ttk.Frame(playlist_frame)
        playlist_buttons.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        ttk.Button(playlist_buttons, text="New…", command=self._create_playlist).pack(fill="x", pady=(0, 4))
        ttk.Button(playlist_buttons, text="Add existing…", command=self._add_playlist).pack(fill="x", pady=(0, 4))
        ttk.Button(playlist_buttons, text="Remove", command=self._remove_playlist).pack(fill="x")

    def _build_output(self):
        output_frame = ttk.LabelFrame(self.root, text="Output", padding=12)
        output_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output = scrolledtext.ScrolledText(output_frame, height=12, state="disabled", wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew")

    def _build_actions(self):
        actions = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        actions.grid(row=2, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)

        self.clear_button = ttk.Button(actions, text="Clear", command=self._clear_fields)
        self.clear_button.grid(row=0, column=1, sticky="e", padx=(0, 8))
        self.download_button = ttk.Button(actions, text="Download", command=self._start_download)
        self.download_button.grid(row=0, column=2, sticky="e")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Select music library directory")
        if path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, path)

    def _load_settings(self):
        if not SETTINGS_PATH.is_file():
            return
        config = configparser.ConfigParser()
        config.read(SETTINGS_PATH)
        music_dir = config.get("defaults", "dir", fallback="").strip()
        if music_dir:
            self.dir_entry.insert(0, music_dir)
        cookies_from_browser = config.get("defaults", "cookies_from_browser", fallback="").strip()
        if cookies_from_browser:
            self.cookies_entry.insert(0, cookies_from_browser)

    def _save_settings(self):
        config = configparser.ConfigParser()
        config["defaults"] = {
            "dir": self.dir_entry.get().strip(),
            "cookies_from_browser": self.cookies_entry.get().strip(),
        }
        with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
            config.write(settings_file)

    def _on_close(self):
        self._save_settings()
        self.root.destroy()

    def _playlist_path_relative_to_dir(self, path: str) -> str | None:
        music_dir = self.dir_entry.get().strip()
        if not music_dir:
            messagebox.showerror("Music library required", "Set the music library directory before adding a playlist.")
            return None
        music_path = Path(music_dir).resolve()
        selected = Path(path).resolve()
        try:
            return str(selected.relative_to(music_path))
        except ValueError:
            messagebox.showerror(
                "Invalid playlist",
                "The playlist must be inside the music library directory.",
            )
            return None

    def _insert_playlist(self, relative_path: str):
        if relative_path not in self.playlists:
            self.playlists.append(relative_path)
            self.playlist_listbox.insert(tk.END, relative_path)

    def _add_playlist(self):
        path = filedialog.askopenfilename(
            title="Select playlist",
            filetypes=dialog_playlist_types,
            initialdir=self.dir_entry.get() or None,
        )
        if not path:
            return
        relative_path = self._playlist_path_relative_to_dir(path)
        if relative_path:
            self._insert_playlist(relative_path)

    def _create_playlist(self):
        music_dir = self.dir_entry.get().strip()
        if not music_dir:
            messagebox.showerror("Music library required", "Set the music library directory before creating a playlist.")
            return

        name = simpledialog.askstring("New playlist", "Playlist name:", parent=self.root)
        if not name or not name.strip():
            return

        sanitized = sanitize_file_name(name.strip())
        if not sanitized:
            messagebox.showerror("Invalid playlist name", "Playlist name cannot be empty.")
            return

        playlist_name = sanitized if sanitized.endswith(".m3u") else f"{sanitized}.m3u"
        playlist_path = Path(music_dir) / playlist_name

        if playlist_path.exists():
            if not messagebox.askyesno(
                "Playlist exists",
                f"{playlist_name} already exists. Add it to the list?",
                parent=self.root,
            ):
                return
        else:
            playlist_path.write_text("#EXTM3U\n", encoding="utf-8")

        self._insert_playlist(playlist_name)

    def _remove_playlist(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self.playlist_listbox.delete(index)
        del self.playlists[index]

    def _append_output(self, text: str):
        self.output.configure(state="normal")
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def _set_running(self, running: bool):
        state = "disabled" if running else "normal"
        self.download_button.configure(state=state)

    def _clear_fields(self):
        for entry in (
            self.artist_entry,
            self.album_entry,
            self.title_entry,
            self.year_entry,
            self.track_entry,
            self.cover_entry,
            self.url_entry,
        ):
            entry.delete(0, tk.END)

    def _validate(self) -> dict | None:
        dir_path = self.dir_entry.get().strip()
        artist = self.artist_entry.get().strip()
        album = self.album_entry.get().strip()
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()

        missing = []
        if not dir_path:
            missing.append("--dir")
        if not artist:
            missing.append("--artist")
        if not album:
            missing.append("--album")
        if not title:
            missing.append("--title")
        if not url:
            missing.append("url")

        if missing:
            messagebox.showerror("Missing required fields", "Required: " + ", ".join(missing))
            return None

        track_text = self.track_entry.get().strip() or "0"
        try:
            track = int(track_text)
        except ValueError:
            messagebox.showerror("Invalid track number", "Track (-k) must be an integer.")
            return None

        year = self.year_entry.get().strip() or None
        cookies = self.cookies_entry.get().strip() or None
        cover = self.cover_entry.get().strip() or None

        return {
            "dir": dir_path,
            "artist": artist,
            "album": album,
            "title": title,
            "year": year,
            "track": track,
            "cookies_from_browser": cookies,
            "cover": cover,
            "url": url,
            "add_to_playlist": list(self.playlists),
        }

    def _start_download(self):
        args = self._validate()
        if args is None:
            return

        self._append_output("\n--- Starting download ---\n")
        self._set_running(True)
        thread = threading.Thread(target=self._run_download, args=(args,), daemon=True)
        thread.start()

    def _run_download(self, args: dict):
        buffer = io.StringIO()
        previous_stdout = sys.stdout
        sys.stdout = buffer

        error_message = None
        try:
            download_args = (
                args["url"],
                [args["artist"]],
                args["album"],
                args["track"],
                args["title"],
                args["year"],
                args["cover"],
                True,
            )
            if is_soundcloud_url(args["url"]):
                downloader = SC(args["dir"])
            else:
                downloader = YT(args["dir"], 10, True, args["cookies_from_browser"])
            downloaded_file_path = downloader.download(*download_args)

            if downloaded_file_path and args["add_to_playlist"]:
                for playlist_file in args["add_to_playlist"]:
                    print(f"Adding song to playlist {playlist_file}")
                    playlist = Playlist(args["dir"], playlist_file, True)
                    playlist.add_song(downloaded_file_path)
                    playlist.write_to_disk()
            elif downloaded_file_path:
                print(f"Downloaded: {downloaded_file_path}")
            else:
                print("Download failed or file already exists.")
        except Exception as exc:
            error_message = str(exc)
        finally:
            sys.stdout = previous_stdout

        output = buffer.getvalue()
        self.root.after(0, lambda: self._finish_download(output, error_message))

    def _finish_download(self, output: str, error_message: str | None):
        if output:
            self._append_output(output)
        if error_message:
            self._append_output(f"\nError: {error_message}\n")
            messagebox.showerror("Download failed", error_message)
        self._append_output("--- Done ---\n")
        self._set_running(False)


def main():
    root = tk.Tk()
    GetTrackGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
