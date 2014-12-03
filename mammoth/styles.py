import collections


Style = collections.namedtuple("Style", [
    "document_matcher",
    "html_path",
])


def style(document_matcher, html_path):
    return Style(document_matcher, html_path)
