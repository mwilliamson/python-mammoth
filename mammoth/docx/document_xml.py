from .. import documents
from .. import results


def read_document_xml_element(element,
        body_reader,
        footnote_elements=None,
        endnote_elements=None):
    
    note_elements = (footnote_elements or []) + (endnote_elements or [])
    
    def _read_note(element):
        return body_reader.read_all(element.body).map(
            lambda body: documents.note(element.note_type, element.id, body))

    body_element = element.find_child("w:body")
    children_result = body_reader.read_all(body_element.children)
    notes_result = results.combine(map(_read_note, note_elements)).map(documents.notes)
    return results.map(documents.document, children_result, notes_result)
