import collections


HtmlPathElement = collections.namedtuple("HtmlPathElement", [
    #:field list[str]
    "names",
    #:field list[str]
    "class_names",
    #:field bool
    "fresh"
])


HtmlPath = collections.namedtuple("HtmlPath", [
    #:field list[HtmlPathElement]
    "elements"
])


#:: list[HtmlPathElement] -> HtmlPath
def path(elements):
    return HtmlPath(elements)

#:: list[str], ?class_names: list[str], ?fresh: bool -> HtmlPathElement
def element(names, class_names=None, fresh=None):
    if class_names is None:
        #:: list[str]
        class_names = []
    if fresh is None:
        fresh = False
    return HtmlPathElement(names, class_names, fresh)

empty = path([])
