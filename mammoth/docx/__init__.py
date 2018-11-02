from functools import partial
import os

import cobble   

from .. import results, lists, zips
from .document_xml import read_document_xml_element
from .header_xml import (read_header_xml_element, read_footer_xml_element)
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
    part_paths = _find_part_paths(zip_file)
    read_part_with_body = _part_with_body_reader(
        getattr(fileobj, "name", None),
        zip_file,
        part_paths=part_paths,
    )

    return results.combine([
        _read_notes(read_part_with_body, part_paths),
        _read_comments(read_part_with_body, part_paths),
        _read_headers(read_part_with_body, part_paths),
        _read_footers(read_part_with_body, part_paths)
    ]).bind(lambda referents:
        _read_document(zip_file, read_part_with_body, notes=referents[0], comments=referents[1], headers=referents[2], footers=referents[3], part_paths=part_paths)
    )


@cobble.data
class _PartPaths(object):
    main_document = cobble.field()
    comments = cobble.field()
    endnotes = cobble.field()
    footnotes = cobble.field()
    numbering = cobble.field()
    headers = cobble.field()
    footers = cobble.field()
    styles = cobble.field()


def _find_part_paths(zip_file):
    package_relationships = _read_relationships(zip_file, "_rels/.rels")
    document_filename = _find_document_filename(zip_file, package_relationships)
    
    document_relationships = _read_relationships(
        zip_file,
        _find_relationships_path_for(document_filename),
    )
    
    def find(name, multiple=False):
        return _find_part_path(
            zip_file=zip_file,
            relationships=document_relationships,
            relationship_type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/" + name,
            fallback_path="word/{0}.xml".format(name),
            base_path=zips.split_path(document_filename)[0],
            multiple=multiple
        )

    return _PartPaths(
        main_document=document_filename,
        comments=find("comments"),
        endnotes=find("endnotes"),
        footnotes=find("footnotes"),
        numbering=find("numbering"),
        headers=find("header", multiple=True),
        footers=find("footer", multiple=True),
        styles=find("styles"),
    )


def _find_document_filename(zip_file, relationships):
    path = _find_part_path(
        zip_file,
        relationships,
        relationship_type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        base_path="",
        fallback_path="word/document.xml",
    )
    if zip_file.exists(path):
        return path
    else:
        raise IOError("Could not find main document part. Are you sure this is a valid .docx file?")


def _find_part_path(zip_file, relationships, relationship_type, base_path, fallback_path, multiple=False):
    targets = [
        zips.join_path(base_path, target).lstrip("/")
        for target in relationships.find_targets_by_type(relationship_type)
    ]
    valid_targets = list(filter(lambda target: zip_file.exists(target), targets))
    if len(valid_targets) == 0:
        return fallback_path
    else:
        return valid_targets if multiple else valid_targets[0]


def _read_notes(read_part_with_body, part_paths):
    footnotes = read_part_with_body(
        part_paths.footnotes,
        lambda root, body_reader: read_footnotes_xml_element(root, body_reader=body_reader),
        default=_empty_result,
    )
    endnotes = read_part_with_body(
        part_paths.endnotes,
        lambda root, body_reader: read_endnotes_xml_element(root, body_reader=body_reader),
        default=_empty_result,
    )

    return results.combine([footnotes, endnotes]).map(lists.flatten)


def _read_comments(read_part_with_body, part_paths):
    return read_part_with_body(
        part_paths.comments,
        lambda root, body_reader: read_comments_xml_element(root, body_reader=body_reader),
        default=_empty_result,
    )

def _read_headers(read_part_with_body, part_paths):
    if type(part_paths.headers) == str:
        header_paths = [part_paths.headers]
    else:
        header_paths = part_paths.headers

    headers = [
        read_part_with_body(header,
            lambda root, body_reader: read_header_xml_element(root, body_reader=body_reader),
        default=_empty_result) for header in header_paths]
    return [h for h in headers if h.value != []]


def _read_footers(read_part_with_body, part_paths):
    if type(part_paths.footers) == str:
        footer_paths = [part_paths.footers]
    else:
        footer_paths = part_paths.footers

    footers = [
        read_part_with_body(footer,
            lambda root, body_reader: read_footer_xml_element(root, body_reader=body_reader),
        default=_empty_result) for footer in footer_paths]

    return [f for f in footers if f.value != []]

    
def _read_document(zip_file, read_part_with_body, notes, comments, headers, footers, part_paths):
    return read_part_with_body(
        part_paths.main_document,
        partial(
            read_document_xml_element,
            notes=notes,
            comments=comments,
            headers=headers,
            footers=footers
        ),
    )


def _part_with_body_reader(document_path, zip_file, part_paths):
    content_types = _try_read_entry_or_default(
        zip_file,
        "[Content_Types].xml",
        read_content_types_xml_element,
        empty_content_types,
    )

    numbering = _try_read_entry_or_default(
        zip_file,
        part_paths.numbering,
        read_numbering_xml_element,
        default=Numbering({}),
    )
    
    styles = _try_read_entry_or_default(
        zip_file,
        part_paths.styles,
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
