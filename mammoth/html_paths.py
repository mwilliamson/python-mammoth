import cobble

from . import html


def path(elements):
    return HtmlPath(elements)


def element(names, class_names=None, fresh=None):
    if class_names is None:
        class_names = []
    if fresh is None:
        fresh = False
    return HtmlPathElement(names, class_names, fresh)


@cobble.data
class HtmlPath(object):
    elements = cobble.field()
    
    def wrap(self, nodes):
        for element in reversed(self.elements):
            nodes = element.wrap(nodes)
        
        return nodes

@cobble.data
class HtmlPathElement(object):
    names = cobble.field()
    class_names = cobble.field()
    fresh = cobble.field()

    def wrap(self, nodes):
        if self.class_names:
            attributes = {"class": " ".join(self.class_names)}
        else:
            attributes = {}
        element = html.element(
            self.names,
            attributes,
            nodes,
            collapsible=not self.fresh)
        return [element]

empty = path([])
