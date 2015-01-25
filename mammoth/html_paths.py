import collections


def path(elements):
    return HtmlPath(elements)


def element(names, class_names=None, fresh=None):
    if class_names is None:
        class_names = []
    if fresh is None:
        fresh = False
    return HtmlPathElement(names, class_names, fresh)


HtmlPath = collections.namedtuple("HtmlPath", ["elements"])
HtmlPathElement = collections.namedtuple("HtmlPathElement", ["names", "class_names", "fresh"])

empty = path([])
