import os
import threading
from time import sleep

from utils import *

class Playlist:

    def __init__(self, dir, name):
        self.dir = dir
        self.name = name
        self.list = []
        self.waiting_tasks = []
        self.thread = None
        self.print_thread_update_status = False


    def format_file_name(self, file_name: str):
        if file_name.startswith(self.dir + '/'):
            return file_name[len(self.dir) + 1:]
        return file_name


    def add_song(self, path):
        self.list.append(self.format_file_name(path))


    def add_waiting_song(self, task):
        self.waiting_tasks.append(
            {
                'task': task,
                'pos': len(self.list)
            }
        )
        self.list.append("WAITING_TASK")
        if not self.thread:
            self.thread = threading.Thread(target=self.process_waiting_tasks)
            self.thread.start()

    def process_waiting_tasks(self):
        while len(self.waiting_tasks) > 0:
            if self.print_thread_update_status:
                print(f"Processing waiting tasks, {len(self.waiting_tasks)} items left")
            item = self.waiting_tasks.pop(0)
            task = item['task']
            pos = item['pos']
            task_result = task()
            if task_result:
                self.list[pos] = self.format_file_name(task_result)
        self.thread = None
        if self.print_thread_update_status:
            print(f"Processing waiting tasks ended")


    def write_to_disk(self):
        self.print_thread_update_status = True
        if self.thread and self.thread.is_alive():
            print(f"\nWaiting for download thread to finish ({len(self.waiting_tasks) + 1} items left)")
        while self.thread and self.thread.is_alive():
            sleep(5)
        if len(self.list) == 0:
            print(f"{WARNING} Empty list, won't be saved{ENDC}")
            return
        playlist_path = self.dir + os.sep + self.name
        print("\nSaving playlist to " + playlist_path)
        playlist_file = open(playlist_path, 'w')
        playlist_file.write('#EXTM3U\n')
        for item in self.list:
            if item == 'WAITING_TASK':
                print(f"{WARNING} invalid item {item} won't be saved{ENDC}")
                continue
            playlist_file.write(item)
            playlist_file.write("\n")
        playlist_file.close()

