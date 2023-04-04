import os
import re
from obse.sparql_queries import SparQLWrapper
from obse.namespace import MBA
from rdflib import URIRef
from .template import Template
from .project_copier import ProjectCopier

def create_path(path,subpath):
    if not os.path.exists(path):
        raise ValueError(f"{path} must exists.")
    p = os.path.join(path,subpath)
    if not os.path.exists(p):
        os.makedirs(p)
    return p

def create_file(path,filename,content):
    if not os.path.exists(path):
        raise ValueError(f"{path} must exists.")
    p = os.path.join(path,filename)
    with open(p,'w',encoding='UTF-8') as f:
        f.write(content)

def read_lines(path,filename,must_exists = True):
    if not os.path.exists(path):
        raise ValueError(f"{path} must exists.")
    p = os.path.join(path,filename)
    if not os.path.exists(p):
        if must_exists:
            raise ValueError(f"{p} must exists.")
        return []
    with open(p,'r',encoding='UTF-8') as f:
        return f.readlines()

def read_file(path,filename):
    if not os.path.exists(path):
        raise ValueError(f"{path} must exists.")
    p = os.path.join(path,filename)
    with open(p,'r',encoding='UTF-8') as f:
        return f.read()


def name2foldername(name):

    name = name.replace(' ', '_')
    
    return name.lower()

def name2componentname(name):
    p = re.split('[-_\s]+', name)
    p = list(map(  (lambda x : str(x[0]).upper() + x[1:]) ,p))
    return ''.join(p)

python_types = {
    'string' : 'str',
    'uint8' : 'int',
    'uint16' : 'int',
    'bytes' : 'bytes'
}

python_dds_types = {
    'string' : 'str',
    'uint8' : 'int',
    'uint16' : 'int',
    'bytes' : 'sequence[int]'
}


class DDSMessage:
    def __init__(self,name,structure):
        self.name = name
        self.structure = structure

    def get_name(self):
        return self.name
    
    def get_structure(self):
        return self.structure

    def get_properties(self):
        return list(map(lambda e: e[0], self.structure))
       
    def create_content(self):
        template = Template("templates/message.py.mustache")
        template.set("MessageClassName",self.get_name())

        properties = []
        for var_name, var_type in self.structure:
            properties.append({
                "name" : var_name,
                "type" : python_dds_types[var_type]
            })
        template.set("properties",properties)

        return template.content()

class ComponentProxyInterface:
    def __init__(self,component_name,recv_messages,send_messages):
        self.recv_messages = recv_messages
        self.send_messages = send_messages
        self.component_name = component_name

    def create_content(self):
        template = Template("templates/proxy.py.mustache")

        template.set("component_name",self.component_name)

        # Datareader , Datawriter
        apply_funcs = []
        for msg in self.recv_messages:
            params = []
            for var_name, var_type in msg.get_structure():
                params.append(f'{var_name} : {python_types[var_type]}')
            apply_funcs.append({
                'name' : msg.get_name(),
                'parameters' : ", ".join(params)
            })
            
        callback_funcs = []
        for msg in self.send_messages:
            params = []
            for _, var_type in msg.get_structure():
                params.append(f'{python_types[var_type]}')
            
            callback_funcs.append({
                'name' : msg.get_name(),
                'parameters' : ",".join(params)
            })
          

        template.set("callback_funcs",callback_funcs)
        template.set("apply_funcs",apply_funcs)

        return template.content()


def message_to_property_list(message):
    property_list = []
    for var_name, var_type in message.get_structure():
            property_list.append({
                    "name" : var_name,
                    "type" : python_types[var_type]
            })
    property_list[-1]['last'] = True
    return property_list

def messages_to_list(messages):
    message_list = []
    for msg in messages:
            message_list.append({
                'package' : f'src.{msg.get_name()}',
                'name' : msg.get_name(),
                'parameters' : message_to_property_list(msg)
            })
    return message_list



class DDSSubscriber:
    def __init__(self,recv_messages,send_messages,proxy_name):
        self.recv_messages = recv_messages
        self.send_messages = send_messages
        self.proxy_name = proxy_name

    def create_content(self):
        template = Template("templates/subscriber.py.mustache")

        # Message Imports and Topics
        proxy_import = []
        proxy_import.append({
            'package' : f'src.{self.proxy_name}',
            'name' : self.proxy_name
        })

        template.set("message_imports",messages_to_list(self.send_messages + self.recv_messages))
        template.set("proxy_import",proxy_import)
        template.set("topics",messages_to_list(self.send_messages + self.recv_messages))

        # Datareader , Datawriter
        template.set("data_reader",self.recv_messages)
        template.set("data_writer",self.send_messages)
     
        # Write message
        template.set("apply_funcs",messages_to_list(self.send_messages))

        # Init self.proxy_name
        template.set("proxy_name",self.proxy_name)
        template.set("proxy_callbacks",messages_to_list(self.send_messages))

    	# Read Messages
        template.set("read_messages",messages_to_list(self.recv_messages))
        
        return template.content()
    

def get_message_structure(sparql_wrapper: SparQLWrapper,rdf_message):
    sequence = []
    rdf_sequence = sparql_wrapper.get_single_out_reference(rdf_message,MBA.structure)
    for i in range(1,100):
        rdf_part= sparql_wrapper.get_out_references(rdf_sequence,URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#_'+str(i)))
        if(len(rdf_part) == 0): break
        if(len(rdf_part) != 1): raise ValueError(f"Unexpected number of properties {rdf_part}")
        var_name = sparql_wrapper.get_single_object_property(rdf_part[0],MBA.name)
        var_type = sparql_wrapper.get_single_object_property(rdf_part[0],MBA.datatype)
        sequence.append((var_name,var_type))

    return sequence

    

def  generate_dds_project(sparql_wrapper: SparQLWrapper,rdf_component,path):
    name = sparql_wrapper.get_single_object_property(rdf_component,MBA.name)
    foldername = name2foldername(name)
    componentname = name2componentname(name)

    project_path = create_path(path,foldername)
    proxy_path = create_path("proxy",foldername)
    proxy_src_path = create_path(proxy_path,"src")

    src_path = create_path(project_path,'src')

    # Create README.md
    readme = Template("templates/README.md")
    create_file(project_path,"README.md",readme.content())
    
    # Create dds-modul
    cyclone_dds_xml = Template("templates/cyclonedds.xml")
    create_file(project_path,"cyclonedds.xml",cyclone_dds_xml.content())

    loop_py = Template("templates/loop.py")
    create_file(project_path,"loop.py",loop_py.content())
    
    #Debug
    pub_py = Template("templates/pub.py")
    create_file(project_path,"pub.py",pub_py.content())

    #TODO generate Messages
    recv_messages = []
    send_messages = []
    for rdf_interface in sparql_wrapper.get_out_references(rdf_component,MBA.has):
        for rdf_message in sparql_wrapper.get_out_references(rdf_interface,MBA.has):
            name = sparql_wrapper.get_single_object_property(rdf_message,MBA.name)
            structure = get_message_structure(sparql_wrapper,rdf_message)
            print("Message",name,structure)
            msg_py = DDSMessage(name,structure)
            create_file(src_path,f"{msg_py.get_name()}.py",msg_py.create_content())

            senders = sparql_wrapper.get_out_references(rdf_message,MBA.hasSender)
            recipients = sparql_wrapper.get_out_references(rdf_message,MBA.hasRecipient)
            if rdf_component in senders:
                send_messages.append(msg_py)
            if rdf_component in recipients:
                recv_messages.append(msg_py)
  
    init_py = Template("templates/__init__.py")
    create_file(src_path,"__init__.py",init_py.content())


    # Create ProxyInterface
    interface_name = f"{componentname}ProxyInterface"
    proxy_name = f"{componentname}Proxy"
    proxy_interface_py = ComponentProxyInterface(interface_name,recv_messages,send_messages)

    create_file(proxy_src_path,f"{interface_name}.py",proxy_interface_py.create_content())

    # Copy python files from proxy
    project_copier = ProjectCopier(source_path = proxy_path,target_path=project_path)
    project_copier.copy()
    for file in os.listdir(proxy_src_path):
        if file == "docker.txt": continue
        if file == "wrapper.txt": continue
        if file == "__pycache__": continue
        content = read_file(proxy_src_path,file)
        create_file(src_path,file,content)

    #TODO generate subscriber from proxy 
    subscriber_py = DDSSubscriber(recv_messages,send_messages,proxy_name)
    create_file(project_path,"subscriber.py",subscriber_py.create_content())

    # create wrapper.sh
    wrapper_sh = Template("templates/wrapper.sh.mustache")
    wrapper_txt = read_lines(proxy_path,"wrapper.txt",must_exists=False)
    wrapper_txt.append("#Start subscriber")
    wrapper_txt.append("python subscriber.py &")
    wrapper_sh.set("include",'\n'.join(wrapper_txt))
    create_file(project_path,"wrapper.sh",wrapper_sh.content())

    # Create Dockerfile
    dockerfile = Template("templates/Dockerfile.mustache")
    docker_txt = read_lines(proxy_path,"docker.txt",must_exists=False)
    dockerfile.set("include",'\n'.join(docker_txt))
    create_file(project_path,"Dockerfile",dockerfile.content())

    return foldername

def generate(graph,output_path):

    sparql_wrapper = SparQLWrapper(graph)

    '''
        Generate projects
    '''
    services = []
    for rdf_component in sparql_wrapper.get_instances_of_type(MBA.Component):
        impl = sparql_wrapper.get_object_properties(rdf_component,MBA.implement)
        if 'dds' in impl:
            print(rdf_component,impl)
            project_path = generate_dds_project(sparql_wrapper,rdf_component,output_path)
            services.append({
                "name" : f"peer-{project_path}" , 
                "build" : f"{project_path}" 
            })


    docker_compose_yml = Template("templates/docker-compose.yml.mustache")
    docker_compose_yml.set('services', services)
    create_file(output_path,"docker-compose.yml",docker_compose_yml.content())


    '''
        Generate messages
    '''


    pass