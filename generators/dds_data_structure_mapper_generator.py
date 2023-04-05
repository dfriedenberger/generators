from .template import Template
from .util.util import snake_case
from .util.cleanup import remove_duplicates
from .data.data_struct import DataStruct
from typing import List

def flatten(l):
    return [item for sublist in l for item in sublist]

def get_cast(from_property,to_property,convert):

    ft = from_property.get_data_type()
    tt = to_property.get_data_type()

    if ft == "array" and tt == "array":
        return f"map_{from_property.get_items()}_to_{to_property.get_items()}"
    return convert[f"{ft}_to_{tt}"]

def get_properties(from_properties,to_properties,convert):
    l = len(from_properties)
    if l != len(to_properties):
        raise ValueError("different length of properties {from_properties} / {to_properties}")

    properties = []
    for i in range(l):
        properties.append({
            'from_name' : from_properties[i].get_name(),
            'to_name' : to_properties[i].get_name()
        })

        ft = from_properties[i].get_data_type()
        if ft != to_properties[i].get_data_type():
            raise ValueError("different types of properties {from_properties[i]} / {to_properties[i]}")

        if ft == "array":
            properties[-1]['arraycast'] = f"map_{from_properties[i].get_items()}_to_{to_properties[i].get_items()}"
            continue

        if ft == "object":
            properties[-1]['cast'] = f"map_{from_properties[i].get_items()}_to_{to_properties[i].get_items()}"
            continue
        
        if ft in convert:
            properties[-1]['cast'] = convert[ft]
            continue
        
        properties[-1]['nocast'] = True


    properties[-1]['last'] = True
    return properties

def data_structures_to_mappings(from_structure,to_structure,convert):
    l = len(from_structure)
    if l != len(to_structure):
        raise ValueError("different length of structures {from_structure} / {to_structure}")
    
    message_list = []
    for i in range(l):
        message_list.append({
                'from_name' : snake_case(from_structure[i].get_name()),
                'from_type' : from_structure[i].get_name(),
                'to_name' : snake_case(to_structure[i].get_name()),
                'to_type' : to_structure[i].get_name(),
                'properties' : get_properties(from_structure[i].get_data_properties(),to_structure[i].get_data_properties(),convert)
        })
    return message_list

def data_structures_to_imports(data_structures : List[DataStruct]):
    structure_imports = []
    for data_struct in data_structures:
        structure_imports.append({
            "name" : data_struct.get_name(),
            "package" : f".{data_struct.get_name()}"
        })
    return structure_imports

class DDSDataStructureMapperGenerator:

    def __init__(self,recv_messages,send_messages):
        self.recv_messages = recv_messages
        self.send_messages = send_messages

    def create_content(self):
        template = Template("templates/mapper.py.mustache")


        #  Message Imports 
        input_structures = flatten(list(map(lambda x: x.get_data_structures(),self.recv_messages)))
        output_structures = flatten(list(map(lambda x: x.get_data_structures(),self.send_messages)))
        recv_structures = flatten(list(map(lambda x: x.get_msg_structures(),self.recv_messages)))
        send_structures = flatten(list(map(lambda x: x.get_msg_structures(),self.send_messages)))


        message_imports = []
        message_imports.extend(data_structures_to_imports(input_structures))
        message_imports.extend(data_structures_to_imports(output_structures))
        message_imports.extend(data_structures_to_imports(recv_structures))
        message_imports.extend(data_structures_to_imports(send_structures))
        template.set("message_imports",remove_duplicates(message_imports))  


        convert1 = {
            "bytes" : "bytes"
        }
        convert2 = {}
        # Mapper
        mapper = []
        mapper.extend(data_structures_to_mappings(recv_structures,input_structures,convert1))
        mapper.extend(data_structures_to_mappings(output_structures,send_structures,convert2))
        template.set("mapper",mapper)

        return template.content()
