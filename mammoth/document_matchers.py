import collections


def paragraph(style_name=None):
    return ParagraphMatcher(style_name)


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", ["style_name"])
