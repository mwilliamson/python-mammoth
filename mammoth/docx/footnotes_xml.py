#~ from .. import documents
#~ from .. import results
from .. import lists
#~ from .xmlparser import node_types
#~ 

def read_footnotes_xml_element(element):
    return lists.map(
        _read_footnote_element,
        element.find_children("w:footnote"),
    )
        

def _read_footnote_element(element):
    return FootnoteElement(element.attributes["w:id"], element.children)


class FootnoteElement(object):
    def __init__(self, id, body):
        self.id = id
        self.body = body
