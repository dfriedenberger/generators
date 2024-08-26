import os
from generators.util.file_manager import FileManager


absolute_path = os.path.dirname(__file__)
data_path = os.path.join(absolute_path, "data")


def test_list_directory():
    file_manager = FileManager(data_path, {})
    assert 1 == len(file_manager.cache)
