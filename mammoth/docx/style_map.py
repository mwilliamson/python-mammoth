from xml.etree import ElementTree

from ..zips import open_zip, update_zip


_style_map_path = "mammoth/style-map"
_style_map_absolute_path = "/" + _style_map_path
_relationships_path = "word/_rels/document.xml.rels"


def write_style_map(fileobj, style_map):
    with open_zip(fileobj, "r") as zip_file:
        relationships_xml = _generate_relationships_xml(zip_file.read_str("word/_rels/document.xml.rels"))
    
    update_zip(fileobj, {
        _style_map_path: style_map,
        _relationships_path: relationships_xml
    })

def _generate_relationships_xml(relationships_xml):
    schema = "http://schemas.zwobble.org/mammoth/style-map";
    relationships_uri = "http://schemas.openxmlformats.org/package/2006/relationships"
    relationship_element_name = "{" + relationships_uri + "}Relationship"
    
    relationships = ElementTree.fromstring(relationships_xml)
    _add_or_update_element(relationships, relationship_element_name, "Id", {
        "Id": "rMammothStyleMap",
        "Type": schema,
        "Target": _style_map_absolute_path,
    })

    return ElementTree.tostring(relationships, "UTF-8")


def _add_or_update_element(parent, name, identifying_attribute, attributes):
    existing_child = _find_child(parent, name, identifying_attribute, attributes)
    if existing_child is None:
        ElementTree.SubElement(parent, name, attributes)
    else:
        existing_child.attrib = attributes
    

def _find_child(parent, name, identifying_attribute, attributes):
    for element in parent.iter():
        if element.tag == name and element.get(identifying_attribute) == attributes.get(identifying_attribute):
            return element


def read_style_map(fileobj):
    with open_zip(fileobj, "r") as zip_file:
        if zip_file.exists(_style_map_path):
            return zip_file.read_str(_style_map_path)


