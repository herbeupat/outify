import os.path

WARNING = '\033[93m'
ENDC = '\033[0m'

exts = ['.mp3', '.m4a']


def sanitize_file_name(file_name: str):
    return file_name.replace("/", "_").replace("\\", "_").replace(":", "_").strip()

# returns real sub dir based on the given subdir name (eg. real case for case-insensitive file systems)
def real_existing_sub_dir(dir: str, subdir: str) -> str | None:
    if not os.path.exists(dir + os.sep + subdir):
        return None
    for possibility in os.listdir(dir):
        if possibility.lower() == subdir.lower():
            return dir + os.sep + possibility
    return None
