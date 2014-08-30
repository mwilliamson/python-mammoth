from .. import lists


def read_footnotes_xml_element(element):
    footnote_elements = lists.filter(
        _is_footnote_element,
        element.find_children("w:footnote"),
    )
    return lists.map(_read_footnote_element, footnote_elements)


def _is_footnote_element(element):
    return element.attributes.get("w:type") not in ["continuationSeparator", "separator"]


def _read_footnote_element(element):
    return FootnoteElement(element.attributes["w:id"], element.children)


class FootnoteElement(object):
    def __init__(self, id, body):
        self.id = id
        self.body = body
