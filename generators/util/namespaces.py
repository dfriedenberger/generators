from rdflib.namespace import DefinedNamespace
from rdflib import URIRef
from .ontology_reader import OntologyReader

assetOntology = OntologyReader("models/assets-0.0.1.ttl")

class ANS(DefinedNamespace):
    Asset: URIRef = assetOntology.get_class('#Asset')
    Template: URIRef = assetOntology.get_class('#Template')
    Configuration: URIRef = assetOntology.get_class('#Configuration')
    Dictionary: URIRef = assetOntology.get_class('#Dictionary')
    KeyValuePair: URIRef = assetOntology.get_class('#KeyValuePair')

    filename: URIRef = assetOntology.get_datatype_property('#filename')
    key: URIRef = assetOntology.get_datatype_property('#key')
    valueAsLiteral: URIRef = assetOntology.get_datatype_property('#valueAsLiteral')
    valueAsClass: URIRef = assetOntology.get_object_property('#valueAsClass')

    hasTemplate: URIRef = assetOntology.get_object_property('#hasTemplate')
    hasConfiguration: URIRef = assetOntology.get_object_property('#hasConfiguration')
    hasKeyValuePair: URIRef = assetOntology.get_object_property('#hasKeyValuePair')
