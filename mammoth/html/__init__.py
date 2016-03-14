from ..lists import flat_map
from .nodes import TextNode, Element, SelfClosingElement, ForceWrite, NodeVisitor


def text(value):
    return TextNode(value)


def element(tag_name, attributes=None, children=None):
    if attributes is None:
        attributes = {}
    if children is None:
        children = []
    
    return Element([tag_name], attributes, children, collapsible=False)


def self_closing_element(tag_name, attributes=None):
    if attributes is None:
        attributes = {}
    
    return SelfClosingElement(tag_name, attributes)


force_write = ForceWrite()


def strip_empty(nodes):
    return flat_map(_strip_empty_node, nodes)


def _strip_empty_node(node):
    return StripEmpty().visit(node)


class StripEmpty(NodeVisitor):
    def visit_text_node(self, node):
        if node.value:
            return [node]
        else:
            return []
    
    def visit_element(self, element):
        children = strip_empty(element.children)
        if len(children) == 0:
            return []
        else:
            return [Element(
                element.tag_names,
                element.attributes,
                children,
                collapsible=element.collapsible)]
    
    def visit_self_closing_element(self, element):
        return [element]
    
    def visit_force_write(self, node):
        return [node]
