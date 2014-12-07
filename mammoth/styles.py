import collections

from .document_matchers import DocumentMatcher
from .html_paths import HtmlPath


Style = collections.namedtuple("Style", [
    #:: DocumentMatcher
    "document_matcher",
    #:: HtmlPath
    "html_path",
])


#:: DocumentMatcher, HtmlPath -> Style
def style(document_matcher, html_path):
    return Style(document_matcher, html_path)
