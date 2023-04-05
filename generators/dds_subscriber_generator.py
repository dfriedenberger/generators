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
                'msg_name' : snake_case(msg.get_root_msg_structure().get_name()),
                'msg_type' : msg.get_root_msg_structure().get_name(),
                'data_name' : snake_case(msg.get_root_data_structure().get_name()),
                'data_type' : msg.get_root_data_structure().get_name()
            })
    return message_list


def data_structures_to_imports(data_structures : List[DataStruct]):
    structure_imports = []
    for data_struct in data_structures:
        structure_imports.append({
            "name" : data_struct.get_name(),
            "package" : f"src.{data_struct.get_name()}"
        })
    return structure_imports

class DDSSubscriberGenerator:
    def __init__(self,proxy_name,recv_messages,send_messages):
        self.recv_messages = recv_messages
        self.send_messages = send_messages
        self.proxy_name = proxy_name

    def create_content(self):
        template = Template("templates/subscriber.py.mustache")


        # Proxy and Message Imports 
        proxy_import = []
        proxy_import.append({
            'package' : f'src.{self.proxy_name}',
            'name' : self.proxy_name
        })
        template.set("proxy_import",proxy_import)

        input_structures = list(map(lambda x: x.get_root_data_structure(),self.recv_messages))
        output_structures = list(map(lambda x: x.get_root_data_structure(),self.send_messages))
        recv_structures = list(map(lambda x: x.get_root_msg_structure(),self.recv_messages))
        send_structures = list(map(lambda x: x.get_root_msg_structure(),self.send_messages))


        message_imports = []
        message_imports.extend(data_structures_to_imports(input_structures))
        message_imports.extend(data_structures_to_imports(output_structures))
        message_imports.extend(data_structures_to_imports(recv_structures))
        message_imports.extend(data_structures_to_imports(send_structures))
        template.set("message_imports",remove_duplicates(message_imports))

        template.set("topics",messages_to_list(self.send_messages + self.recv_messages))

        # Datareader , Datawriter
        template.set("data_reader",messages_to_list(self.recv_messages))
        template.set("data_writer",messages_to_list(self.send_messages))
     
        # Write message
        template.set("apply_funcs",messages_to_list(self.send_messages))

        # Init self.proxy_name
        template.set("proxy_name",self.proxy_name)
        template.set("proxy_callbacks",messages_to_list(self.send_messages))

    	# Read Messages
        template.set("read_messages",messages_to_list(self.recv_messages))
        
        return template.content()
    
