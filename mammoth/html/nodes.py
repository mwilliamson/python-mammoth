import cobble


class Node(object):
    pass


@cobble.data
class TextNode(Node):
    value = cobble.field()


@cobble.data
class Element(Node):
    tag_names = cobble.field()
    attributes = cobble.field()
    children = cobble.field()
    collapsible = cobble.field()


@cobble.data
class SelfClosingElement(Node):
    tag_name = cobble.field()
    attributes = cobble.field()


@cobble.visitable
class ForceWrite(Node):
    pass


NodeVisitor = cobble.visitor(Node)
