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
    assert_equal(
        "Heading1",
        styles.find_paragraph_style_by_id("Heading1").style_id
    )


@istest
def character_style_can_be_found_by_id():
    element = xml_element("w:styles", {}, [
        _character_style_element("Heading1Char", "Heading 1 Char"),
    ])
    styles = read_styles_xml_element(element)
    assert_equal(
        "Heading1Char",
        styles.find_character_style_by_id("Heading1Char").style_id
    )


@istest
def table_style_can_be_found_by_id():
    element = xml_element("w:styles", {}, [
        _table_style_element("TableNormal", "Normal Table"),
    ])
    styles = read_styles_xml_element(element)
    assert_equal(
        "TableNormal",
        styles.find_table_style_by_id("TableNormal").style_id
    )


@istest
def paragraph_and_character_styles_are_distinct():
    element = xml_element("w:styles", {}, [
        _paragraph_style_element("Heading1", "Heading 1"),
        _character_style_element("Heading1Char", "Heading 1 Char"),
    ])
    styles = read_styles_xml_element(element)
    assert_equal(None, styles.find_character_style_by_id("Heading1"))
    assert_equal(None, styles.find_paragraph_style_by_id("Heading1Char"))


@istest
def styles_include_names():
    element = xml_element("w:styles", {}, [
        _paragraph_style_element("Heading1", "Heading 1"),
    ])
    styles = read_styles_xml_element(element)
    assert_equal(
        "Heading 1",
        styles.find_paragraph_style_by_id("Heading1").name
    )


@istest
def style_name_is_none_if_name_element_does_not_exist():
    element = xml_element("w:styles", {}, [
        _style_without_name_element("paragraph", "Heading1"),
        _style_without_name_element("character", "Heading1Char")
    ])
    styles = read_styles_xml_element(element)
    assert_equal(None, styles.find_paragraph_style_by_id("Heading1").name)
    assert_equal(None, styles.find_character_style_by_id("Heading1Char").name)


def _paragraph_style_element(style_id, name):
    return _style_element("paragraph", style_id, name)

def _character_style_element(style_id, name):
    return _style_element("character", style_id, name)

def _table_style_element(style_id, name):
    return _style_element("table", style_id, name)

def _style_element(element_type, style_id, name):
    children = [xml_element("w:name", {"w:val": name}, [])]
    return _style_element_with_children(element_type, style_id, children)

def _style_without_name_element(element_type, style_id):
    return _style_element_with_children(element_type, style_id, [])

def _style_element_with_children(element_type, style_id, children):
    attributes = {"w:type": element_type, "w:styleId": style_id}
    return xml_element("w:style", attributes, children)
