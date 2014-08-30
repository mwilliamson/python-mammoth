import dodge


Document = dodge.data_class("Document", ["children", "footnotes"])
Paragraph = dodge.data_class("Paragraph", ["children", "style_id", "style_name", "numbering"])
Run = dodge.data_class("Run", ["children", "style_id", "style_name", "is_bold", "is_italic", "is_underline"])
Text = dodge.data_class("Text", ["value"])
Hyperlink = dodge.data_class("Hyperlink", ["href", "children"])
Table = dodge.data_class("Table", ["children"])
TableRow = dodge.data_class("TableRow", ["children"])
TableCell = dodge.data_class("TableCell", ["children"])
LineBreak = dodge.data_class("LineBreak", [])

class Tab(object):
    pass


class Image(object):
    def __init__(self, alt_text, content_type, open):
        self.alt_text = alt_text
        self.content_type = content_type
        self.open = open


def document(children, footnotes=None):
    if footnotes is None:
        footnotes = Footnotes({})
    return Document(children, footnotes)

def paragraph(children, style_id=None, style_name=None, numbering=None):
    return Paragraph(children, style_id, style_name, numbering)

def run(children, style_id=None, style_name=None, is_bold=None, is_italic=None, is_underline=None):
    return Run(children, style_id, style_name, bool(is_bold), bool(is_italic), bool(is_underline))

text = Text

_tab = Tab()

def tab():
    return _tab


image = Image
hyperlink = Hyperlink
table = Table
table_row = TableRow
table_cell = TableCell
line_break = LineBreak

def numbering_level(level_index, is_ordered):
    return _NumberingLevel(str(level_index), bool(is_ordered))

_NumberingLevel = dodge.data_class("NumberingLevel", ["level_index", "is_ordered"])


footnote = Footnote = dodge.data_class("Footnote", ["id", "body"])


class Footnotes(object):
    def __init__(self, footnotes):
        self._footnotes = footnotes
    
    def find_footnote_by_id(self, id):
        return self._footnotes[id]
    
    def __eq__(self, other):
        return isinstance(other, Footnotes) and self._footnotes == other._footnotes

    def __ne__(self, other):
        return not (self == other)

footnotes = Footnotes
