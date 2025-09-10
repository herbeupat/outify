
WARNING = '\033[93m'
ENDC = '\033[0m'

exts = ['.mp3', '.m4a']


def sanitize_file_name(file_name: str):
    return file_name.replace("/", "_").replace("\\", "_").strip()