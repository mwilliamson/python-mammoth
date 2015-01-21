import zipfile
import contextlib

from .xmlparser import parse_xml
from .document_xml import read_document_xml_element
from .content_types_xml import read_content_types_xml_element
from .relationships_xml import read_relationships_xml_element
from .numbering_xml import read_numbering_xml_element, Numbering
from .styles_xml import read_styles_xml_element
from .notes_xml import read_footnotes_xml_element, read_endnotes_xml_element


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
    
    with _open_entry(zip_file, "[Content_Types].xml") as content_types_fileobj:
        content_types = read_content_types_xml_element(_parse_docx_xml(content_types_fileobj))
    
    with _open_entry(zip_file, "word/_rels/document.xml.rels") as relationships_fileobj:
        relationships = read_relationships_xml_element(_parse_docx_xml(relationships_fileobj))

    numbering = _try_read_entry_or_default(
        zip_file, "word/numbering.xml", read_numbering_xml_element, default=Numbering({}))
    
    with _open_entry(zip_file, "word/styles.xml") as styles_fileobj:
        styles = read_styles_xml_element(_parse_docx_xml(styles_fileobj))
    
    footnote_elements = _try_read_entry_or_default(
        zip_file, "word/footnotes.xml", read_footnotes_xml_element, default=[])
    
    endnote_elements = _try_read_entry_or_default(
        zip_file, "word/endnotes.xml", read_endnotes_xml_element, default=[])
    
    with _open_entry(zip_file, "word/document.xml") as document_fileobj:
        document_xml = _parse_docx_xml(document_fileobj)
        return read_document_xml_element(
            document_xml,
            content_types=content_types,
            relationships=relationships,
            docx_file=zip_file,
            numbering=numbering,
            styles=styles,
            footnote_elements=footnote_elements,
            endnote_elements=endnote_elements,
        )


def _parse_docx_xml(fileobj):
    return parse_xml(fileobj, _namespaces)


@contextlib.contextmanager
def _open_entry(zip_file, name):
    entry = zip_file.open(name)
    try:
        yield entry
    finally:
        entry.close()


def _try_read_entry_or_default(zip_file, name, reader, default):
    if _has_entry(zip_file, name):
        with _open_entry(zip_file, name) as fileobj:
            return reader(_parse_docx_xml(fileobj))
    else:
        return default


def _has_entry(zip_file, name):
    try:
        zip_file.getinfo(name)
        return True
    except KeyError:
        return False
