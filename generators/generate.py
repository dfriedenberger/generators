import os

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

def read_file(path):
    with open(path,'r',encoding='UTF-8') as f:
        return f.read()


def name2foldername(name):

    name = name.replace(' ', '_')
    
    return name.lower()



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

class DDSSubscriber:
    def __init__(self,recv_messages,send_messages):
        self.recv_messages = recv_messages
        self.send_messages = send_messages

    def create_content(self):
        template = Template("templates/subscriber.py.template")

        # Message Imports and Topics
        message_imports = []
        topics = []
        for msg in self.send_messages + self.recv_messages:
            message_imports.append(f"from src.{msg.get_name()} import {msg.get_name()}")
            topics.append(f'topic{msg.get_name()} = Topic(dp, "{msg.get_name()}Topic", {msg.get_name()}, qos=Qos(Policy.Reliability.Reliable(0)))')
        
        template.replace("{{message_imports}}",message_imports)
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
        write_message = []
        if len(self.send_messages) > 0:
            msg = self.send_messages[0]
            params = []
            properties = msg.get_properties()
            for i in range(len(properties)):
                params.append(f'{properties[i]}=params[{i}]')

            write_message.append(f'message = {msg.get_name()}({",".join(params)})')
            write_message.append(f'dw{msg.get_name()}.write(message)')

        template.replace("{{write_message}}",write_message)


    	# Read Messages
        read_message = []
        if len(self.recv_messages) > 0:
            msg = self.recv_messages[0]
            params = []
            properties = msg.get_properties()
            for i in range(len(properties)):
                params.append(f'message.{properties[i]}')
            
            read_message.append(f'for message in dr{msg.get_name()}.take(10):')
            read_message.append('    logging.info(f"Recv Message {message}")') #ohne format
            read_message.append(f'    proxy.apply([{",".join(params)}])')

        template.replace("{{read_message}}",read_message)

      

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
    project_path = create_path(path,foldername)
    src_path = create_path(project_path,'src')

    # Create README.md
    readme = Template("templates/README.md")
    create_file(project_path,"README.md",readme.content())
    
    # Create Dockerfile
    dockerfile = Template("templates/Dockerfile")
    create_file(project_path,"Dockerfile",dockerfile.content())

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

    # Copy Proxy and requirements.txt
    proxy_py = read_file("proxy/proxy.py")
    create_file(src_path,"proxy.py",proxy_py)

    #TODO copy component proxy
    mocks_py = read_file("proxy/mocks.py")
    create_file(src_path,"mocks.py",mocks_py)

    #TODO generate subscriber from proxy 
    subscriber_py = DDSSubscriber(recv_messages,send_messages)
    create_file(project_path,"subscriber.py",subscriber_py.create_content())

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