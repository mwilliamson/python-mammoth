from .. import lists


def create_reader(note_type):
    def read_notes_xml_element(element):
        note_elements = lists.filter(
            _is_note_element,
            element.find_children("w:" + note_type),
        )
        return lists.map(_read_note_element, note_elements)


    def _is_note_element(element):
        return element.attributes.get("w:type") not in ["continuationSeparator", "separator"]


    def _read_note_element(element):
        return NoteElement(note_type, element.attributes["w:id"], element.children)
    
    return read_notes_xml_element

class NoteElement(object):
    def __init__(self, note_type, id, body):
        self.note_type = note_type
        self.id = id
        self.body = body


read_footnotes_xml_element = create_reader("footnote")
read_endnotes_xml_element = create_reader("endnote")
