from rdflib.namespace import DefinedNamespace
from rdflib import URIRef
from .ontology_reader import OntologyReader

assetOntology = OntologyReader("models/assets-0.0.1.ttl")


class ANS(DefinedNamespace):
    Asset: URIRef = assetOntology.get_class('#Asset')
    Target: URIRef = assetOntology.get_class('#Target')
    Source: URIRef = assetOntology.get_class('#Source')
    Template: URIRef = assetOntology.get_class('#Template')
    Directory: URIRef = assetOntology.get_class('#Directory')

    Configuration: URIRef = assetOntology.get_class('#Configuration')
    Dictionary: URIRef = assetOntology.get_class('#Dictionary')
    KeyValuePair: URIRef = assetOntology.get_class('#KeyValuePair')

    filename: URIRef = assetOntology.get_datatype_property('#filename')
    path: URIRef = assetOntology.get_datatype_property('#path')
    key: URIRef = assetOntology.get_datatype_property('#key')
    valueAsLiteral: URIRef = assetOntology.get_datatype_property('#valueAsLiteral')
    valueAsClass: URIRef = assetOntology.get_object_property('#valueAsClass')

    hasTarget: URIRef = assetOntology.get_object_property('#hasTarget')
    hasSource: URIRef = assetOntology.get_object_property('#hasSource')
    hasTemplate: URIRef = assetOntology.get_object_property('#hasTemplate')
    hasDirectory: URIRef = assetOntology.get_object_property('#hasDirectory')
    hasSubdirectory: URIRef = assetOntology.get_object_property('#hasSubdirectory')


    hasConfiguration: URIRef = assetOntology.get_object_property('#hasConfiguration')
    hasKeyValuePair: URIRef = assetOntology.get_object_property('#hasKeyValuePair')
