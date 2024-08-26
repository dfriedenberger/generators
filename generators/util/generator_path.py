import os


class GeneratorPath:

    def __init__(self, path):
        self.path = [path]

    def add_parent_path(self, parent_path):
        self.path.insert(0, parent_path)

    def get_root(self):
        return self.path[0]

    def to_rel_path(self):
        directory_path = "."
        for part in self.path[1:]:
            directory_path = os.path.join(directory_path, part)

        return directory_path
    def to_path(self, config, make_directory=False):

        directory_path = self.path[0]

        if "$" not in directory_path:
            raise ValueError(f"Cannot set the absolute path '{directory_path}' in {self.path}")

        path_env = directory_path[1:]
        directory_path = config[path_env]

        for part in self.path[1:]:
            if "$" in part:
                raise ValueError(f"Cannot resolve variable '{part}' in {self.path}")
            directory_path = os.path.join(directory_path, part)
            if not os.path.exists(directory_path) and make_directory:
                os.mkdir(directory_path)

        return directory_path
