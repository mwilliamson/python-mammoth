from nose.tools import istest, assert_equal

from mammoth.docx.xmlparser import element as xml_element
from mammoth.docx.relationships_xml import read_relationships_xml_element


@istest
def target_is_read_from_relationship_element():
    element = xml_element("relationships:Relationships", {}, [
        xml_element("relationships:Relationship", {
            "Id": "rId8",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            "Target": "http://example.com",
        })
    ])
    relationships = read_relationships_xml_element(element)
    assert_equal(
        "http://example.com",
        relationships.find_target_by_relationship_id("rId8"),
    )
