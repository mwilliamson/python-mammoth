import dodge

#:type Node = Document | Paragraph | Run | Text | Hyperlink | Table | TableRow | TableCell | LineBreak
Node = None


Document = dodge.data_class("Document", [
    #:field list[Node]
    "children",
    #:field Notes
    "notes"
])

Paragraph = dodge.data_class("Paragraph", [
    #:field list[Node]
    "children",
    #:field str
    "style_id",
    #:field str
    "style_name",
    #:field Numbering
    "numbering"
])


class Numbering(object):
    def __init__(self, nums):
        self._nums = nums
    
    def find_level(self, num_id, level):
        num = self._nums.get(num_id)
        if num is None:
            return None
        else:
            return num[level]
            
Run = dodge.data_class("Run", [
    #:field list[Node]
    "children",
    #:field str
    "style_id",
    #:field str
    "style_name",
    #:field bool
    "is_bold",
    #:field bool
    "is_italic",
    #:field bool
    "is_underline",
    #:field str 
    "vertical_alignment",
])
Text = dodge.data_class("Text", [
    #:field str
    "value"
])
Hyperlink = dodge.data_class("Hyperlink", [
    #:field str
    "href",
    #:field str
    "anchor",
    #:field list[Node]
    "children"
])
Table = dodge.data_class("Table", [
    #:field list[Node]
    "children"
])
TableRow = dodge.data_class("TableRow", [
    #:field list[Node]
    "children"
])
TableCell = dodge.data_class("TableCell", [
    #:field list[Node]
    "children"
])
LineBreak = dodge.data_class("LineBreak", [])

class Tab(object):
    pass


class Image(object):
    def __init__(self, alt_text, content_type, open):
        self.alt_text = alt_text
        self.content_type = content_type
        self.open = open


def document(children, notes=None):
    if notes is None:
        notes = Notes({})
    return Document(children, notes)

def paragraph(children, style_id=None, style_name=None, numbering=None):
    return Paragraph(children, style_id, style_name, numbering)

def run(children, style_id=None, style_name=None, is_bold=None, is_italic=None, is_underline=None, vertical_alignment=None):
    if vertical_alignment is None:
        vertical_alignment = VerticalAlignment.baseline
    return Run(
        children, style_id, style_name, bool(is_bold), bool(is_italic),
        bool(is_underline), vertical_alignment,
    )

class VerticalAlignment(object):
    baseline = "baseline"
    superscript = "superscript"
    subscript = "subscript"

text = Text

_tab = Tab()

def tab():
    return _tab


image = Image

def hyperlink(children, href=None, anchor=None):
    return Hyperlink(href, anchor, children)

Bookmark = dodge.data_class("Bookmark", [
    #:field str
    "name"
])
bookmark = Bookmark
    

table = Table
table_row = TableRow
table_cell = TableCell
line_break = LineBreak

def numbering_level(level_index, is_ordered):
    return _NumberingLevel(str(level_index), bool(is_ordered))

_NumberingLevel = dodge.data_class("_NumberingLevel", [
    #:field int
    "level_index",
    #:field bool
    "is_ordered"
])


Note = dodge.data_class("Note", [
    #:field str
    "note_type",
    #:field str
    "note_id",
    #:field list[Node]
    "body"
])
note = Note


class Notes(object):
    def __init__(self, notes):
        self._notes = notes
    
    def find_note(self, note_type, note_id):
        return self._notes[(note_type, note_id)]
    
    def resolve(self, reference):
        return self.find_note(reference.note_type, reference.note_id)
    
    def __eq__(self, other):
        return isinstance(other, Notes) and self._notes == other._notes

    def __ne__(self, other):
        return not (self == other)

def notes(notes_list):
    return Notes(dict(
        (_note_key(note), note)
        for note in notes_list
    ))
    
def _note_key(note):
    return (note.note_type, note.note_id)

NoteReference = dodge.data_class("NoteReference", [
    #:field str
    "note_type",
    #:field str
    "note_id"
])
note_reference = NoteReference
