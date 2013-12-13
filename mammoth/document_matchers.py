import collections


def paragraph(style_name=None, numbering=None):
    return ParagraphMatcher(style_name, numbering)


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", ["style_name", "numbering"])


def run(style_name=None):
    return RunMatcher(style_name)


RunMatcher = collections.namedtuple("RunMatcher", ["style_name"])
