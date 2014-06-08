import dodge


Document = dodge.data_class("Document", ["children"])
Paragraph = dodge.data_class("Paragraph", ["children", "style_id", "style_name", "numbering"])
Run = dodge.data_class("Run", ["children", "style_id", "is_bold", "is_italic"])
Text = dodge.data_class("Text", ["value"])
Hyperlink = dodge.data_class("Hyperlink", ["href", "children"])

class Tab(object):
    pass


class Image(object):
    def __init__(self, alt_text, content_type, open):
        self.alt_text = alt_text
        self.content_type = content_type
        self.open = open


document = Document

def paragraph(children, style_id=None, style_name=None, numbering=None):
    return Paragraph(children, style_id, style_name, numbering)

def run(children, style_id=None, is_bold=None, is_italic=None):
    return Run(children, style_id, bool(is_bold), bool(is_italic))

text = Text

_tab = Tab()

def tab():
    return _tab


image = Image
hyperlink = Hyperlink


def numbering_level(level_index, is_ordered):
    return _NumberingLevel(str(level_index), bool(is_ordered))

_NumberingLevel = dodge.data_class("NumberingLevel", ["level_index", "is_ordered"])
