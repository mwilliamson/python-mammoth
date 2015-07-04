from .. import documents
from .. import results
from . import body_xml


def read_document_xml_element(element,
        numbering=None,
        content_types=None,
        relationships=None,
        styles=None,
        footnote_elements=None,
        endnote_elements=None,
        docx_file=None):
    
    note_elements = (footnote_elements or []) + (endnote_elements or [])
    
    body_reader = body_xml.reader(
        numbering=numbering,
        content_types=content_types,
        relationships=relationships,
        styles=styles,
        docx_file=docx_file,
    )
    
    def _read_note(element):
        return body_reader.read_all(element.body).map(
            lambda body: documents.note(element.note_type, element.id, body))

    body_element = element.find_child("w:body")
    children_result = body_reader.read_all(body_element.children)
    notes_result = results.combine(map(_read_note, note_elements)).map(documents.notes)
    return results.map(documents.document, children_result, notes_result)
