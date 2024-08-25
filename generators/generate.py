import os
import shutil

from obse.sparql_queries import SparQLWrapper
from rdflib import URIRef, RDFS

from .template import Template
from .util.namespaces import ANS
from .util.generator_path import GeneratorPath


def read_bytes(filename):
    if not os.path.exists(filename):
        return None
    with open(filename, "rb") as f:
        return f.read()


def create_path(path, subpath):
    if not os.path.exists(path):
        raise ValueError(f"{path} must exists.")
    p = os.path.join(path, subpath)
    if not os.path.exists(p):
        os.makedirs(p)
    return p


def write_file(path, data):

    old_data = read_bytes(path)
    if old_data == data:
        # print(f"No changes to {path}")
        return

    if old_data:
        print(f"Update {path}")
    else:
        print(f"New {path}")

    with open(path, 'wb') as f:
        f.write(data)


def create_file(dst_path, dst_filename, content, config):

    data = bytes(content, 'utf-8')
    path = os.path.join(dst_path.to_path(config, make_directory=True), dst_filename)
    write_file(path, data)


def copy_file(dst_path, dst_filename, src_path, src_filename, config):

    src = os.path.join(src_path.to_path(config), src_filename)
    if not os.path.exists(src):
        raise ValueError(f"Source file {src} must exists.")

    path = os.path.join(dst_path.to_path(config, make_directory=True), dst_filename)
    data = read_bytes(src)

    write_file(path, data)


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


def generate(graph, config):

    sparql_wrapper = SparQLWrapper(graph)

    # Generate Assets
    for rdf_asset in sparql_wrapper.get_instances_of_type(ANS.Asset):
        asset_name = sparql_wrapper.get_single_object_property(rdf_asset, RDFS.label)

        rdf_target = sparql_wrapper.get_single_out_reference(rdf_asset, ANS.hasTarget)

        asset_filename = sparql_wrapper.get_single_object_property(rdf_target, ANS.filename)
        rdf_directory = sparql_wrapper.get_single_out_reference(rdf_target, ANS.hasDirectory)

        asset_output_path = get_directory_path(sparql_wrapper, rdf_directory)

        print(f'Generate Asset "{asset_name}" => {asset_output_path.path} / {asset_filename}')

        rdf_sources = sparql_wrapper.get_out_references(rdf_asset, ANS.hasSource)

        # sort
        # 1 Generate SANDBOX_DIRECTORY
        # 2 Generate ROOT_DIRECTORY
        # 3 Copy from SANDBOX to ROOT_DIRECTORY

        if len(rdf_sources) == 1:  # Copy Asset
            asset_source_filename = sparql_wrapper.get_single_object_property(rdf_sources[0], ANS.filename)
            rdf_source_directory = sparql_wrapper.get_single_out_reference(rdf_sources[0], ANS.hasDirectory)

            asset_source_path = get_directory_path(sparql_wrapper, rdf_source_directory)

            copy_file(asset_output_path, asset_filename, asset_source_path, asset_source_filename, config)

        else:  # Generate Asset from Config and Template

            rdf_config = sparql_wrapper.get_single_out_reference(rdf_asset, ANS.hasConfiguration)
            context = get_asset_dictionary(sparql_wrapper, rdf_config)
            # print(json.dumps(context,indent=4))

            rdf_template = sparql_wrapper.get_single_out_reference(rdf_asset, ANS.hasTemplate)
            template_filename = sparql_wrapper.get_single_object_property(rdf_template, ANS.filename)
            # print("template_filename",template_filename)

            asset_template = Template("templates/"+template_filename)
            asset_template.set_context(context)
            create_file(asset_output_path, asset_filename, asset_template.content(), config)



          


