import cobble

from . import html


def path(elements):
    return HtmlPath(elements)


def element(names, class_names=None, fresh=None, separator=None):
    if class_names is None:
        class_names = []
    if fresh is None:
        fresh = False
    if class_names:
        attributes = {"class": " ".join(class_names)}
    else:
        attributes = {}
    return HtmlPathElement(html.tag(
        tag_names=names,
        attributes=attributes,
        collapsible=not fresh,
        separator=separator,
    ))


@cobble.data
class HtmlPath(object):
    elements = cobble.field()
    
    def wrap(self, generate_nodes, ol_element_attrs=None):
        nodes = generate_nodes()
   
        for element in reversed(self.elements):
            if element.tag.tag_name == "ol" and ol_element_attrs is not None:         
                nodes = element.wrap_nodes(nodes, ol_element_attrs)
                ol_element_attrs = None  # apply 'start' attr to deepest <ol>
            else:
                nodes = element.wrap_nodes(nodes)
        
        return nodes


@cobble.data
class HtmlPathElement(object):
    tag = cobble.field()

    def wrap(self, generate_nodes):
        return self.wrap_nodes(generate_nodes())

    def wrap_nodes(self, nodes, attrs={}):
        element = html.Element(self.tag, nodes)
        element.tag.update_attributes( attrs )
        return [element]

empty = path([])


class ignore(object):
    @staticmethod
    def wrap(generate_nodes):
        return []
