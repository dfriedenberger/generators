from .template import Template
from .util.util import snake_case
from .util.cleanup import remove_duplicates
from .data.data_struct import DataStruct
from typing import List


def messages_to_list(messages):
    message_list = []
    for msg in messages:
            message_list.append({
                'name' : msg.get_name(),
                'data_name' : snake_case(msg.get_root_data_structure().get_name()),
                'data_type' : msg.get_root_data_structure().get_name()
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

class ComponentProxyInterfaceGenerator:
    def __init__(self,component_name,recv_messages,send_messages):
        self.recv_messages = recv_messages
        self.send_messages = send_messages
        self.component_name = component_name

    def create_content(self):
        template = Template("templates/proxy.py.mustache")

        template.set("component_name",self.component_name)


        input_structures = list(map(lambda x: x.get_root_data_structure(),self.recv_messages))
        output_structures = list(map(lambda x: x.get_root_data_structure(),self.send_messages))

        message_imports = []
        message_imports.extend(data_structures_to_imports(input_structures))
        message_imports.extend(data_structures_to_imports(output_structures))
        template.set("message_imports",remove_duplicates(message_imports))


        # Datareader , Datawriter
        template.set("callback_funcs",messages_to_list(self.send_messages))
        template.set("apply_funcs",messages_to_list(self.recv_messages))

        return template.content()