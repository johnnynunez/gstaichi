import os
from gstaichi.lang import impl

class PysideCache:
    def __init__(self) -> None:
        _cache_parent_folder = impl.get_runtime().prog.config().offline_cache_file_path
        self.cache_folder = os.path.join(_cache_parent_folder, "pyside_cache")

    def _get_filepath(self, key: str) -> str:
        filepath = os.path.join(self.cache_folder, f"{key}.cache.txt")
        return filepath

    def store(self, key: str, value: str) -> None:
        filepath = self._get_filepath(key)
        with open(filepath, "w") as f:
            f.write(value)
        print('stored', key, 'to', filepath)

    def try_load(self, key:str) -> str | None:
        filepath = self._get_filepath(key)
        if not os.path.isfile(filepath):
            print("cache miss for", key)
            return None
        print('loading', key, 'from', filepath)
        with open(filepath) as f:
            return f.read()
