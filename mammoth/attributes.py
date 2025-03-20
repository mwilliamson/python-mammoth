import copy

from .html import MS_SHAPES
from .documents import Element as WordElement


def compose_attributes(element, initial_attributes={}):
    attributes = copy.deepcopy(initial_attributes)

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

    colspan = getattr(element, 'colspan', 1)
    if colspan != 1:
        attributes["colspan"] = str(colspan)

    rowspan = getattr(element, 'rowspan', 1)
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


def compose_border_style(formatting):
    ...
