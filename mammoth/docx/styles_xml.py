import collections


class Styles(object):
    def __init__(self, paragraph_styles, character_styles):
        self._paragraph_styles = paragraph_styles
        self._character_styles = character_styles
    
    def find_paragraph_style_by_id(self, style_id):
        return self._paragraph_styles.get(style_id)
    
    def find_character_style_by_id(self, style_id):
        return self._character_styles.get(style_id)


def read_styles_xml_element(element):
    paragraph_styles = {}
    character_styles = {}
    styles = {
        "paragraph": paragraph_styles,
        "character": character_styles,
    }
    
    for style_element in element.find_children("w:style"):
        style = _read_style_element(style_element)
        styles[style.element_type][style.style_id] = style
    
    return Styles(paragraph_styles, character_styles)


def _read_style_element(element):
    element_type = element.attributes["w:type"]
    style_id = element.attributes["w:styleId"]
    name = element.find_child("w:name").attributes["w:val"]
    return Style(element_type=element_type, style_id=style_id, name=name)


Style = collections.namedtuple("Style", ["element_type", "style_id", "name"])
