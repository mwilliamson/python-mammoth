import collections


def paragraph(children, style_name=None, numbering=None):
    return Paragraph(children, style_name, numbering)


Document = collections.namedtuple("Document", ["children"])
Paragraph = collections.namedtuple("Paragraph", ["children", "style_name", "numbering"])
Run = collections.namedtuple("Run", ["children"])
Text = collections.namedtuple("Text", ["value"])
