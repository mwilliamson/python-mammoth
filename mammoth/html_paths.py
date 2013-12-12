import collections


def path(elements):
    return HtmlPath(elements)


def element(names, class_names=None):
    if class_names is None:
        class_names = []
    return HtmlPathElement(names, class_names)


HtmlPath = collections.namedtuple("HtmlPath", ["elements"])
HtmlPathElement = collections.namedtuple("HtmlPathElement", ["names", "class_names"])
