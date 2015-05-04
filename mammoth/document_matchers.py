import collections


DocumentMatcher = collections.namedtuple("DocumentMatcher", [
    #:field str
    "element_type",
    #:field str | none
    "style_id",
    #:field str | none
    "style_name",
    #:field str | none
    "numbering",
])


#:: ?style_id: str, ?style_name: str, ?numbering: str -> DocumentMatcher
def paragraph(style_id=None, style_name=None, numbering=None):
    return DocumentMatcher("paragraph", style_id, style_name, numbering)


#:: ?style_id: str, ?style_name: str -> DocumentMatcher
def run(style_id=None, style_name=None):
    return DocumentMatcher("run", style_id, style_name, None)
