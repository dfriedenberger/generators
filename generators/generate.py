import os
import shutil

from obse.sparql_queries import SparQLWrapper
from rdflib import URIRef, RDFS

from .template import Template
from .util.namespaces import ANS
from .util.generator_path import GeneratorPath
from .util.file_manager import FileManager





def create_path(path, subpath):
    if not os.path.exists(path):
        raise ValueError(f"{path} must exists.")
    p = os.path.join(path, subpath)
    if not os.path.exists(p):
        os.makedirs(p)
    return p






def get_asset_dictionary(sparql_wrapper: SparQLWrapper, rdf_use):
    data = dict()

    for rdf_key_value in sparql_wrapper.get_out_references(rdf_use, ANS.hasKeyValuePair):

        key = sparql_wrapper.get_single_object_property(rdf_key_value, ANS.key)
        literals = sparql_wrapper.get_object_properties(rdf_key_value, ANS.valueAsLiteral)
        rdf_classes = sparql_wrapper.get_out_references(rdf_key_value, ANS.valueAsClass)

        if (len(literals) + len(rdf_classes)) != 1:
            raise ValueError(f"Specification of values is invalid {literals} / {rdf_classes}")
        if len(literals) == 1:
            value = literals[0]
            if key in data:
                raise ValueError("Duplicate Entries for key {key} data: {data[key]} and {value}")
            data[key] = value
        else:
            value = get_asset_dictionary(sparql_wrapper, rdf_classes[0])
            if key not in data:
                data[key] = []
            data["has_"+key] = True
            data[key].append(value)

    return data


def get_directory_path(sparql_wrapper: SparQLWrapper, rdf_directory: URIRef):

    directory_path = sparql_wrapper.get_single_object_property(rdf_directory, ANS.path)
    target = GeneratorPath(directory_path)

    while True:
        rdf_parents = sparql_wrapper.get_in_references(rdf_directory, ANS.hasSubdirectory)
        if len(rdf_parents) == 0:
            break
        if len(rdf_parents) == 1:
            parent_path = sparql_wrapper.get_single_object_property(rdf_parents[0], ANS.path)

            target.add_parent_path(parent_path)
            rdf_directory = rdf_parents[0]
            continue
        raise ValueError(f"{rdf_directory} has more than one parent {rdf_parents}")

    return target


def generate(graph, config, sandbox_only, show_unused):

    sparql_wrapper = SparQLWrapper(graph)

    processes = [
        {
            'name': 'Sandbox',
            'path': 'SANDBOX_DIRECTORY',
            'sandbox': True,
            'ds': []
        },
        {
            'name': 'Target-System',
            'path': 'ROOT_DIRECTORY',
            'sandbox': False,
            'ds': []
        }
    ]

    # Generate Assets
    for rdf_asset in sparql_wrapper.get_instances_of_type(ANS.Asset):
        asset_name = sparql_wrapper.get_single_object_property(rdf_asset, RDFS.label)

        rdf_target = sparql_wrapper.get_single_out_reference(rdf_asset, ANS.hasTarget)

        asset_filename = sparql_wrapper.get_single_object_property(rdf_target, ANS.filename)
        rdf_directory = sparql_wrapper.get_single_out_reference(rdf_target, ANS.hasDirectory)

        asset_output_path = get_directory_path(sparql_wrapper, rdf_directory)

        # print(f'Generate Asset "{asset_name}" => {asset_output_path.path} / {asset_filename}')

        rdf_sources = sparql_wrapper.get_out_references(rdf_asset, ANS.hasSource)

        dataset = (rdf_asset, asset_name, asset_output_path, asset_filename, rdf_sources)

        if asset_output_path.get_root() == '$SANDBOX_DIRECTORY':
            processes[0]['ds'].append(dataset)
        elif asset_output_path.get_root() == '$ROOT_DIRECTORY':
            processes[1]['ds'].append(dataset)
        else:
            raise ValueError(f"Unknown root path {asset_output_path.get_root()}")

    for process in processes:
        dataset = process['ds']
        if sandbox_only and not process['sandbox']:
            continue

        print(f"Prozess {process['name']} Items {len(dataset)}")
        file_manager = FileManager(config[process['path']], config)
        for (rdf_asset, asset_name, asset_output_path, asset_filename, rdf_sources) in dataset:
            if len(rdf_sources) == 1:  # Copy Asset
                asset_source_filename = sparql_wrapper.get_single_object_property(rdf_sources[0], ANS.filename)
                rdf_source_directory = sparql_wrapper.get_single_out_reference(rdf_sources[0], ANS.hasDirectory)

                asset_source_path = get_directory_path(sparql_wrapper, rdf_source_directory)

                file_manager.copy_file(asset_output_path, asset_filename, asset_source_path, asset_source_filename)

            else:  # Generate Asset from Config and Template

                rdf_config = sparql_wrapper.get_single_out_reference(rdf_asset, ANS.hasConfiguration)
                context = get_asset_dictionary(sparql_wrapper, rdf_config)
                # print(json.dumps(context,indent=4))

                rdf_template = sparql_wrapper.get_single_out_reference(rdf_asset, ANS.hasTemplate)
                template_filename = sparql_wrapper.get_single_object_property(rdf_template, ANS.filename)
                # print("template_filename",template_filename)

                asset_template = Template("templates/"+template_filename)
                asset_template.set_context(context)
                file_manager.create_file(asset_output_path, asset_filename, asset_template.content())

        if not process['sandbox'] and show_unused:
            file_manager.remove_files()

