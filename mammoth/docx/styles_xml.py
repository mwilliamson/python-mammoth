import collections


class Styles(object):
    def __init__(self, paragraph_styles):
        self._paragraph_styles = paragraph_styles
    
    def find_paragraph_style_by_id(self, style_id):
        return self._paragraph_styles.get(style_id)


def read_styles_xml_element(element):
    paragraph_styles = {}
    
    for style_element in element.find_children("w:style"):
        style = _read_style_element(style_element)
        paragraph_styles[style.style_id] = style
    
    return Styles(paragraph_styles)


def _read_style_element(element):
    style_id = element.attributes["w:styleId"]
    return Style(style_id=style_id)


Style = collections.namedtuple("Style", "style_id")
