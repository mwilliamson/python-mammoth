import collections
import xml.sax


XmlElement = collections.namedtuple("XmlElement", ["name", "attributes", "children"])
XmlText = collections.namedtuple("XmlText", ["value"])


element = XmlElement
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
    
    handler = Handler(namespace_prefixes)
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.setContentHandler(handler)
    parser.parse(fileobj)
    return handler.root()


class Handler(xml.sax.handler.ContentHandler):
    def __init__(self, namespace_prefixes):
        self._namespace_prefixes = namespace_prefixes
        self._element_stack = [RootElement()]
        self._character_buffer = []
    
    def root(self):
        return self._element_stack[0].children[0]
    
    def startElementNS(self, name, qname, attrs):
        self._flush_character_buffer()
        attributes = dict((self._read_name(key), value) for key, value in attrs.items())
        element = XmlElement(self._read_name(name), attributes, [])
        self._element_stack[-1].children.append(element)
        self._element_stack.append(element)
    
    def endElementNS(self, name, qname):
        self._flush_character_buffer()
        self._element_stack.pop()
        
    def characters(self, content):
        self._character_buffer.append(content)

    def _flush_character_buffer(self):
        if self._character_buffer:
            text = "".join(self._character_buffer)
            self._element_stack[-1].children.append(XmlText(text))
            self._character_buffer = []
            
    def _read_name(self, name):
        uri, local_name = name
        if uri is None:
            return local_name
        else:
            prefix = self._namespace_prefixes.get(uri)
            if prefix is None:
                return "{%s}%s" % (uri, local_name)
            else:
                return "%s:%s" % (prefix, local_name)

class RootElement(object):
    def __init__(self):
        self.children = []
