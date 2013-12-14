import collections

Document = collections.namedtuple("Document", ["children"])
Paragraph = collections.namedtuple("Paragraph", ["children", "style_name", "numbering"])
Run = collections.namedtuple("Run", ["children", "style_name", "is_bold", "is_italic"])
Text = collections.namedtuple("Text", ["value"])
Hyperlink = collections.namedtuple("Hyperlink", ["href", "children"])

class Tab(object):
    pass


class Image(object):
    def __init__(self, alt_text, content_type, open):
        self.alt_text = alt_text
        self.content_type = content_type
        self.open = open


document = Document

def paragraph(children, style_name=None, numbering=None):
    return Paragraph(children, style_name, numbering)

def run(children, style_name=None, is_bold=None, is_italic=None):
    return Run(children, style_name, bool(is_bold), bool(is_italic))

text = Text

_tab = Tab()

def tab():
    return _tab


image = Image
hyperlink = Hyperlink


def numbering_level(level_index, is_ordered):
    return _NumberingLevel(str(level_index), bool(is_ordered))

_NumberingLevel = collections.namedtuple("NumberingLevel", ["level_index", "is_ordered"])
