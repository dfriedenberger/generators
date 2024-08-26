import string
from rdflib import Graph


class OntologyReader:

    def __init__(self, path):
        self.graph = Graph()
        self.graph.parse(path)

    def _select_named_type(self, name, rdf_type):
        query_string = string.Template("""
            SELECT DISTINCT ?subject
            WHERE {
            ?subject a $TYPE.
            FILTER( STRENDS(STR(?subject),str(<$NAME>)) )
        }
        """).substitute(NAME=name, TYPE=rdf_type)

        nodes = [r['subject'] for r in self.graph.query(query_string)]

        if len(nodes) != 1: 
            raise ValueError(f" not a singleton {nodes}")

        return nodes[0]

    def get_class(self, name):
        return self._select_named_type(name, "owl:Class")

    def get_object_property(self, name):
        return self._select_named_type(name, "owl:ObjectProperty")

    def get_datatype_property(self, name):
        return self._select_named_type(name, "owl:DatatypeProperty")
