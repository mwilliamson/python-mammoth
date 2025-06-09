import re
import json
import copy
import os.path

from .debug import is_debug_mode, print_and_pause
from .html import MS_SHAPES, MS_BORDER_STYLES
from .documents import Element as WordElement

STYLES = {
    'root': {
      'ms-h1-color': '#2F5496',
      'ms-h2-color': '#2F5496',
      'ms-h3-color': '#1F3763',
      'ms-h4-color': '#2F5496',
      'ms-link-color': '#0563C1',
      'ms-visited-link-color': '#954F72',
      'ms-table-banding-gray': '#F2F2F2',
    }
}


class CSSStore(dict):
    CSS_VAR_RULE = "var\\(.*?\\)"
    CSS_VAR_CONTENTS_RULE = "--.*?"

    VAR_REGEX = re.compile(CSS_VAR_RULE, re.DOTALL)
    VAR_CONTENTS_REGEX = re.compile(CSS_VAR_CONTENTS_RULE, re.DOTALL)

    def __init__(self, css_file=None):
        super().__init__()

        if css_file is not None and os.path.exists(css_file):
            with open(css_file, 'rt') as fp:
                css = json.load(fp)
                self.update(css)
        #print(self)
        #input()

    def _find_class_rules(self, class_name):
        try:
            # If the class name is a number
            int(class_name)
            class_name = f".c{class_name}"
        except:
            class_name = f".{class_name}"
        return self.get(class_name, {})

    def _var(self, var):
        root_defs = self.get(':root', {})
        return root_defs.get(var, '')

    def _find_vars(self, css):
        return self.VAR_REGEX.findall(css)

    def _find_var_content(self, var_line):
        try:
            return self.VAR_CONTENTS_REGEX.match(var_line).group(0)
        except:
            return ''

    def _find_css_store(self, store_name):
        return self.get(store_name, {})

    def get_styles(self, element, parent_style_id=''):
        tags = element.tag.tag_names
        formatting = copy.deepcopy(element.formatting)
        style_id = element.style_id
        styles = [
            self._compose_style(formatting),
            self._get_tag_styles(tags),
            self._get_class_styles(style_id, parent_style_id)
        ]
        base_attributes = self._compose_attributes(element)

    def _get_class_styles(self, style_id, parent_style_id=''):
        store = self._find_css_store('styles')
        style_context = {}
        style_context.update(store.get(self._find_class_rules(style_id), {}))
        if len(parent_style_id):
            parent_store = store.get(self._find_class_rules(parent_style_id), {})
        else:
            parent_store = store.get(self._find_class_rules(style_id), {})
        [style_context.update({k:v}) for k,v in parent_store.items() if not isinstance(v, dict)]
        return style_context

    def _get_tag_styles(self, tags):
        store = self._find_css_store('styles')
        for tag in tags:
            tag_styles = store.get(tag, None)
            if tag_styles is not None:
                return tag_styles
        return {}

    @staticmethod
    def _compose_attributes(element, initial_attributes={}):
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

        if is_debug_mode():
            attributes = CSSStore._compose_conditional_styles(attributes, formatting)

        return attributes

    @staticmethod
    def _compose_conditional_styles(attributes, formatting):
        conditional_formatting = formatting.get('conditional_style', {})

        if not ('style' in attributes and len(attributes['style'])):
            attributes['style'] = ''

        oddHBand = conditional_formatting.get('oddHBand', 0)
        oddVBand = conditional_formatting.get('oddVBand', 0)
        evenHBand = conditional_formatting.get('evenHBand', 0)
        evenVBand = conditional_formatting.get('evenVBand', 0)

        oddHBand = int(oddHBand) if oddHBand is not None else 0
        oddVBand = int(oddVBand) if oddVBand is not None else 0
        evenHBand = int(evenHBand) if evenHBand is not None else 0
        evenVBand = int(evenVBand) if evenVBand is not None else 0

        if oddHBand or oddVBand or evenHBand or evenVBand:
            attributes['style'] += f'background-color:{STYLES["root"]["ms-table-banding-gray"]};'

        if is_debug_mode():
            firstRow = conditional_formatting.get('firstRow', 0)
            firstRow = int(firstRow) if firstRow is not None else 0

            if firstRow:
                attributes['style'] += 'text-transform:uppercase;font-weight:bold;border-bottom:thin solid;'

            firstColumn = conditional_formatting.get('firstColumn', 0)
            firstColumn = int(firstColumn) if firstColumn is not None else 0

            if firstColumn:
                attributes[
                    'style'] += 'text-transform:none;font-weight:bold;background-color:white !important;font-style:italic;'
        return attributes

    @staticmethod
    def _compose_style(formatting):
        return [
            CSSStore._compose_style_category(formatting, 'table_style'),
            CSSStore._compose_style_category(formatting, 'table_row_style'),
            CSSStore._compose_style_category(formatting, 'cell_style'),
            CSSStore._compose_style_category(formatting, 'border_style'),
            CSSStore._compose_style_category(formatting, 'text_style')
        ]

    @staticmethod
    def _compose_style_category(formatting, category=''):
        css = ''

        for k, v in formatting.get(category, {}).items():
            css += f"{k}:{v};"

        return css

    @staticmethod
    def _join_styles(styles):
        css = ''.join(styles)
        return {'style': css} if len(css) else {}


def compose_attributes(element, initial_attributes={}):
    attributes = copy.deepcopy(initial_attributes)
    formatting = getattr(element, 'formatting', {})
    attribute_formatting = formatting.get('attributes', {})

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

    colspan = attribute_formatting.get('colspan', 1)
    if colspan != 1:
        attributes["colspan"] = str(colspan)

    rowspan = attribute_formatting.get('rowspan', 1)
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

    if is_debug_mode():
        attributes = compose_conditional_styles(attributes, formatting)

    return attributes


def compose_conditional_styles(attributes, formatting):
    conditional_formatting = formatting.get('conditional_style', {})

    if not ('style' in attributes and len(attributes['style'])):
        attributes['style'] = ''

    oddHBand = conditional_formatting.get('oddHBand', 0)
    oddVBand = conditional_formatting.get('oddVBand', 0)
    evenHBand = conditional_formatting.get('evenHBand', 0)
    evenVBand = conditional_formatting.get('evenVBand', 0)

    oddHBand = int(oddHBand) if oddHBand is not None else 0
    oddVBand = int(oddVBand) if oddVBand is not None else 0
    evenHBand = int(evenHBand) if evenHBand is not None else 0
    evenVBand = int(evenVBand) if evenVBand is not None else 0

    if oddHBand or oddVBand or evenHBand or evenVBand:
        attributes['style'] += f'background-color:{STYLES["root"]["ms-table-banding-gray"]};'

    if is_debug_mode():
        firstRow = conditional_formatting.get('firstRow', 0)
        firstRow = int(firstRow) if firstRow is not None else 0

        if firstRow:
            attributes['style'] += 'text-transform:uppercase;font-weight:bold;border-bottom:thin solid;'

        firstColumn = conditional_formatting.get('firstColumn', 0)
        firstColumn = int(firstColumn) if firstColumn is not None else 0

        if firstColumn:
            attributes['style'] += 'text-transform:none;font-weight:bold;background-color:white !important;font-style:italic;'
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
