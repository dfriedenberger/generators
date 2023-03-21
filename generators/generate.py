import os
import re
from obse.sparql_queries import SparQLWrapper
from obse.namespace import MBA
from rdflib import URIRef
from .template import Template

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
    'uint16' : 'int'
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
        template = Template("templates/message.py.template")
        template.replace("{{MessageClassName}}",self.get_name())

        properties = []
        for var_name, var_type in self.structure:
            properties.append(f"{var_name}: {python_types[var_type]}")
        template.replace("{{properties}}",properties)

        return template.content()

class ComponentProxyInterface:
    def __init__(self,component_name,recv_messages,send_messages):
        self.recv_messages = recv_messages
        self.send_messages = send_messages
        self.component_name = component_name

    def create_content(self):
        template = Template("templates/proxy.py.template")

        template.replace("{{component_name}}",self.component_name)

        # Datareader , Datawriter
        apply_funcs = []
        for msg in self.recv_messages:
            params = []
            for var_name, var_type in msg.get_structure():
                params.append(f'{var_name} : {python_types[var_type]}')
            apply_funcs.append(f'@abstractmethod')
            apply_funcs.append(f'def apply_{msg.get_name()}(self,{", ".join(params)}) -> None: pass')

        callback_funcs = []
        for msg in self.send_messages:
            params = []
            for _, var_type in msg.get_structure():
                params.append(f'{python_types[var_type]}')
            callback_funcs.append(f'@abstractmethod')
            callback_funcs.append(f'def set_{msg.get_name()}_callback(self,callback : Callable[[{",".join(params)}], None]) -> None: pass')

        template.replace("{{callback_funcs}}",callback_funcs)
        template.replace("{{apply_funcs}}",apply_funcs)

        return template.content()

class DDSSubscriber:
    def __init__(self,recv_messages,send_messages,proxy_name):
        self.recv_messages = recv_messages
        self.send_messages = send_messages
        self.proxy_name = proxy_name

    def create_content(self):
        template = Template("templates/subscriber.py.template")

        # Message Imports and Topics
        message_imports = []
        topics = []
        for msg in self.send_messages + self.recv_messages:
            message_imports.append(f"from src.{msg.get_name()} import {msg.get_name()}")
            topics.append(f'topic{msg.get_name()} = Topic(dp, "{msg.get_name()}Topic", {msg.get_name()}, qos=Qos(Policy.Reliability.Reliable(0)))')
        
        template.replace("{{message_imports}}",message_imports)
        template.replace("{{proxy_import}}",f"from src.{self.proxy_name} import {self.proxy_name}")
        template.replace("{{topics}}",topics)

        # Datareader , Datawriter
        data_reader = []
        for msg in self.recv_messages:
            data_reader.append(f'dr{msg.get_name()} = DataReader(dp, topic{msg.get_name()})')
        data_writer = []
        for msg in self.send_messages:
            data_writer.append(f'dw{msg.get_name()} = DataWriter(dp, topic{msg.get_name()})')
        template.replace("{{data_reader}}",data_reader)
        template.replace("{{data_writer}}",data_writer)
     
        # Write message
        apply_funcs = []
        for msg in self.send_messages:
            params1 = []
            params2 = []
            properties = msg.get_properties()
            for var_name, var_type in msg.get_structure():
                params1.append(f'{var_name} : {python_types[var_type]}')
                params2.append(f'{var_name}={var_name}')

            apply_funcs.append(f'def apply_{msg.get_name()}({", ".join(params1)}):')
            apply_funcs.append(f'    message = {msg.get_name()}({", ".join(params2)})')
            apply_funcs.append('    logging.info(f"Send Message {message}")') #no format
            apply_funcs.append(f'    dw{msg.get_name()}.write(message)')

        template.replace("{{apply_funcs}}",apply_funcs)

        # Init self.proxy_name
        proxy = []
        proxy.append(f"proxy = {self.proxy_name}()")
        for msg in self.send_messages:
            proxy.append(f"proxy.set_{msg.get_name()}_callback(apply_{msg.get_name()})")

        template.replace("{{proxy}}",proxy)

    	# Read Messages
        read_messages = []
        for msg in self.recv_messages:
            params = []
            properties = msg.get_properties()
            for i in range(len(properties)):
                params.append(f'{properties[i]} = message.{properties[i]}')

            read_messages.append(f'for message in dr{msg.get_name()}.take(10):')
            read_messages.append('    logging.info(f"Recv Message {message}")') #ohne format
            read_messages.append(f'    proxy.apply_{msg.get_name()}({",".join(params)})')

        template.replace("{{read_messages}}",read_messages)

      

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

    create_file(proxy_path,f"{interface_name}.py",proxy_interface_py.create_content())

    # Copy python files from proxy
    for file in os.listdir(proxy_path):
        if file == "docker.txt": continue
        if file == "wrapper.txt": continue
        
        content = read_file(proxy_path,file)
        create_file(src_path,file,content)

    #TODO generate subscriber from proxy 
    subscriber_py = DDSSubscriber(recv_messages,send_messages,proxy_name)
    create_file(project_path,"subscriber.py",subscriber_py.create_content())

    # create wrapper.sh
    wrapper_sh = Template("templates/wrapper.sh.template")
    wrapper_txt = read_lines(proxy_path,"wrapper.txt",must_exists=False)
    wrapper_txt.append("#Start subscriber")
    wrapper_txt.append("python subscriber.py &")
    wrapper_sh.replace("{{include}}",wrapper_txt)
    create_file(project_path,"wrapper.sh",wrapper_sh.content())

    # Create Dockerfile
    dockerfile = Template("templates/Dockerfile.template")
    docker_txt = read_lines(proxy_path,"docker.txt",must_exists=False)
    dockerfile.replace("{{include}}",docker_txt)
    create_file(project_path,"Dockerfile",dockerfile.content())

    return foldername

def generate(graph,output_path):

    sparql_wrapper = SparQLWrapper(graph)

    '''
        Generate projects
    '''
    dds_path = create_path(output_path,'dds')
    peers = []
    for rdf_component in sparql_wrapper.get_instances_of_type(MBA.Component):
        impl = sparql_wrapper.get_object_properties(rdf_component,MBA.implement)
        if 'dds' in impl:
            print(rdf_component,impl)
            project_path = generate_dds_project(sparql_wrapper,rdf_component,dds_path)
            peers.append(f"peer-{project_path}:")
            peers.append(f"    build: {project_path}")

    docker_compose_yml = Template("templates/docker-compose.yml.template")
    docker_compose_yml.replace("{{peers}}",peers)
    create_file(dds_path,"docker-compose.yml",docker_compose_yml.content())


    '''
        Generate messages
    '''


    pass