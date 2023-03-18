import os
import pkgutil

from obse.sparql_queries import SparQLWrapper
from obse.namespace import MBA


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

class Template:

    def __init__(self,path):
        self.data = pkgutil.get_data(__package__, path).decode('utf-8')

    def content(self):
        return self.data

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
    
    #TODO generate Messages
    messages_py = Template("templates/messages.py")
    create_file(src_path,"messages.py",messages_py.content())
  
    init_py = Template("templates/__init__.py")
    create_file(src_path,"__init__.py",init_py.content())

    # Copy Proxy and requirements.txt
    proxy_py = read_file("proxy/proxy.py")
    create_file(src_path,"proxy.py",proxy_py)

    #TODO copy component proxy
    mocks_py = read_file("proxy/mocks.py")
    create_file(src_path,"mocks.py",mocks_py)

    #TODO generate subscriber from proxy and messages
    subscriber_py = Template("templates/subscriber.py")
    create_file(project_path,"subscriber.py",subscriber_py.content())


def generate(graph,output_path):

    sparql_wrapper = SparQLWrapper(graph)

    '''
        Generate projects
    '''
    for rdf_component in sparql_wrapper.get_instances_of_type(MBA.Component):
        impl = sparql_wrapper.get_object_properties(rdf_component,MBA.implement)
        if 'dds' in impl:
            print(rdf_component,impl)
            dds_path = create_path(output_path,'dds')
            generate_dds_project(sparql_wrapper,rdf_component,dds_path)
        
    '''
        Generate messages
    '''


    pass