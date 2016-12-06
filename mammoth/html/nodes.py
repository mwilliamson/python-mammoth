import cobble


class Node(object):
    pass


@cobble.data
class TextNode(Node):
    value = cobble.field()


@cobble.data
class Tag(object):
    tag_names = cobble.field()
    attributes = cobble.field()
    collapsible = cobble.field()
    separator = cobble.field()
    
    @property
    def tag_name(self):
        return self.tag_names[0]


@cobble.data
class Element(Node):
    tag = cobble.field()
    children = cobble.field()
    
    @property
    def tag_name(self):
        return self.tag.tag_name
        
    @property
    def tag_names(self):
        return self.tag.tag_names

    @property
    def attributes(self):
        return self.tag.attributes
        
    @property
    def collapsible(self):
        return self.tag.collapsible
        
    @property
    def separator(self):
        return self.tag.separator


@cobble.data
class SelfClosingElement(Node):
    tag_name = cobble.field()
    attributes = cobble.field()


@cobble.visitable
class ForceWrite(Node):
    pass


NodeVisitor = cobble.visitor(Node)
