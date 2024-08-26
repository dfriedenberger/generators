import os


class FileManager:

    def __init__(self, root_path, config):
        self.root_path = root_path
        self.config = config
        self.cache = set()
        self._read_directory('.', self.cache)

    def _read_directory(self, path, cache):
        with os.scandir(os.path.join(self.root_path, path)) as it:
            for e in it:
                if e.name in ['.git', '__pycache__', '.pytest_cache']: # ignore list
                    continue
                e_path = os.path.join(path, e.name)
                if e.is_dir():
                    self._read_directory(e_path, cache)
                else:
                    cache.add(e_path)

    def _register_file(self, path):
        if path not in self.cache:
            raise ValueError(f"{path} not found in {self.cache}")
        self.cache.remove(path)

    def _read_bytes(self, filename):
        if not os.path.exists(filename):
            return None
        with open(filename, "rb") as f:
            return f.read()

    def _write_file(self, path, data):

        old_data = self._read_bytes(path)
        if old_data == data:
            # print(f"No changes to {path}")
            return

        if old_data:
            print(f"Update {path}")
        else:
            print(f"New {path}")

        with open(path, 'wb') as f:
            f.write(data)

    def create_file(self, dst_path, dst_filename, content):

        data = bytes(content, 'utf-8')
        self._register_file(os.path.join(dst_path.to_rel_path(), dst_filename))
        path = os.path.join(dst_path.to_path(self.config, make_directory=True), dst_filename)
        self._write_file(path, data)

    def copy_file(self, dst_path, dst_filename, src_path, src_filename):

        src = os.path.join(src_path.to_path(self.config), src_filename)
        if not os.path.exists(src):
            raise ValueError(f"Source file {src} must exists.")

        self._register_file(os.path.join(dst_path.to_rel_path(), dst_filename))
        path = os.path.join(dst_path.to_path(self.config, make_directory=True), dst_filename)
        data = self._read_bytes(src)

        self._write_file(path, data)

    def remove_files(self):
        for p in sorted(self.cache):
            print(f"Unused {p}")
