import collections

Document = collections.namedtuple("Document", ["children"])
Paragraph = collections.namedtuple("Paragraph", ["children", "style_name", "numbering"])
Run = collections.namedtuple("Run", ["children", "style_name", "is_bold", "is_italic"])
Text = collections.namedtuple("Text", ["value"])


document = Document

def paragraph(children, style_name=None, numbering=None):
    return Paragraph(children, style_name, numbering)

def run(children, style_name=None, is_bold=None, is_italic=None):
    return Run(children, style_name, bool(is_bold), bool(is_italic))

text = Text
