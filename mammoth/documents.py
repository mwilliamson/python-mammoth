import collections


Document = collections.namedtuple("Document", ["children"])
Paragraph = collections.namedtuple("Paragraph", ["children"])
Run = collections.namedtuple("Run", ["children"])
Text = collections.namedtuple("Text", ["value"])
