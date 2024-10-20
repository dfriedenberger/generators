from rdflib import RDF, URIRef, Literal
from rdflib.namespace import XSD
from obse.sparql_queries import SparQLWrapper
from .namespaces import ANS


def process_key_value_pairs(sparql_wrapper: SparQLWrapper, rdf_use):
    """Verarbeitet alle Key-Value-Paare für ein RDF-Subjekt."""
    json_obj = {}

    for kv_pair in sparql_wrapper.graph.objects(rdf_use, ANS.hasKeyValuePair):
        key = str(sparql_wrapper.graph.value(kv_pair, ANS.key))  # Extrahiere den Key
        value_node = sparql_wrapper.graph.value(kv_pair, ANS.value)  # Extrahiere den Wert
        t, json_obj[key] = process_value(sparql_wrapper, value_node)  # Verarbeite den Wert
        if t == "list" and len(json_obj[key]) > 0:
            json_obj["has_"+key] = True

    return json_obj


def process_value(sparql_wrapper: SparQLWrapper, value_node):
    """Verarbeitet einen RDF-Wert und wandelt ihn in JSON um."""

    if (value_node, RDF.type, RDF.Seq) in sparql_wrapper.graph:
        return 'list', process_seq(sparql_wrapper, value_node)  # Wenn es eine Liste (rdf:Seq) ist
    elif (value_node, RDF.type, ANS.Dictionary) in sparql_wrapper.graph:
        return 'dict', process_key_value_pairs(sparql_wrapper, value_node)  # Wenn es ein JSON-Objekt ist
    elif isinstance(value_node, Literal):
        return 'lit', literal_to_value(value_node)  # Wenn es ein einfacher Wert ist

    raise ValueError(f"Unrecognized RDF node type: {type(value_node)}")


def process_seq(sparql_wrapper: SparQLWrapper, seq_node):
    """Verarbeitet eine RDF-Sequenz (rdf:Seq) und gibt eine Liste zurück."""
    seq_list = []
    index = 1
    while True:
        item = sparql_wrapper.graph.value(seq_node, URIRef(RDF["_{}".format(index)]))
        if item is None:
            break
        _, element = process_value(sparql_wrapper, item)
        seq_list.append(element)  # Verarbeite jedes Element der Liste
        index += 1
    return seq_list


def literal_to_value(literal):
    """Wandelt ein Literal in den passenden JSON-Typ um."""
    if literal.datatype:
        if literal.datatype == XSD.integer:
            return int(literal)
        elif literal.datatype == XSD.float:
            return float(literal)
        elif literal.datatype == XSD.boolean:
            return bool(literal)
        else:
            raise ValueError(f"Unknown datatype {literal.datatype} for {literal}")
    return str(literal)  # Default: als String behandeln
