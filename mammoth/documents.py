import cobble


class Element(object):
    pass


class HasChildren(Element):
    children = cobble.field()


@cobble.data
class Document(HasChildren):
    notes = cobble.field()

@cobble.data
class Paragraph(HasChildren):
    style_id = cobble.field()
    style_name = cobble.field()
    numbering = cobble.field()

@cobble.data
class Run(HasChildren):
    style_id = cobble.field()
    style_name = cobble.field()
    is_bold = cobble.field()
    is_italic = cobble.field()
    is_underline = cobble.field()
    is_strikethrough = cobble.field()
    vertical_alignment = cobble.field()

@cobble.data
class Text(Element):
    value = cobble.field()

@cobble.data
class Hyperlink(HasChildren):
    href = cobble.field()
    anchor = cobble.field()

@cobble.data
class Table(HasChildren):
    pass

@cobble.data
class TableRow(HasChildren):
    pass

@cobble.data
class TableCell(HasChildren):
    colspan = cobble.field()
    rowspan = cobble.field()

@cobble.data
class LineBreak(Element):
    pass

@cobble.data
class Tab(Element):
    pass
    

@cobble.visitable
class Image(Element):
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

def run(children, style_id=None, style_name=None, is_bold=None, is_italic=None, is_underline=None, is_strikethrough=None, vertical_alignment=None):
    if vertical_alignment is None:
        vertical_alignment = VerticalAlignment.baseline
    return Run(
        children, style_id, style_name, bool(is_bold), bool(is_italic),
        bool(is_underline), bool(is_strikethrough), vertical_alignment,
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
    return Hyperlink(href=href, anchor=anchor, children=children)


@cobble.data
class Bookmark(Element):
    name = cobble.field()

bookmark = Bookmark
    

table = Table
table_row = TableRow
def table_cell(children, colspan=None, rowspan=None):
    if colspan is None:
        colspan = 1
    if rowspan is None:
        rowspan = 1
    return TableCell(children=children, colspan=colspan, rowspan=rowspan)


line_break = LineBreak

def numbering_level(level_index, is_ordered):
    return _NumberingLevel(str(level_index), bool(is_ordered))

@cobble.data
class _NumberingLevel(object):
    level_index = cobble.field()
    is_ordered = cobble.field()

@cobble.data
class Note(Element):
    note_type = cobble.field()
    note_id = cobble.field()
    body = cobble.field()


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

@cobble.data
class NoteReference(Element):
    note_type = cobble.field()
    note_id = cobble.field()

note_reference = NoteReference


ElementVisitor = cobble.visitor(Element)
