import xml.dom.minidom

import cobble

from mammoth.debug import is_debug_mode


@cobble.data
class XmlElement(object):
    name = cobble.field()
    attributes = cobble.field()
    children = cobble.field()
    parent = cobble.field()

    def find_child_or_null(self, name):
        return self.find_child(name) or null_xml_element

    def find_child(self, name):
        for child in self.children:
            if isinstance(child, XmlElement) and child.name == name:
                return child


    def find_children(self, name):
        return XmlElementList(filter(
            lambda child: child.node_type == node_types.element and child.name == name,
            self.children
        ))

    def find_parent(self):
        return self.parent


class XmlElementList(object):
    def __init__(self, elements):
        self._elements = elements

    def __iter__(self):
        return iter(self._elements)

    def find_children(self, name):
        children = []
        for element in self._elements:
            for child in element.find_children(name):
                children.append(child)
        return XmlElementList(children)


class NullXmlElement(object):
    name = 'NULL'
    attributes = {}
    children = []

    def find_child_or_null(self, name):
        return self

    def find_child(self, name):
        return None

    def find_children(self, name):
        return []

    def find_parent(self):
        return self


null_xml_element = NullXmlElement()


@cobble.data
class XmlText(object):
    value = cobble.field()
    children = []
    parent = cobble.field()


def element(name, attributes=None, children=None, parent=None):
    return XmlElement(name, attributes or {}, children or [], parent)

text = XmlText


class node_types(object):
    element = 1
    text = 3


XmlElement.node_type = node_types.element
XmlText.node_type = node_types.text



def parse_xml(fileobj, namespace_mapping=None):
    if namespace_mapping is None:
        namespace_prefixes = {}
    else:
        namespace_prefixes = dict((uri, prefix) for prefix, uri in namespace_mapping)

    document = xml.dom.minidom.parse(fileobj)

    def convert_node(node, parent=NullXmlElement()):
        if node.nodeType == xml.dom.Node.ELEMENT_NODE:
            return XmlElement(name=convert_name(node),
                              attributes=convert_attributes(node),
                              children=convert_children(node),
                              parent=parent)
        elif node.nodeType == xml.dom.Node.TEXT_NODE:
            return XmlText(value=node.nodeValue,
                           parent=parent)
        else:
            return None

    def convert_attributes(element):
        if not element.attributes is None:
            return dict(
                (convert_name(attribute), attribute.value)
                for attribute in element.attributes.values()
                if attribute.namespaceURI != "http://www.w3.org/2000/xmlns/"
            )
        else:
            return {}

    def convert_children(element):
        converted_children = []
        for child_node in element.childNodes:
            converted_child_node = convert_node(child_node)
            if converted_child_node is not None:
                converted_children.append(converted_child_node)
        return converted_children

    def convert_name(node):
        if node.namespaceURI is None:
            return node.localName
        else:
            prefix = namespace_prefixes.get(node.namespaceURI)
            if prefix is None:
                return "{%s}%s" % (node.namespaceURI, node.localName)
            else:
                return "%s:%s" % (prefix, node.localName)

    def add_parent_node(nodes, parent=NullXmlElement()):
        if isinstance(nodes, list):
            for node in nodes:
                node.parent = parent
                add_parent_node(node.children, node)
        else:
            nodes.parent = parent
            add_parent_node(nodes.children, nodes)
        return nodes

    doc_tree = convert_node(document.documentElement)
    return add_parent_node(doc_tree)
