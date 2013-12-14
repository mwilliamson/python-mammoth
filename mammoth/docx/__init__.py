import zipfile

from ..results import Result
from .xmlparser import parse_xml
from .document_xml import read_document_xml_element
from .content_types_xml import read_content_types_xml_element
from .relationships_xml import read_relationships_xml_element
from .numbering_xml import read_numbering_xml_element, Numbering


_namespaces = [
    ("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main"),
    ("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
    ("a", "http://schemas.openxmlformats.org/drawingml/2006/main"),
    ("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture"),
    ("content-types", "http://schemas.openxmlformats.org/package/2006/content-types"),
    ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships"),
    ("relationships", "http://schemas.openxmlformats.org/package/2006/relationships"),
]

def read(fileobj):
    zip_file = zipfile.ZipFile(fileobj)
    
    with zip_file.open("[Content_Types].xml") as content_types_fileobj:
        content_types = read_content_types_xml_element(_parse_docx_xml(content_types_fileobj))
    
    with zip_file.open("word/_rels/document.xml.rels") as relationships_fileobj:
        relationships = read_relationships_xml_element(_parse_docx_xml(relationships_fileobj))
    
    if _has_entry(zip_file, "word/numbering.xml"):
        with zip_file.open("word/numbering.xml") as numbering_fileobj:
            numbering = read_numbering_xml_element(_parse_docx_xml(numbering_fileobj))
    else:
        numbering = Numbering({})
    
    with zip_file.open("word/document.xml") as document_fileobj:
        document_xml = _parse_docx_xml(document_fileobj)
        return read_document_xml_element(
            document_xml,
            content_types=content_types,
            relationships=relationships,
            docx_file=zip_file,
            numbering=numbering,
        )


def _parse_docx_xml(fileobj):
    return parse_xml(fileobj, _namespaces)


def _has_entry(zip_file, name):
    try:
        zip_file.getinfo(name)
        return True
    except KeyError:
        return False
