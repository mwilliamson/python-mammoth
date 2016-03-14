import os

from .. import results, lists
from .document_xml import read_document_xml_element
from .content_types_xml import read_content_types_xml_element
from .relationships_xml import read_relationships_xml_element, Relationships
from .numbering_xml import read_numbering_xml_element, Numbering
from .styles_xml import read_styles_xml_element
from .notes_xml import create_footnotes_reader, create_endnotes_reader
from .files import Files
from . import body_xml, office_xml
from ..zips import open_zip


def read(fileobj):
    zip_file = open_zip(fileobj, "r")
    body_readers = _body_readers(getattr(fileobj, "name", None), zip_file)
    
    return _read_notes(zip_file, body_readers).bind(lambda notes:
        _read_document(zip_file, body_readers, notes))


def _read_notes(zip_file, body_readers):
    empty_result = results.success([])
    
    read_footnotes_xml = create_footnotes_reader(body_readers("footnotes"))
    footnotes = _try_read_entry_or_default(
        zip_file, "word/footnotes.xml", read_footnotes_xml, default=empty_result)
    
    read_endnotes_xml = create_endnotes_reader(body_readers("endnotes"))
    endnotes = _try_read_entry_or_default(
        zip_file, "word/endnotes.xml", read_endnotes_xml, default=empty_result)
    
    return results.combine([footnotes, endnotes]).map(lists.flatten)
    
def _read_document(zip_file, body_readers, notes):
    with zip_file.open("word/document.xml") as document_fileobj:
        document_xml = office_xml.read(document_fileobj)
        return read_document_xml_element(
            document_xml,
            body_reader=body_readers("document"),
            notes=notes,
        )


def _body_readers(document_path, zip_file):
    with zip_file.open("[Content_Types].xml") as content_types_fileobj:
        content_types = read_content_types_xml_element(office_xml.read(content_types_fileobj))

    numbering = _try_read_entry_or_default(
        zip_file, "word/numbering.xml", read_numbering_xml_element, default=Numbering({}))
    
    with zip_file.open("word/styles.xml") as styles_fileobj:
        styles = read_styles_xml_element(office_xml.read(styles_fileobj))
    
    def for_name(name):
        relationships_path = "word/_rels/{0}.xml.rels".format(name)
        relationships = _try_read_entry_or_default(
            zip_file, relationships_path, read_relationships_xml_element,
            default=Relationships({}))
            
        return body_xml.reader(
            numbering=numbering,
            content_types=content_types,
            relationships=relationships,
            styles=styles,
            docx_file=zip_file,
            files=Files(None if document_path is None else os.path.dirname(document_path)),
        )
    
    return for_name


def _try_read_entry_or_default(zip_file, name, reader, default):
    if zip_file.exists(name):
        with zip_file.open(name) as fileobj:
            return reader(office_xml.read(fileobj))
    else:
        return default
