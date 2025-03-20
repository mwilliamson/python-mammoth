import copy

from .html import MS_SHAPES, MS_BORDER_STYLES
from .documents import Element as WordElement


def compose_attributes(element, initial_attributes={}):
    attributes = copy.deepcopy(initial_attributes)
    formatting = getattr(element, 'formatting', {})

    if not isinstance(element, WordElement):
        return attributes

    style_id = getattr(element, 'style_id', None)
    if not style_id is None:
        attributes['class'] = str(style_id)

    checked = getattr(element, 'checked', False)
    if checked:
        attributes["checked"] = "checked"

    target_frame = getattr(element, 'target_frame', None)
    if target_frame is not None:
        attributes["target"] = target_frame

    colspan = formatting.get('colspan', 1)
    if colspan != 1:
        attributes["colspan"] = str(colspan)

    rowspan = formatting.get('rowspan', 1)
    if rowspan != 1:
        attributes["rowspan"] = str(rowspan)

    alt_text = getattr(element, 'alt_text', None)
    if alt_text is not None:
        attributes["alt"] = str(alt_text)

    shape = getattr(element, 'shape', None)
    if shape is not None:
        attributes.update(shape)
        style = attributes.get('style', '')
        attributes['style'] = style + f"{MS_SHAPES.get(shape.get('_ms_shape', ''), '')}"

    return attributes


def compose_style(formatting):
    css = [
        compose_style_category(formatting, 'cell_style'),
        compose_style_category(formatting, 'border_style'),
        compose_style_category(formatting, 'text_style')
    ]
    css = ''.join(css)
    return {'style': css} if len(css) else {}


def compose_style_category(formatting, category=''):
    css = ''

    for k, v in formatting.get(category, {}).items():
        css += f"{k}:{v};"

    return css


def compose_text_style(formatting):
    css = ""
    text_formatting = formatting.get('text', {})

    highlight = text_formatting.get('highlight', None)
    if highlight is not None:
        css += f"background-color:{highlight};"

    font = text_formatting.get('font', None)
    if font is not None:
        css += f"font-family:{font};"

    font_size = text_formatting.get('font_size', None)
    if font_size is not None:
        css += f"font-size:{font_size}pt;"

    font_color = text_formatting.get('font_color', None)
    if font_color is not None:
        css += f"color:#{font_color};"

    vertical_alignment = text_formatting.get('vertical_alignment', None)
    if vertical_alignment is not None:
        if vertical_alignment == "superscript":
            css += f"vertical-align:super;"
        elif vertical_alignment == "subscript":
            css += f"vertical-align:sub;"
        else:
            css += f"vertical-align:baseline;"

    if text_formatting.get('is_small_caps', False):
        css += f"font-variant: common-ligatures small-caps;"

    if text_formatting.get('is_all_caps', False):
        css += f"text-transform: uppercase;"

    if text_formatting.get('is_strikethrough', False):
        css += f"text-decoration: line-through;"

    if text_formatting.get('is_underline', False):
        css += f"text-decoration: underline;"

    if text_formatting.get('is_italic', False):
        css += f"font-style: italic;"

    if text_formatting.get('is_bold', False):
        css += f"font-weight: bold;"

    return css
