from functools import partial
import os

from .. import results, lists, zips
from .document_xml import read_document_xml_element
from .content_types_xml import empty_content_types, read_content_types_xml_element
from .relationships_xml import read_relationships_xml_element, Relationships
from .numbering_xml import read_numbering_xml_element, Numbering
from .styles_xml import read_styles_xml_element, Styles
from .notes_xml import read_endnotes_xml_element, read_footnotes_xml_element
from .comments_xml import read_comments_xml_element
from .files import Files
from . import body_xml, office_xml
from ..zips import open_zip


_empty_result = results.success([])


def read(fileobj):
    zip_file = open_zip(fileobj, "r")
    read_part_with_body = _part_with_body_reader(getattr(fileobj, "name", None), zip_file)
    
    return results.combine([
        _read_notes(read_part_with_body),
        _read_comments(read_part_with_body),
    ]).bind(lambda referents:
        _read_document(zip_file, read_part_with_body, notes=referents[0], comments=referents[1])
    )


def _read_notes(read_part_with_body):
    footnotes = read_part_with_body(
        "word/footnotes.xml",
        lambda root, body_reader: read_footnotes_xml_element(root, body_reader=body_reader),
        default=_empty_result,
    )
    endnotes = read_part_with_body(
        "word/endnotes.xml",
        lambda root, body_reader: read_endnotes_xml_element(root, body_reader=body_reader),
        default=_empty_result,
    )
    
    return results.combine([footnotes, endnotes]).map(lists.flatten)


def _read_comments(read_part_with_body):
    return read_part_with_body(
        "word/comments.xml",
        lambda root, body_reader: read_comments_xml_element(root, body_reader=body_reader),
        default=_empty_result,
    )

    
def _read_document(zip_file, read_part_with_body, notes, comments):
    package_relationships = _read_relationships(zip_file, "_rels/.rels")
    document_filename = _find_document_filename(zip_file, package_relationships)
    
    return read_part_with_body(
        document_filename,
        partial(
            read_document_xml_element,
            notes=notes,
            comments=comments,
        ),
    )


def _find_document_filename(zip_file, relationships):
    office_document_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    targets = [
        target.lstrip("/")
        for target in relationships.find_targets_by_type(office_document_type)
    ] + ["word/document.xml"]
    valid_targets = list(filter(lambda target: zip_file.exists(target), targets))
    if len(valid_targets) == 0:
        raise IOError("Could not find main document part. Are you sure this is a valid .docx file?")
    else:
        return valid_targets[0]


def _part_with_body_reader(document_path, zip_file):
    content_types = _try_read_entry_or_default(
        zip_file,
        "[Content_Types].xml",
        read_content_types_xml_element,
        empty_content_types,
    )

    numbering = _try_read_entry_or_default(
        zip_file, "word/numbering.xml", read_numbering_xml_element, default=Numbering({}))
    
    styles = _try_read_entry_or_default(
        zip_file,
        "word/styles.xml",
        read_styles_xml_element,
        Styles.EMPTY,
    )
    
    def read_part(name, reader, default=_undefined):
        relationships = _read_relationships(zip_file, _find_relationships_path_for(name))
            
        body_reader = body_xml.reader(
            numbering=numbering,
            content_types=content_types,
            relationships=relationships,
            styles=styles,
            docx_file=zip_file,
            files=Files(None if document_path is None else os.path.dirname(document_path)),
        )

        if default is _undefined:
            return _read_entry(zip_file, name, partial(reader, body_reader=body_reader))
        else:
            return _try_read_entry_or_default(zip_file, name, partial(reader, body_reader=body_reader), default=default)
    
    return read_part



def _find_relationships_path_for(name):
    dirname, basename = zips.split_path(name)
    return zips.join_path(dirname, "_rels", basename + ".rels")
    

def _read_relationships(zip_file, name):
    return _try_read_entry_or_default(
        zip_file,
        name,
        read_relationships_xml_element,
        default=Relationships.EMPTY,
    )

def _try_read_entry_or_default(zip_file, name, reader, default):
    if zip_file.exists(name):
        return _read_entry(zip_file, name, reader)
    else:
        return default


def _read_entry(zip_file, name, reader):
    with zip_file.open(name) as fileobj:
        return reader(office_xml.read(fileobj))


_undefined = object()
