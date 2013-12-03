import collections


class Relationships(object):
    def __init__(self, relationships):
        self._relationships = relationships
    
    def __getitem__(self, key):
        return self._relationships[key]


Relationship = collections.namedtuple("Relationship", ["target"])


def read_relationships_xml_element(element):
    children = element.find_children("relationships:Relationship")
    return Relationships(dict(map(_read_relationship, children)))


def _read_relationship(element):
    relationship_id = element.attributes["Id"]
    relationship = Relationship(target=element.attributes["Target"])
    return relationship_id, relationship
