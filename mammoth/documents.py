import collections


def paragraph(children, style_name=None):
    return Paragraph(children, style_name)


Document = collections.namedtuple("Document", ["children"])
Paragraph = collections.namedtuple("Paragraph", ["children", "style_name"])
Run = collections.namedtuple("Run", ["children"])
Text = collections.namedtuple("Text", ["value"])
