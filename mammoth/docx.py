import zipfile

from . import documents
from .results import Result
from .xmlparser import parse_xml, node_types


_namespaces = [
    ("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main"),
]


def read(fileobj):
    zip_file = zipfile.ZipFile(fileobj)
    document_fileobj = zip_file.open("word/document.xml")
    document_xml = parse_xml(document_fileobj, _namespaces)
    return Result(read_xml_element(document_xml), [])


_handlers = {}


def handler(name):
    def add(func):
        _handlers[name] = func
        
    return add


def read_xml_element(element):
    handler = _handlers.get(element.name)
    if handler is None:
        return None
    else:
        return handler(element)


@handler("w:t")
def text(element):
    return documents.Text(_inner_text(element))


@handler("w:r")
def run(element):
    return documents.Run(_read_xml_elements(element.children))


@handler("w:p")
def paragraph(element):
    return documents.paragraph(_read_xml_elements(element.children))


@handler("w:body")
def paragraph(element):
    return _read_xml_elements(element.children)


@handler("w:document")
def paragraph(element):
    body_element = _find(lambda child: child.name == "w:body", element.children)
    return documents.Document(_read_xml_elements(body_element.children))


def _find(predicate, iterable):
    for item in iterable:
        if predicate(item):
            return item


def _read_xml_elements(elements):
    return filter(None, map(read_xml_element, elements))


def _inner_text(node):
    if node.node_type == node_types.text:
        return node.value
    else:
        return "".join(_inner_text(child) for child in node.children)
