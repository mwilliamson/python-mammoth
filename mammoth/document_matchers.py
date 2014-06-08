import collections


def paragraph(style_id=None, style_name=None, numbering=None):
    return ParagraphMatcher(style_id, style_name, numbering)


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", ["style_id", "style_name", "numbering"])
ParagraphMatcher.element_type = "paragraph"


def run(style_id=None, style_name=None):
    return RunMatcher(style_id, style_name)


RunMatcher = collections.namedtuple("RunMatcher", ["style_id", "style_name"])
RunMatcher.element_type = "run"
