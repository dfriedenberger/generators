from abc import ABC, abstractmethod
from .template import Template
from .data.data_property import DataProperty

class BaseDataStructureGenerator(ABC):

    def __init__(self,name,properties):
        self.name = name
        self.properties = properties
    
    @abstractmethod
    def get_template(self): pass

    @abstractmethod
    def convert_type(self,property : DataProperty): pass

    def create_content(self):
        template = Template(self.get_template())

        template.set("MessageClassName",self.name)
        message_imports = []
        for property in self.properties:
            if property.get_data_type() in ["array","object"]:
                message_imports.append({
                    "name" : property.get_items(),
                    "package" : f".{property.get_items()}"
                })
        template.set("message_imports",message_imports)

        properties = []
        for property in self.properties:
            properties.append({
                "name" : property.get_name(),
                "type" : self.convert_type(property)
            })
        template.set("properties",properties)
        return template.content()
    
class DataStructureGenerator(BaseDataStructureGenerator):

    def get_template(self):
        return "templates/message.py.mustache"

    def convert_type(self,property : DataProperty):
        python_types = {
            'string' : 'str',
            'uint8' : 'int',
            'uint16' : 'int',
            'bytes' : 'bytes'
        }
        t = property.get_data_type()
        if t == "array":
            return f'List[{property.get_items()}]'
        if t == "object":
            return f'{property.get_items()}'
        return python_types[t]
    
class DDSDataStructureGenerator(BaseDataStructureGenerator):

    def get_template(self):
        return "templates/dds_message.py.mustache"

    def convert_type(self,property : DataProperty):
        python_dds_types = {
        'string' : 'str',
        'uint8' : 'int',
        'uint16' : 'int',
        'bytes' : 'sequence[int]'
        }
        t = property.get_data_type()
        if t == "array":
            return f'sequence[{property.get_items()}]'
        if t == "object":
            return f'{property.get_items()}'
        return python_dds_types[t]
