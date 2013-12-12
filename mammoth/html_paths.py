import collections


def path(elements):
    return HtmlPath(elements)


def element(name):
    return HtmlPathElement(name)


HtmlPath = collections.namedtuple("HtmlPath", ["elements"])
HtmlPathElement = collections.namedtuple("HtmlPathElement", ["name"])
