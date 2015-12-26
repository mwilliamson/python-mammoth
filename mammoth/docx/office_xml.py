from ..lists import flat_map
from .xmlparser import parse_xml, XmlElement


_namespaces = [
    ("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main"),
    ("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
    ("a", "http://schemas.openxmlformats.org/drawingml/2006/main"),
    ("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture"),
    ("content-types", "http://schemas.openxmlformats.org/package/2006/content-types"),
    ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships"),
    ("relationships", "http://schemas.openxmlformats.org/package/2006/relationships"),
    ("v", "urn:schemas-microsoft-com:vml"),
    ("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006"),
    ("office-word", "urn:schemas-microsoft-com:office:word"),
]


def read(fileobj):
    return _collapse_alternate_content(parse_xml(fileobj, _namespaces))[0]
    

def _collapse_alternate_content(node):
    if isinstance(node, XmlElement):
        if node.name == "mc:AlternateContent":
            return node.find_child("mc:Fallback").children
        else:
            node.children = flat_map(_collapse_alternate_content, node.children)
            return [node]
    else:
        return [node]
