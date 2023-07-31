import os
import re
import json
import shutil

from obse.sparql_queries import SparQLWrapper
from obse.namespace import MBA
from rdflib import URIRef, RDFS

from .template import Template
from .project_copier import ProjectCopier
from .data.data_struct import DataStruct
from .data.data_property import DataProperty
from .util.util import snake_case
from .util.namespaces import ANS

from .base_data_structure_generator import DDSDataStructureGenerator, DataStructureGenerator
from .component_proxy_interface_generator import ComponentProxyInterfaceGenerator
from .dds_subscriber_generator import DDSSubscriberGenerator
from .dds_data_structure_mapper_generator import DDSDataStructureMapperGenerator



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


def copy_file(dst_path,dst_filename,src_path,src_filename):

    if not os.path.exists(dst_path):
        raise ValueError(f"Destination path {dst_path} must exists.")
    
    if not os.path.exists(src_path):
        raise ValueError(f"Source path {src_path} must exists.")

    dst = os.path.join(dst_path,dst_filename)
    src = os.path.join(src_path,src_filename)

    if not os.path.exists(src):
        raise ValueError(f"Source file {src} must exists.")

    shutil.copyfile(src, dst)



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


def name2componentname(name):
    p = re.split('[-_\s]+', name)
    p = list(map(  (lambda x : str(x[0]).upper() + x[1:]) ,p))
    return ''.join(p)


class DDSMessage:
    def __init__(self,name,structure):
        self.name = name
        self.structure = structure

    def get_name(self):
        return self.name
    
    def get_structure(self):
        return self.structure


class DDSMessage:
    def __init__(self,name,data_structures,msg_structures):
        self.name = name
        self.data_structures = data_structures
        self.msg_structures = msg_structures

    def get_name(self):
        return self.name
    
    def get_root_data_structure(self):
        return self.data_structures[-1]
    
    def get_root_msg_structure(self):
        return self.msg_structures[-1]
    
    def get_data_structures(self):
        return self.data_structures
    
    def get_msg_structures(self):
        return self.msg_structures
    


def get_message_structure(sparql_wrapper: SparQLWrapper,rdf_message):
    data_structs = []

    rdf_sequence = sparql_wrapper.get_single_out_reference(rdf_message,MBA.structure)
    var_structure_name = sparql_wrapper.get_single_object_property(rdf_sequence,MBA.name)
    data_struct= DataStruct(var_structure_name)

    for i in range(1,100):
        rdf_part= sparql_wrapper.get_out_references(rdf_sequence,URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#_'+str(i)))
        if(len(rdf_part) == 0): break
        if(len(rdf_part) != 1): raise ValueError(f"Unexpected number of properties {rdf_part}")

        var_name = sparql_wrapper.get_single_object_property(rdf_part[0],MBA.name)
        var_type = sparql_wrapper.get_single_object_property(rdf_part[0],MBA.datatype)
        items = None
        if var_type == "array" or var_type == "object":
            ds = get_message_structure(sparql_wrapper,rdf_part[0])
            items = ds[-1].name
            data_structs.extend(ds)

        data_property = DataProperty(name = var_name,data_type = var_type,items = items)
            
        data_struct.add_data_property(data_property)
    data_structs.append(data_struct)
    return data_structs

   

def clone_structures(structures):
    msg_structures = []
    for structure in structures:
        msg_structure = DataStruct(f"{structure.get_name()}Message")
        for property in structure.get_data_properties():
            items = property.get_items()
            if items:
                items = f"{items}Message"
            msg_property = DataProperty(property.get_name(),property.get_data_type(),items)
            msg_structure.add_data_property(msg_property)
        msg_structures.append(msg_structure)

    return msg_structures


def generate_dds_project(sparql_wrapper: SparQLWrapper,rdf_component,path):
    name = sparql_wrapper.get_single_object_property(rdf_component,MBA.name)
    foldername = snake_case(name)

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
            structures = get_message_structure(sparql_wrapper,rdf_message)
            #print("Message",name,structures)

            msg_structures = clone_structures(structures)
            #print("Message",name,msg_structures)

            msg_py = DDSMessage(name,structures,msg_structures)

            senders = sparql_wrapper.get_out_references(rdf_message,MBA.hasSender)
            recipients = sparql_wrapper.get_out_references(rdf_message,MBA.hasRecipient)
            if rdf_component in senders:
                send_messages.append(msg_py)
            if rdf_component in recipients:
                recv_messages.append(msg_py)


    # Create Init File (notwendig?)
    init_py = Template("templates/__init__.py")
    create_file(src_path,"__init__.py",init_py.content())
   

    # Create Data Structures
    for msg in recv_messages + send_messages:
        for structure in msg.get_data_structures():
            data_structure_py = DataStructureGenerator(structure.get_name(),structure.get_data_properties())
            create_file(proxy_src_path,f"{structure.get_name()}.py",data_structure_py.create_content())


    # Create ProxyInterface and Proxy
    interface_name = f"{componentname}ProxyInterface"
    proxy_name = f"{componentname}Proxy"
  
    proxy_interface_py = ComponentProxyInterfaceGenerator(interface_name,recv_messages,send_messages)

    create_file(proxy_src_path,f"{interface_name}.py",proxy_interface_py.create_content())

    # Copy python files from proxy
    project_copier = ProjectCopier(source_path = proxy_path,target_path=project_path)
    project_copier.copy()
   
    # Create Message Structures
    for msg in recv_messages + send_messages:
        for structure in msg.get_msg_structures():
            data_structure_py = DDSDataStructureGenerator(structure.get_name(),structure.get_data_properties())
            create_file(src_path,f"{structure.get_name()}.py",data_structure_py.create_content())

    # Create Mapper
    mapper_py = DDSDataStructureMapperGenerator(recv_messages,send_messages)
    create_file(src_path,"mapper.py",mapper_py.create_content())


    #TODO generate subscriber from proxy 
    subscriber_py = DDSSubscriberGenerator(proxy_name,recv_messages,send_messages)
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
    docker_from_txt = read_lines(proxy_path,"docker-from.txt",must_exists=True)
    dockerfile.set("from",'\n'.join(docker_from_txt))
    docker_txt = read_lines(proxy_path,"docker.txt",must_exists=False)
    dockerfile.set("include",'\n'.join(docker_txt))
    create_file(project_path,"Dockerfile",dockerfile.content())

    return foldername




def get_asset_dictionary(sparql_wrapper : SparQLWrapper,rdf_use):
    data = dict()

    for rdf_key_value in sparql_wrapper.get_out_references(rdf_use,ANS.hasKeyValuePair):
        
        key = sparql_wrapper.get_single_object_property(rdf_key_value,ANS.key)
        literals = sparql_wrapper.get_object_properties(rdf_key_value,ANS.valueAsLiteral)
        rdf_classes = sparql_wrapper.get_out_references(rdf_key_value,ANS.valueAsClass)

        if (len(literals) + len(rdf_classes)) != 1:
            raise ValueError(f"Specification of values is invalid {literals} / {rdf_classes}")
        if len(literals) == 1:
            value = literals[0]
            if key in data:
                raise ValueError("Duplicate Entries for key {key} data: {data[key]} and {value}")
            data[key] = value
        else:
            value = get_asset_dictionary(sparql_wrapper,rdf_classes[0])
            if key not in data:
                data[key] = []
            data["has_"+key] = True
            data[key].append(value)

    return data

def get_directory_path(sparql_wrapper : SparQLWrapper, rdf_directory : URIRef, config ):

    directory_path = sparql_wrapper.get_single_object_property(rdf_directory,ANS.path)

    while True:
        rdf_parents = sparql_wrapper.get_in_references(rdf_directory,ANS.hasSubdirectory)
        if len(rdf_parents) == 0:
            break
        if len(rdf_parents) == 1:
            parent_path = sparql_wrapper.get_single_object_property(rdf_parents[0],ANS.path)

            if "$" in parent_path:
                parent_path = config[parent_path[1:]]
            directory_path = os.path.join(parent_path,directory_path)
            rdf_directory = rdf_parents[0]
            continue
        raise ValueError(f"{rdf_directory} has more than one parent {rdf_parents}")

    return directory_path


def generate(graph,config):

    sparql_wrapper = SparQLWrapper(graph)

    # Generate projects
    for rdf_component in sparql_wrapper.get_instances_of_type(MBA.Component):
        impl = sparql_wrapper.get_object_properties(rdf_component,MBA.implement)
        if 'dds' in impl:
            #print(rdf_component,impl)
            _ = generate_dds_project(sparql_wrapper,rdf_component,output_path) 




    # Generate Assets
    for rdf_asset in sparql_wrapper.get_instances_of_type(ANS.Asset):
        asset_name = sparql_wrapper.get_single_object_property(rdf_asset,RDFS.label)

        rdf_target = sparql_wrapper.get_single_out_reference(rdf_asset,ANS.hasTarget)
        
        asset_filename = sparql_wrapper.get_single_object_property(rdf_target,ANS.filename)
        rdf_directory = sparql_wrapper.get_single_out_reference(rdf_target,ANS.hasDirectory)
       
        asset_output_path = get_directory_path(sparql_wrapper,rdf_directory,config)
        print(f"Generate Asset {asset_name} => {asset_output_path} / {asset_filename}")

        if not os.path.exists(asset_output_path):
            os.mkdir(asset_output_path)

        rdf_sources = sparql_wrapper.get_out_references(rdf_asset,ANS.hasSource)


        if len(rdf_sources) == 1: # Copy Asset
            asset_source_filename = sparql_wrapper.get_single_object_property(rdf_sources[0],ANS.filename)
            rdf_source_directory = sparql_wrapper.get_single_out_reference(rdf_sources[0],ANS.hasDirectory)
       
            asset_source_path = get_directory_path(sparql_wrapper,rdf_source_directory,config)

            copy_file(asset_output_path,asset_filename,asset_source_path,asset_source_filename)


        else: #Generate Asset from Config and Template

            rdf_config = sparql_wrapper.get_single_out_reference(rdf_asset,ANS.hasConfiguration)
            context = get_asset_dictionary(sparql_wrapper,rdf_config)
            print(json.dumps(context,indent=4))

            rdf_template = sparql_wrapper.get_single_out_reference(rdf_asset,ANS.hasTemplate)
            template_filename = sparql_wrapper.get_single_object_property(rdf_template,ANS.filename)
            print("template_filename",template_filename)

            asset_template = Template("templates/"+template_filename)
            asset_template.set_context(context)
            create_file(asset_output_path,asset_filename,asset_template.content())



          


