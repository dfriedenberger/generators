import os
from generators.template import Template


absolute_path = os.path.dirname(__file__)
data_path = os.path.join(absolute_path, "data")


def test_workflow():
    template = Template(os.path.join(data_path, "test.txt"))
    template.set("lines", [{"name": "hello"}])
    assert "hello" in template.content()
