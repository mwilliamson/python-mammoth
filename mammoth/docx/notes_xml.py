import functools

from .. import lists
from .. import documents
from .. import results


def create_reader(note_type, body_reader):
    def read_notes_xml_element(element):
        note_elements = lists.filter(
            _is_note_element,
            element.find_children("w:" + note_type),
        )
        return results.combine(lists.map(_read_note_element, note_elements))


    def _is_note_element(element):
        return element.attributes.get("w:type") not in ["continuationSeparator", "separator"]


    def _read_note_element(element):
        return body_reader.read_all(element.children).map(lambda body: 
            documents.note(
                note_type=note_type,
                note_id=element.attributes["w:id"],
                body=body
            ))
    
    return read_notes_xml_element

create_footnotes_reader = functools.partial(create_reader, "footnote")
create_endnotes_reader = functools.partial(create_reader, "endnote")
