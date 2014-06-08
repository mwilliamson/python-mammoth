from nose.tools import istest, assert_equal

from mammoth.docx.xmlparser import element as xml_element
from mammoth.docx.styles_xml import read_styles_xml_element


@istest
def paragraph_style_is_null_if_no_style_with_that_id_exists():
    element = xml_element("w:styles")
    styles = read_styles_xml_element(element)
    assert_equal(None, styles.find_paragraph_style_by_id("Heading1"))


@istest
def paragraph_style_can_be_found_by_id():
    element = xml_element("w:styles", {}, [
        _paragraph_style_element("Heading1", "Heading 1"),
    ])
    styles = read_styles_xml_element(element)
    assert_equal("Heading1", styles.find_paragraph_style_by_id("Heading1").style_id)


def _paragraph_style_element(style_id, name):
    return _style_element("paragraph", style_id, name)

def _style_element(element_type, style_id, name):
    return xml_element("w:style", {"w:type": element_type, "w:styleId": style_id}, [
        xml_element("w:name", {"w:val": name}, [])
    ])
