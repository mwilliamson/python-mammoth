import collections

from .documents import NumberingLevel


ParagraphMatcher = collections.namedtuple("ParagraphMatcher", [
    #:: str
    "element_type",
    #:: str | none
    "style_id",
    #:: str | none
    "style_name",
    #:: NumberingLevel | none
    "numbering"
])


#:: ?style_id: str | none, ?style_name: str | none, ?numbering: NumberingLevel | none -> ParagraphMatcher
def paragraph(style_id=None, style_name=None, numbering=None):
    return ParagraphMatcher("paragraph", style_id, style_name, numbering)


RunMatcher = collections.namedtuple("RunMatcher", [
    #:: str
    "element_type",
    #:: str | none
    "style_id",
    #:: str | none
    "style_name"
])


#:: ?style_id: str | none, ?style_name: str | none -> RunMatcher
def run(style_id=None, style_name=None):
    return RunMatcher("run", style_id, style_name)
