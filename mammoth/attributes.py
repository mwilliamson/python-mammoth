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
        class_name = str(style_id)
        try:
            int(class_name)
            # Must be the conditional style id
            attributes['class'] = f"c{class_name}"
        except:
            attributes['class'] = class_name

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
        compose_style_category(formatting, 'table_style'),
        compose_style_category(formatting, 'table_row_style'),
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
