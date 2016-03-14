from ..lists import flat_map
from .nodes import TextNode, Element, SelfClosingElement, ForceWrite, NodeVisitor


def text(value):
    return TextNode(value)


def element(tag_names, attributes=None, children=None, collapsible=False):
    if not isinstance(tag_names, list):
        tag_names = [tag_names]
    if attributes is None:
        attributes = {}
    if children is None:
        children = []
    return Element(tag_names, attributes, children, collapsible=collapsible)


def collapsible_element(tag_names, attributes=None, children=None):
    return element(tag_names, attributes, children, collapsible=True)
    

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


def collapse(nodes):
    collapsed = []
    
    for node in nodes:
        _collapsing_add(collapsed, node)
    
    return collapsed

class _CollapseNode(NodeVisitor):
    def visit_text_node(self, node):
        return node
    
    def visit_element(self, element):
        return Element(
            element.tag_names,
            element.attributes,
            collapse(element.children),
            collapsible=element.collapsible)
    
    def visit_self_closing_element(self, element):
        return element
    
    def visit_force_write(self, node):
        return node
    
_collapse_node = _CollapseNode().visit


def _collapsing_add(collapsed, node):
    collapsed_node = _collapse_node(node)
    if not _try_collapse(collapsed, collapsed_node):
        collapsed.append(collapsed_node)
    
def _try_collapse(collapsed, node):
    if not collapsed:
        return False

    last = collapsed[-1]
    if not isinstance(last, Element) or not isinstance(node, Element):
        return False
    
    if not node.collapsible:
        return False
        
    if not _is_match(last, node):
        return False
    
    for child in node.children:
        _collapsing_add(last.children, child)
    return True

def _is_match(first, second):
    return first.tag_name in second.tag_names and first.attributes == second.attributes


def write(writer, nodes):
    visitor = _NodeWriter(writer)
    visitor.visit_all(nodes)
        

class _NodeWriter(NodeVisitor):
    def __init__(self, writer):
        self._writer = writer
    
    def visit_text_node(self, node):
        self._writer.text(node.value)
    
    def visit_element(self, element):
        self._writer.start(element.tag_name, element.attributes)
        self.visit_all(element.children)
        self._writer.end(element.tag_name)
    
    def visit_self_closing_element(self, element):
        self._writer.self_closing(element.tag_name, element.attributes)
    
    def visit_force_write(self, element):
        pass
    
    def visit_all(self, nodes):
        for node in nodes:
            self.visit(node)
