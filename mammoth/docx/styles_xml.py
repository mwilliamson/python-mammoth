import collections


class Styles(object):
    @staticmethod
    def create(paragraph_styles=None, character_styles=None, table_styles=None, numbering_styles=None):
        if paragraph_styles is None:
            paragraph_styles = {}
        if character_styles is None:
            character_styles = {}
        if table_styles is None:
            table_styles = {}
        if numbering_styles is None:
            numbering_styles = {}

        return Styles(
            paragraph_styles=paragraph_styles,
            character_styles=character_styles,
            table_styles=table_styles,
            numbering_styles=numbering_styles,
        )

    def __init__(self, paragraph_styles, character_styles, table_styles, numbering_styles):
        self._paragraph_styles = paragraph_styles
        self._character_styles = character_styles
        self._table_styles = table_styles
        self._numbering_styles = numbering_styles

    def find_paragraph_style_by_id(self, style_id):
        return self._paragraph_styles.get(style_id)

    def find_character_style_by_id(self, style_id):
        return self._character_styles.get(style_id)

    def find_table_style_by_id(self, style_id):
        return self._table_styles.get(style_id)

    def find_numbering_style_by_id(self, style_id):
        return self._numbering_styles.get(style_id)


Styles.EMPTY = Styles(
    paragraph_styles={},
    character_styles={},
    table_styles={},
    numbering_styles={},
)


def read_styles_xml_element(element):
    paragraph_styles = {}
    character_styles = {}
    table_styles = {}
    numbering_styles = {}
    styles = {
        "paragraph": paragraph_styles,
        "character": character_styles,
        "table": table_styles,
    }

    for style_element in element.find_children("w:style"):
        style = _read_style_element(style_element)
        element_type = style_element.attributes["w:type"]
        if element_type == "numbering":
            numbering_styles[style.style_id] = _read_numbering_style_element(style_element)
        else:
            style_set = styles.get(element_type)
            if style_set is not None:
                style_set[style.style_id] = style

    return Styles(
        paragraph_styles=paragraph_styles,
        character_styles=character_styles,
        table_styles=table_styles,
        numbering_styles=numbering_styles,
    )


Style = collections.namedtuple("Style", ["style_id", "name"])


def _read_style_element(element):
    style_id = element.attributes["w:styleId"]
    name = element.find_child_or_null("w:name").attributes.get("w:val")
    return Style(style_id=style_id, name=name)


NumberingStyle = collections.namedtuple("NumberingStyle", ["num_id"])


def _read_numbering_style_element(element):
    num_id = element \
        .find_child_or_null("w:pPr") \
        .find_child_or_null("w:numPr") \
        .find_child_or_null("w:numId") \
        .attributes.get("w:val")

    return NumberingStyle(num_id=num_id)
