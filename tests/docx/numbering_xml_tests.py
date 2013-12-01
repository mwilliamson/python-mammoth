from nose.tools import istest, assert_equal

from mammoth.docx.xmlparser import element as xml_element
from mammoth.docx.numbering_xml import read_numbering_xml_element


@istest
def find_level_returns_none_if_num_with_id_cannot_be_found():
    numbering = read_numbering_xml_element(xml_element("w:numbering"))
    assert_equal(None, numbering.find_level("47", "0"))


_sample_numbering_xml = xml_element("w:numbering", {}, [
    xml_element("w:abstractNum", {"w:abstractNumId": "42"}, [
        xml_element("w:lvl", {"w:ilvl": "0"}, [
            xml_element("w:numFmt", {"w:val": "bullet"})
        ]),
        xml_element("w:lvl", {"w:ilvl": "1"}, [
            xml_element("w:numFmt", {"w:val": "decimal"})
        ])
    ]),
    xml_element("w:num", {"w:numId": "47"}, [
        xml_element("w:abstractNumId", {"w:val": "42"})
    ])
])


@istest
def level_includes_level_index():
    numbering = read_numbering_xml_element(_sample_numbering_xml)
    assert_equal("0", numbering.find_level("47", "0").level_index)
    assert_equal("1", numbering.find_level("47", "1").level_index)


@istest
def list_is_not_ordered_if_formatted_as_bullet():
    numbering = read_numbering_xml_element(_sample_numbering_xml)
    assert_equal(False, numbering.find_level("47", "0").is_ordered)

@istest
def list_is_ordered_if_formatted_as_decimal():
    numbering = read_numbering_xml_element(_sample_numbering_xml)
    assert_equal(True, numbering.find_level("47", "1").is_ordered)
