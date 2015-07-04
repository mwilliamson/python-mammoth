from .. import documents


def read_document_xml_element(element,
        body_reader,
        notes=None):
    
    if notes is None:
        notes = []
    
    body_element = element.find_child("w:body")
    return body_reader.read_all(body_element.children) \
        .map(lambda children: documents.document(children, documents.notes(notes)))
