import collections


def path(elements):
    return HtmlPath(elements)


def element(names):
    return HtmlPathElement(names)


HtmlPath = collections.namedtuple("HtmlPath", ["elements"])
HtmlPathElement = collections.namedtuple("HtmlPathElement", ["names"])
