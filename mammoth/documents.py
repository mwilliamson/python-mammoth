import dodge

Footnote = dodge.data_class("Footnote", [
    #:: str
    "id",
    #:: str
    "body"
])
footnote = Footnote


class Footnotes(object):
    #:: Self, dict[str, Footnote] -> none
    def __init__(self, footnotes):
        self._footnotes = footnotes
    
    #:: Self, str -> Footnote
    def find_footnote_by_id(self, id):
        return self._footnotes[id]
    
    #:: Self, object -> bool
    def __eq__(self, other):
        if not isinstance(other, Footnotes):
            return False
        else:
            return self._footnotes == other._footnotes

    #:: Self, object -> bool
    def __ne__(self, other):
        return not (self == other)

footnotes = Footnotes

NumberingLevel = dodge.data_class("NumberingLevel", [
    #:: str
    "level_index",
    #:: bool
    "is_ordered",
])

#:: str, bool -> NumberingLevel
def numbering_level(level_index, is_ordered):
    return NumberingLevel(str(level_index), bool(is_ordered))


# TODO: base type for document nodes
Document = dodge.data_class("Document", [
    #:: list[object]
    "children",
    #:: Footnotes
    "footnotes",
])

Paragraph = dodge.data_class("Paragraph", [
    #:: list[object]
    "children",
    #:: str | none
    "style_id",
    #:: str | none
    "style_name",
    #:: NumberingLevel | none
    "numbering",
])

Run = dodge.data_class("Run", [
    #:: list[object]
    "children",
    #:: str | none
    "style_id",
    #:: str | none
    "style_name",
    #:: bool
    "is_bold",
    #:: bool
    "is_italic",
    #:: bool
    "is_underline",
    #:: str
    "vertical_alignment",
])

Text = dodge.data_class("Text", [
    #:: str
    "value"
])

Hyperlink = dodge.data_class("Hyperlink", [
    #:: str
    "href",
    #:: list[object]
    "children"
])

Table = dodge.data_class("Table", [
    #:: list[object]
    "children"
])

TableRow = dodge.data_class("TableRow", [
    #:: list[object]
    "children"
])

TableCell = dodge.data_class("TableCell", [
    #:: list[object]
    "children"
])

LineBreak = dodge.data_class("LineBreak", [])

class Tab(object):
    pass


# TODO: type of open should be ( -> file)
class Image(object):
    #:: Self, str, str, ( -> none) -> none
    def __init__(self, alt_text, content_type, open):
        self.alt_text = alt_text
        self.content_type = content_type
        self.open = open

FootnoteReference = dodge.data_class("FootnoteReference", [
    #:: str
    "footnote_id"
])
footnote_reference = FootnoteReference

#:: list[object], ?footnotes: Footnotes -> Document
def document(children, footnotes=None):
    if footnotes is None:
        footnotes = Footnotes({})
    return Document(children, footnotes)

#:: list[object], ?style_id: str, ?style_name: str, ?numbering: NumberingLevel -> Paragraph
def paragraph(children, style_id=None, style_name=None, numbering=None):
    return Paragraph(children, style_id, style_name, numbering)

class VerticalAlignment(object):
    baseline = "baseline"
    superscript = "superscript"
    subscript = "subscript"

#:: list[object], ?style_id: str, ?style_name: str, ?is_bold: bool, ?is_italic: bool, ?is_underline: bool, ?vertical_alignment: str -> Run
def run(children, style_id=None, style_name=None, is_bold=None, is_italic=None, is_underline=None, vertical_alignment=None):
    if vertical_alignment is None:
        vertical_alignment = VerticalAlignment.baseline
    return Run(
        children, style_id, style_name, bool(is_bold), bool(is_italic),
        bool(is_underline), vertical_alignment,
    )

text = Text

_tab = Tab()

#:: -> Tab
def tab():
    return _tab


image = Image
hyperlink = Hyperlink
table = Table
table_row = TableRow
table_cell = TableCell
line_break = LineBreak
