import io

from nose.tools import istest, assert_equal

from mammoth.docx.xmlparser import parse_xml, element as xml_element, text as xml_text


@istest
def can_parse_self_closing_element():
    xml = _parse_xml_string(b"<body/>")
    assert_equal(xml_element("body", {}, []), xml)


@istest
def can_parse_empty_element_with_separate_closing_tag():
    xml = _parse_xml_string(b"<body></body>")
    assert_equal(xml_element("body", {}, []), xml)


@istest
def can_parse_attributes_of_tag():
    xml = _parse_xml_string(b"<body name='bob'></body>")
    assert_equal(xml_element("body", {"name": "bob"}, []), xml)


@istest
def can_parse_text_element():
    xml = _parse_xml_string(b"<body>Hello!</body>")
    assert_equal(xml_element("body", {}, [xml_text("Hello!")]), xml)


@istest
def can_parse_text_element_before_new_tag():
    xml = _parse_xml_string(b"<body>Hello!<br/></body>")
    assert_equal(xml_element("body", {}, [xml_text("Hello!"), xml_element("br", {}, [])]), xml)


@istest
def can_parse_element_with_children():
    xml = _parse_xml_string(b"<body><a/><b/></body>")
    assert_equal([xml_element("a", {}, []), xml_element("b", {}, [])], xml.children)


@istest
def unmapped_namespaces_uris_are_included_in_braces_as_prefix():
    xml = _parse_xml_string(b'<w:body xmlns:w="word"/>')
    assert_equal("{word}body", xml.name)


@istest
def mapped_namespaces_uris_are_translated_using_namespace_map():
    xml = _parse_xml_string(b'<w:body xmlns:w="word"/>', [("x", "word")])
    assert_equal("x:body", xml.name)


@istest
def namespace_of_attributes_is_mapped_to_prefix():
    xml = _parse_xml_string(b'<w:body xmlns:w="word" w:val="Hello!"/>', [("x", "word")])
    assert_equal("Hello!", xml.attributes["x:val"])


@istest
def whitespace_between_xml_declaration_and_root_tag_is_ignored():
    xml = _parse_xml_string(b'<?xml version="1.0" ?>\n<body/>')
    assert_equal("body", xml.name)


def _parse_xml_string(string, namespace_mapping=None):
    return parse_xml(io.BytesIO(string), namespace_mapping)
