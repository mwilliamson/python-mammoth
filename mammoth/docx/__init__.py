import zipfile

from ..results import Result
from .xmlparser import parse_xml
from .document_xml import read_document_xml_element


_namespaces = [
    ("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main"),
]


def read(fileobj):
    zip_file = zipfile.ZipFile(fileobj)
    document_fileobj = zip_file.open("word/document.xml")
    document_xml = parse_xml(document_fileobj, _namespaces)
    return read_document_xml_element(document_xml)

