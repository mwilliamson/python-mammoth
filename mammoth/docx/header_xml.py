import functools
from .. import documents

def _read_extremity(extremity, element, body_reader):
    return body_reader.read_all(element.children) \
        .map(lambda children: extremity(children))

read_header_xml_element = functools.partial(_read_extremity, documents.header)
read_footer_xml_element = functools.partial(_read_extremity, documents.footer)