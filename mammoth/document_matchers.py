import collections


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", [
    #:: str
    "element_type",
    #:: str | none
    "style_id",
    #:: str | none
    "style_name",
    "numbering"
])


def paragraph(style_id=None, style_name=None, numbering=None):
    return ParagraphMatcher("paragraph", style_id, style_name, numbering)


RunMatcher = collections.namedtuple("RunMatcher", [
    "element_type",
    "style_id",
    "style_name"
])


def run(style_id=None, style_name=None):
    return RunMatcher("run", style_id, style_name)
