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
    
    def wrap(self, generate_nodes, extra_attributes={}):
        nodes = generate_nodes()
   
        for element in reversed(self.elements):
            nodes = element.wrap_nodes(nodes, extra_attributes)
        
        return nodes


@cobble.data
class HtmlPathElement(object):
    tag = cobble.field()

    def wrap(self, generate_nodes, extra_attributes={}):
        return self.wrap_nodes(generate_nodes(), extra_attributes)

    def wrap_nodes(self, nodes, extra_attributes={}):
        element_tag = self.tag.clone() ## don't re-use tag from path, so we can set atttributes
        attrs = extra_attributes.get(id(self))
        if attrs is not None:
            element_tag.attributes.update(attrs)

        element = html.Element(element_tag, nodes)
      
        return [element]

empty = path([])


class ignore(object):
    @staticmethod
    def wrap(generate_nodes):
        return []
