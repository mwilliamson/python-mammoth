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
        element_type = style_element.attributes["w:type"]
        style_set = styles.get(element_type)
        if style_set is not None:
            style_set[style.style_id] = style
    
    return Styles(paragraph_styles, character_styles)


def _read_style_element(element):
    style_id = element.attributes["w:styleId"]
    name = element.find_child_or_null("w:name").attributes.get("w:val")
    return Style(style_id=style_id, name=name)


Style = collections.namedtuple("Style", ["style_id", "name"])
