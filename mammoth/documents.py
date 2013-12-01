import collections

Document = collections.namedtuple("Document", ["children"])
Paragraph = collections.namedtuple("Paragraph", ["children", "style_name", "numbering"])
Run = collections.namedtuple("Run", ["children", "style_name", "is_bold"])
Text = collections.namedtuple("Text", ["value"])


document = Document

def paragraph(children, style_name=None, numbering=None):
    return Paragraph(children, style_name, numbering)

def run(children, style_name=None, is_bold=None):
    return Run(children, style_name, bool(is_bold))

text = Text
