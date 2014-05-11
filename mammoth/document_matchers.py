import collections


def paragraph(style_id=None, numbering=None):
    return ParagraphMatcher(style_id, numbering)


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", ["style_id", "numbering"])
ParagraphMatcher.element_type = "paragraph"


def run(style_id=None):
    return RunMatcher(style_id)


RunMatcher = collections.namedtuple("RunMatcher", ["style_id"])
RunMatcher.element_type = "run"
