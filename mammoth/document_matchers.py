import collections


def paragraph(style_name=None):
    return ParagraphMatcher(style_name)


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", ["style_name"])


def run(style_name=None):
    return RunMatcher(style_name)


RunMatcher = collections.namedtuple("RunMatcher", ["style_name"])
