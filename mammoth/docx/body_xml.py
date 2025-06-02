import contextlib
import copy
import re
import sys

from .. import documents
from .. import results
from .. import lists
from . import complex_fields, xmlparser
from .dingbats import dingbats
from .xmlparser import node_types, XmlElement, null_xml_element
from .styles_xml import Styles
from .uris import replace_fragment, uri_to_zip_entry_name
from ..debug import is_debug_mode, print_and_pause
from ..html import MS_BORDER_STYLES, MS_CELL_ALIGNMENT_STYLES
from ..word_formatting import WordFormatting

if sys.version_info >= (3,):
    unichr = chr

# Conversion units
EMU_TO_INCHES = 914400
EMU_TO_PIXELS = 9525
POINT_TO_PIXEL = (1 / 0.75)  # Per W3C
TWIP_TO_PIXELS = POINT_TO_PIXEL / 20 # 20 -> 1 inch; 72pt / in per PostScript -> 72 points
EIGHTPOINT_TO_PIXEL = POINT_TO_PIXEL / 8
FIFTHPERCENT_TO_PERCENT = 0.02


def reader(
        numbering=None,
        content_types=None,
        relationships=None,
        styles=None,
        docx_file=None,
        files=None
):
    if styles is None:
        styles = Styles.EMPTY

    read_all = _create_reader(
        numbering=numbering,
        content_types=content_types,
        relationships=relationships,
        styles=styles,
        docx_file=docx_file,
        files=files,
    )
    return _BodyReader(read_all)


class _BodyReader(object):
    def __init__(self, read_all):
        self._read_all = read_all

    def read_all(self, elements):
        result = self._read_all(elements)
        return results.Result(result.elements, result.messages)


def _create_reader(numbering, content_types, relationships, styles, docx_file, files):
    current_instr_text = []
    complex_field_stack = []

    if is_debug_mode():
        word_formatting = WordFormatting(styles._styles_node)

    # When a paragraph is marked as deleted, its contents should be combined
    # with the following paragraph. See 17.13.5.15 del (Deleted Paragraph) of
    # ECMA-376 4th edition Part 1.
    deleted_paragraph_contents = []

    _ignored_elements = set([
        "office-word:wrap",
        "v:shadow",
        "v:shapetype",
        "w:annotationRef",
        "w:bookmarkEnd",
        "w:sectPr",
        "w:proofErr",
        "w:lastRenderedPageBreak",
        "w:commentRangeStart",
        "w:commentRangeEnd",
        "w:del",
        "w:footnoteRef",
        "w:endnoteRef",
        "w:pPr",
        "w:rPr",
        "w:tblPr",
        "w:tblGrid",
        "w:trPr",
        "w:tcPr",
    ])

    def text(element):
        return _success(documents.Text(_inner_text(element)))

    def run(element):
        # At least in my test documents, this bit is useless if a run is inside a pPr.
        # Meaning, the rPr element will only appear inside a run if that run has special formatting.
        # If the run follows the parent's formatting, the rPr element will be in the parent's *Pr element.
        properties = element.find_child_or_null("w:rPr")
        props, formatting = _find_run_properties(properties)

        def add_complex_field_hyperlink(children):
            hyperlink_kwargs = current_hyperlink_kwargs()
            if hyperlink_kwargs is None:
                return children
            else:
                return [documents.hyperlink(children=children, **hyperlink_kwargs)]

        return _ReadResult.map_results(
            _read_run_style(properties),
            _read_xml_elements(element.children).map(add_complex_field_hyperlink),
            lambda style, children: documents.run(
                children=children,
                formatting=formatting,
                style_id=style[0],
                style_name=style[1],
                **props
            ))

    def _find_run_properties(properties):
        formatting = {}
        text_alignment = properties \
            .find_child_or_null("w:vertAlign") \
            .attributes.get("w:val")
        if text_alignment is not None:
            if text_alignment == "superscript":
                formatting['vertical-align'] = "super"
            elif text_alignment == "subscript":
                formatting['vertical-align'] = "sub"
            else:
                formatting['vertical-align'] = "baseline"

        font = properties.find_child_or_null("w:rFonts").attributes.get("w:ascii")
        if font is not None:
            formatting['font-family'] = font

        font_size_string = properties.find_child_or_null("w:sz").attributes.get("w:val")
        if _is_int(font_size_string):
            # w:sz gives the font size in half points, so halve the value to get the size in points
            font_size = int(font_size_string) / 2
        else:
            font_size = None
        if font_size is not None:
            formatting['font-size'] = f"{font_size}pt"

        font_color = properties.find_child_or_null("w:color").attributes.get("w:val")
        if font_color is not None and font_color != 'none':
            font_color = font_color
        else:
            font_color = '000000'
        if font_color is not None:
            formatting['color'] = f'#{font_color}'

        is_bold = read_boolean_element(properties.find_child("w:b"))
        if is_bold:
            formatting['font-weight'] = 'bold'
        is_italic = read_boolean_element(properties.find_child("w:i"))
        if is_italic:
            formatting['font-style'] = 'italic'
        is_underline = read_underline_element(properties.find_child("w:u"))
        if is_underline:
            formatting['text-decoration'] = 'underline'
        is_strikethrough = read_boolean_element(properties.find_child("w:strike"))
        if is_strikethrough:
            formatting['text-decoration'] = 'line-through'
        is_all_caps = read_boolean_element(properties.find_child("w:caps"))
        if is_all_caps:
            formatting['text-transform'] = 'uppercase'
        is_small_caps = read_boolean_element(properties.find_child("w:smallCaps"))
        if is_small_caps:
            formatting['font-variant'] = 'common-ligatures small-caps' if is_small_caps else 'normal'
        highlight = read_highlight_value(properties.find_child_or_null("w:highlight").attributes.get("w:val"))
        if highlight is not None:
            formatting['background-color'] = highlight
        is_deleted = properties.find_child("w:del")

        return ({
                    'vertical_alignment': text_alignment,
                    'font': font,
                    'font_size': font_size,
                    'font_color': font_color,
                    'is_bold': is_bold,
                    'is_italic': is_italic,
                    'is_underline': is_underline,
                    'is_strikethrough': is_strikethrough,
                    'is_all_caps': is_all_caps,
                    'is_small_caps': is_small_caps,
                    'highlight': highlight,
                    'is_deleted': is_deleted,
                },
                {'text_style': formatting}
        )

    def _read_run_style(properties):
        return _read_style(properties, "w:rStyle", "Run", styles.find_character_style_by_id)

    def read_boolean_element(element):
        if element is None:
            return False
        else:
            return read_boolean_attribute_value(element.attributes.get("w:val"))

    def read_boolean_attribute_value(value):
        return value not in ["false", "0"]

    def read_underline_element(element):
        return element and element.attributes.get("w:val") not in [None, "false", "0", "none"]

    def read_highlight_value(value):
        if not value or value == "none":
            return None
        else:
            return value

    def paragraph(element):
        properties = element.find_child_or_null("w:pPr")
        props, formatting = _find_paragraph_props(properties)

        if props['is_deleted'] is not None:
            for child in element.children:
                deleted_paragraph_contents.append(child)
            return _empty_result

        else:
            children_xml = element.children
            if deleted_paragraph_contents:
                children_xml = deleted_paragraph_contents + children_xml
                del deleted_paragraph_contents[:]

            return _ReadResult.map_results(
                _read_paragraph_style(properties),
                _read_xml_elements(children_xml),
                lambda style, children: documents.paragraph(
                    children=children,
                    style_id=style[0],
                    style_name=style[1],
                    numbering=_read_numbering_properties(
                        paragraph_style_id=style[0],
                        element=properties.find_child_or_null("w:numPr"),
                    ),
                    alignment=props['alignment'],
                    indent=props['indent'],
                    formatting=formatting
                )).append_extra()

    def _find_paragraph_props(properties):
        rpr = properties.find_child_or_null("w:rPr")
        props, formatting = _find_run_properties(rpr)

        alignment = properties.find_child_or_null("w:jc").attributes.get("w:val"),
        props['alignment'] = alignment
        if alignment is not None:
            formatting['text-justify'] = alignment

        indent = _read_paragraph_indent(properties.find_child_or_null("w:ind"))
        props['indent'] = indent

        formatting['conditional_style']: _find_conditional_style_props(properties)
        return props, formatting

    def _read_paragraph_style(properties):
        return _read_style(properties, "w:pStyle", "Paragraph", styles.find_paragraph_style_by_id)

    def current_hyperlink_kwargs():
        for complex_field in reversed(complex_field_stack):
            if isinstance(complex_field, complex_fields.Hyperlink):
                return complex_field.kwargs

        return None

    def read_fld_char(element):
        fld_char_type = element.attributes.get("w:fldCharType")
        if fld_char_type == "begin":
            complex_field_stack.append(complex_fields.begin(fld_char=element))
            del current_instr_text[:]

        elif fld_char_type == "end":
            complex_field = complex_field_stack.pop()
            if isinstance(complex_field, complex_fields.Begin):
                complex_field = parse_current_instr_text(complex_field)

            if isinstance(complex_field, complex_fields.Checkbox):
                return _success(documents.checkbox(checked=complex_field.checked))

        elif fld_char_type == "separate":
            complex_field_separate = complex_field_stack.pop()
            complex_field = parse_current_instr_text(complex_field_separate)
            complex_field_stack.append(complex_field)

        return _empty_result

    def parse_current_instr_text(complex_field):
        instr_text = "".join(current_instr_text)

        if isinstance(complex_field, complex_fields.Begin):
            fld_char = complex_field.fld_char
        else:
            fld_char = null_xml_element

        return parse_instr_text(instr_text, fld_char=fld_char)

    def parse_instr_text(instr_text, *, fld_char):
        external_link_result = re.match(r'\s*HYPERLINK "(.*)"', instr_text)
        if external_link_result is not None:
            return complex_fields.hyperlink(dict(href=external_link_result.group(1)))

        internal_link_result = re.match(r'\s*HYPERLINK\s+\\l\s+"(.*)"', instr_text)
        if internal_link_result is not None:
            return complex_fields.hyperlink(dict(anchor=internal_link_result.group(1)))

        checkbox_result = re.match(r'\s*FORMCHECKBOX\s*', instr_text)
        if checkbox_result is not None:
            checkbox_element = fld_char \
                .find_child_or_null("w:ffData") \
                .find_child_or_null("w:checkBox")
            checked_element = checkbox_element.find_child("w:checked")

            if checked_element is None:
                checked = read_boolean_element(checkbox_element.find_child("w:default"))
            else:
                checked = read_boolean_element(checked_element)

            return complex_fields.checkbox(checked=checked)

        return None

    def read_instr_text(element):
        current_instr_text.append(_inner_text(element))
        return _empty_result

    def _read_style(properties, style_tag_name, style_type, find_style_by_id):
        messages = []
        style_id = properties \
            .find_child_or_null(style_tag_name) \
            .attributes.get("w:val")

        if style_id is None:
            style_name = None
        else:
            style = find_style_by_id(style_id)
            if style is None:
                style_name = None
                messages.append(_undefined_style_warning(style_type, style_id))
            else:
                style_name = style.name

        return _ReadResult([style_id, style_name], [], messages)

    def _undefined_style_warning(style_type, style_id):
        return results.warning(
            "{0} style with ID {1} was referenced but not defined in the document".format(style_type, style_id))

    def _read_numbering_properties(paragraph_style_id, element):
        num_id = element.find_child_or_null("w:numId").attributes.get("w:val")
        level_index = element.find_child_or_null("w:ilvl").attributes.get("w:val")
        if num_id is not None and level_index is not None:
            return numbering.find_level(num_id, level_index)

        if paragraph_style_id is not None:
            level = numbering.find_level_by_paragraph_style_id(paragraph_style_id)
            if level is not None:
                return level

        return None

    def _read_paragraph_indent(element):
        attributes = element.attributes
        return documents.paragraph_indent(
            start=attributes.get("w:start") or attributes.get("w:left"),
            end=attributes.get("w:end") or attributes.get("w:right"),
            first_line=attributes.get("w:firstLine"),
            hanging=attributes.get("w:hanging"),
        )

    def tab(element):
        return _success(documents.tab())

    def no_break_hyphen(element):
        return _success(documents.text(unichr(0x2011)))

    def soft_hyphen(element):
        return _success(documents.text(u"\u00ad"))

    def symbol(element):
        # See 17.3.3.30 sym (Symbol Character) of ECMA-376 4th edition Part 1
        font = element.attributes.get("w:font")
        char = element.attributes.get("w:char")

        unicode_code_point = dingbats.get((font, int(char, 16)))

        if unicode_code_point is None and re.match("^F0..", char):
            unicode_code_point = dingbats.get((font, int(char[2:], 16)))

        if unicode_code_point is None:
            warning = results.warning(
                "A w:sym element with an unsupported character was ignored: char {0} in font {1}".format(
                    char,
                    font,
                ))
            return _empty_result_with_message(warning)
        else:
            return _success(documents.text(unichr(unicode_code_point)))

    def table(element):
        properties = element.find_child_or_null("w:tblPr")
        if is_debug_mode():
            formatting = word_formatting.get_element_base_formatting(element)
            formatting.update(_find_table_props(properties))
        else:
            formatting = _find_table_props(properties)
        return _ReadResult.map_results(
            read_table_style(properties),
            _read_xml_elements(element.children)
            .flat_map(calculate_row_spans),

            lambda style, children: documents.table(
                children=children,
                formatting=formatting,
                style_id=style[0],
                style_name=style[1],
            ),
        )

    def read_table_style(properties):
        return _read_style(properties, "w:tblStyle", "Table", styles.find_table_style_by_id)

    def _find_table_props(properties):
        """
        Check out `Table Properties <http://officeopenxml.com/WPtableProperties.php>`_.
        Check out `Table Width <http://officeopenxml.com/WPtableProperties.php>`_.
        Check out `Table Borders <http://officeopenxml.com/WPtableBorders.php>`_.
        """
        tblBorders = properties.find_child_or_null("w:tblBorders")
        tblW = properties.find_child_or_null("w:tblW")
        width = tblW.attributes.get('w:w')
        width_type = tblW.attributes.get('w:type')

        table_style = {}
        if width is not None:
            if width_type == 'dxa':
                table_style['width'] = f"{round(float(width) * TWIP_TO_PIXELS,1)}px"
            elif width_type == 'pct':
                table_style['width'] = f"{round(float(width) * FIFTHPERCENT_TO_PERCENT,1)}%"

        return {
            'table_style': table_style,
            'border_style': _find_border_style_props(tblBorders, {'border-collapse': 'collapse'})
        }

    def table_row(element):
        properties = element.find_child_or_null("w:trPr")
        is_header = bool(properties.find_child("w:tblHeader"))
        if is_debug_mode():
            formatting = word_formatting.get_conditional_formatting(element)
            formatting.update(_find_table_row_props(properties))
        else:
            formatting = _find_table_row_props(properties)
        return _ReadResult.map_results(
            read_table_conditional_style(properties),
            _read_xml_elements(element.children),
            lambda style, children: documents.table_row(
                children=children,
                is_header=is_header,
                formatting=formatting,
                style_id=style[0],
                style_name=style[1],
            )
        )

    def _find_table_row_props(properties):
        """
        Check out `Table Properties <http://officeopenxml.com/WPtableProperties.php>`_.
        Check out `Table Width <http://officeopenxml.com/WPtableProperties.php>`_.
        Check out `Table Borders <http://officeopenxml.com/WPtableBorders.php>`_.
        """
        trHeight = properties.find_child_or_null("w:trHeight")
        height = trHeight.attributes.get("w:val")

        table_row_style = {}
        if height is not None:
            table_row_style['height'] = f"{round(float(height) * TWIP_TO_PIXELS,1)}px"

        return {
            'conditional_style': _find_conditional_style_props(properties),
            'table_row_style': table_row_style
        }

    def read_table_conditional_style(properties):
        """
        The id in a conditional style is present in `w:val` and represents a bit mask?

        See `Conditional Table Style <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.conditionalformatstyle?view=openxml-3.0.1>`_
        for more details about how conditional styles work.

        """
        return _read_style(properties, "w:cnfStyle", "Table", styles.find_table_style_by_id)

    def table_cell(element):
        properties = element.find_child_or_null("w:tcPr")
        if is_debug_mode():
            formatting = word_formatting.get_conditional_formatting(element)
            formatting.update(_find_table_cell_props(properties))
        else:
            formatting = _find_table_cell_props(properties)

        return _ReadResult.map_results(
            read_table_conditional_style(properties),
            _read_xml_elements(element.children),
            lambda style, children: _add_attrs(
                documents.table_cell(
                    children=children,
                    formatting=formatting,
                    style_id=style[0],
                    style_name=style[1],
                ),
                _vmerge=read_vmerge(properties),
            ))

    def _find_table_cell_props(properties):
        """
        Check out `Table Cell Properties <http://officeopenxml.com/WPtableCellProperties.php>`_
        Check out `Table Grid <http://officeopenxml.com/WPtableGrid.php>`_
        """
        tcW = properties.find_child_or_null("w:tcW")
        gridspan = properties.find_child_or_null("w:gridSpan").attributes.get('w:val')
        vAlign = properties.find_child_or_null("w:vAlign").attributes.get("w:val")
        width = tcW.attributes.get("w:w")

        cell_style = {}
        if width is not None:
            cell_style['width'] = f"{round(float(width) * TWIP_TO_PIXELS,1)}px"
        if vAlign is not None:
            cell_style['vertical-align'] = MS_CELL_ALIGNMENT_STYLES[vAlign]

        return {
            'conditional_style': _find_conditional_style_props(properties),
            'cell_style': cell_style,
            'colspan': 1 if gridspan is None else int(gridspan),
            'rowspan': 1,
            'border_style': _find_border_style_props(properties),

        }

    def _find_border_style_props(properties, initial_formatting={}):
        """
        Check out `Table Cell Properties - Borders <http://officeopenxml.com/WPtableCellProperties-Borders.php>`_
        """
        tcBorders = properties.find_child_or_null("w:tcBorders")
        formatting = copy.deepcopy(initial_formatting)

        top = tcBorders.find_child_or_null("w:top")
        top_width = top.attributes.get('w:sz')
        top_space = top.attributes.get('w:space')
        top_style = top.attributes.get('w:val')
        top_border = MS_BORDER_STYLES.get(top_style, None)
        top_color = top.attributes.get('w:color')
        if top is not None:
            if top_border is not None:
                formatting['border-top-style'] = top_border
            if top_width is not None:
                formatting['border-top-width'] = round(float(top_width) * EIGHTPOINT_TO_PIXEL,1)
            if top_color is not None and top_color != 'auto':
                formatting['border-top-color'] = top_color

        bottom = tcBorders.find_child_or_null("w:bottom")
        bottom_width = bottom.attributes.get('w:sz')
        bottom_space = bottom.attributes.get('w:space')
        bottom_style = bottom.attributes.get('w:val')
        bottom_border = MS_BORDER_STYLES.get(bottom_style, None)
        bottom_color = bottom.attributes.get('w:color')
        if bottom is not None:
            if bottom_border is not None:
                formatting['border-bottom-style'] = bottom_border
            if bottom_width is not None:
                formatting['border-bottom-width'] = round(float(bottom_width) * EIGHTPOINT_TO_PIXEL,1)
            if bottom_color is not None and bottom_color != 'auto':
                formatting['border-bottom-color'] = bottom_color

        left = tcBorders.find_child_or_null("w:left")
        left_width = left.attributes.get('w:sz')
        left_space = left.attributes.get('w:space')
        left_style = left.attributes.get('w:val')
        left_border = MS_BORDER_STYLES.get(left_style, None)
        left_color = left.attributes.get('w:color')
        if left is not None:
            if left_border is not None:
                formatting['border-left-style'] = left_border
            if left_width is not None:
                formatting['border-left-width'] = round(float(left_width) * EIGHTPOINT_TO_PIXEL,1)
            if left_color is not None and left_color != 'auto':
                formatting['border-left-color'] = left_color

        right = tcBorders.find_child_or_null("w:right")
        right_width = right.attributes.get('w:sz')
        right_space = right.attributes.get('w:space')
        right_style = right.attributes.get('w:val')
        right_border = MS_BORDER_STYLES.get(right_style, None)
        right_color = right.attributes.get('w:color')
        if right is not None:
            if right_border is not None:
                formatting['border-right-style'] = right_border
            if right_width is not None:
                formatting['border-right-width'] = round(float(right_width) * EIGHTPOINT_TO_PIXEL,1)
            if right_color is not None and right_color != 'auto':
                formatting['border-right-color'] = right_color

        spacing = [
            float(top_space) if top_space is not None else -1,
            float(bottom_space) if bottom_space is not None else -1,
            float(left_space) if left_space is not None else -1,
            float(right_space) if right_space is not None else -1,
        ]
        max_spacing = max(spacing)
        if max_spacing > -1:
            formatting['border-spacing'] = round(max_spacing * POINT_TO_PIXEL,1)

        return formatting

    def _find_conditional_style_props(properties):
        cnfStyle = properties.find_child_or_null("w:cnfStyle")
        return {
            'firstRow': cnfStyle.attributes.get("w:firstRow"),
            'lastRow': cnfStyle.attributes.get("w:lastRow"),
            'firstColumn': cnfStyle.attributes.get("w:firstColumn"),
            'lastColumn': cnfStyle.attributes.get("w:lastColumn"),
            'oddVBand': cnfStyle.attributes.get("w:oddVBand"),
            'evenVBand': cnfStyle.attributes.get("w:evenVBand"),
            'oddHBand': cnfStyle.attributes.get("w:oddHBand"),
            'evenHBand': cnfStyle.attributes.get("w:evenHBand"),
            'firstRowFirstColumn': cnfStyle.attributes.get("w:firstRowFirstColumn"),
            'firstRowLastColumn': cnfStyle.attributes.get("w:firstRowLastColumn"),
            'lastRowFirstColumn': cnfStyle.attributes.get("w:lastRowFirstColumn"),
            'lastRowLastColumn': cnfStyle.attributes.get("w:lastRowLastColumn"),
        }

    def read_vmerge(properties):
        vmerge_element = properties.find_child("w:vMerge")
        if vmerge_element is None:
            return False
        else:
            val = vmerge_element.attributes.get("w:val")
            return val == "continue" or not val

    def calculate_row_spans(rows):
        unexpected_non_rows = any(
            not isinstance(row, documents.TableRow)
            for row in rows
        )
        if unexpected_non_rows:
            return _elements_result_with_messages(rows, [results.warning(
                "unexpected non-row element in table, cell merging may be incorrect"
            )])

        unexpected_non_cells = any(
            not isinstance(cell, documents.TableCell)
            for row in rows
            for cell in row.children
        )
        if unexpected_non_cells:
            return _elements_result_with_messages(rows, [results.warning(
                "unexpected non-cell element in table row, cell merging may be incorrect"
            )])

        columns = {}
        for row in rows:
            cell_index = 0
            for cell in row.children:
                if cell._vmerge and cell_index in columns:
                    columns[cell_index].formatting['rowspan'] += 1
                else:
                    columns[cell_index] = cell
                    cell._vmerge = False
                cell_index += cell.formatting['colspan']

        for row in rows:
            row.children = lists.filter(lambda cell: not cell._vmerge, row.children)
            for cell in row.children:
                del cell._vmerge

        return _success(rows)

    def read_child_elements(element):
        return _read_xml_elements(element.children)

    def pict(element):
        return read_child_elements(element).to_extra()

    def hyperlink(element):
        relationship_id = element.attributes.get("r:id")
        anchor = element.attributes.get("w:anchor")
        target_frame = element.attributes.get("w:tgtFrame") or None
        children_result = _read_xml_elements(element.children)

        def create(**kwargs):
            return children_result.map(lambda children: documents.hyperlink(
                children=children,
                target_frame=target_frame,
                **kwargs
            ))

        if relationship_id is not None:
            href = relationships.find_target_by_relationship_id(relationship_id)
            if anchor is not None:
                href = replace_fragment(href, anchor)

            return create(href=href)
        elif anchor is not None:
            return create(anchor=anchor)
        else:
            return children_result

    def bookmark_start(element):
        name = element.attributes.get("w:name")
        if name == "_GoBack":
            return _empty_result
        else:
            return _success(documents.bookmark(name))

    def break_(element):
        break_type = element.attributes.get("w:type")

        if not break_type or break_type == "textWrapping":
            return _success(documents.line_break)
        elif break_type == "page":
            return _success(documents.page_break)
        elif break_type == "column":
            return _success(documents.column_break)
        else:
            warning = results.warning("Unsupported break type: {0}".format(break_type))
            return _empty_result_with_message(warning)

    def inline(element):
        properties = element.find_child_or_null("wp:docPr").attributes
        if properties.get("descr", "").strip():
            alt_text = properties.get("descr")
        else:
            alt_text = properties.get("title")
        pic_element = element.find_children("a:graphic") \
            .find_children("a:graphicData") \
            .find_children("pic:pic")
        blips = pic_element.find_children("pic:blipFill") \
            .find_children("a:blip")
        shape_props_element = pic_element.find_children("pic:spPr")
        shape_props = _find_image_shapes(shape_props_element)
        return _read_blips(blips, alt_text, shape_props)

    def _read_blips(blips, alt_text, shape_props):
        return _ReadResult.concat(lists.map(lambda blip: _read_blip(blip, alt_text, shape_props), blips))

    def _read_blip(element, alt_text, shape_props):
        blip_image = _find_blip_image(element)

        if blip_image is None:
            warning = results.warning("Could not find image file for a:blip element")
            return _empty_result_with_message(warning)
        else:
            return _read_image(blip_image, alt_text, shape_props)

    def _read_image(image_file, alt_text, shape_props):
        image_path, open_image = image_file
        content_type = content_types.find_content_type(image_path)
        image = documents.image(alt_text=alt_text, content_type=content_type, open=open_image, shape=shape_props)

        if content_type in ["image/png", "image/gif", "image/jpeg", "image/svg+xml", "image/tiff"]:
            messages = []
        else:
            messages = [
                results.warning("Image of type {0} is unlikely to display in web browsers".format(content_type))]

        return _element_result_with_messages(image, messages)

    def _find_blip_image(element):
        embed_relationship_id = element.attributes.get("r:embed")
        link_relationship_id = element.attributes.get("r:link")
        if embed_relationship_id is not None:
            return _find_embedded_image(embed_relationship_id)
        elif link_relationship_id is not None:
            return _find_linked_image(link_relationship_id)
        else:
            return None

    def _find_image_shapes(props_element):
        return lists.map(lambda element: _find_image_shape(element), props_element)[-1]

    def _find_image_shape(element):
        location_element = element.find_child("a:xfrm") \
            .find_child("a:off")
        size_element = element.find_child("a:xfrm") \
            .find_child("a:ext")
        shape_element = element.find_child("a:prstGeom")
        return {
            "width": str(round(float(size_element.attributes.get("cx")) / EMU_TO_PIXELS,1)),
            "height": str(round(float(size_element.attributes.get("cy")) / EMU_TO_PIXELS,1)),
            "position": "relative",
            "left": str(round(float(location_element.attributes.get("x")),1)),
            "top": str(round(float(location_element.attributes.get("y")),1)),
            "_ms_shape": shape_element.attributes.get("prst")
        }

    def _find_embedded_image(relationship_id):
        target = relationships.find_target_by_relationship_id(relationship_id)
        image_path = uri_to_zip_entry_name("word", target)

        def open_image():
            image_file = docx_file.open(image_path)
            if hasattr(image_file, "__exit__"):
                return image_file
            else:
                return contextlib.closing(image_file)

        return image_path, open_image

    def _find_linked_image(relationship_id):
        image_path = relationships.find_target_by_relationship_id(relationship_id)

        def open_image():
            return files.open(image_path)

        return image_path, open_image

    def read_imagedata(element):
        relationship_id = element.attributes.get("r:id")
        if relationship_id is None:
            warning = results.warning("A v:imagedata element without a relationship ID was ignored")
            return _empty_result_with_message(warning)
        else:
            title = element.attributes.get("o:title")
            return _read_image(_find_embedded_image(relationship_id), title)

    def note_reference_reader(note_type):
        def note_reference(element):
            return _success(documents.note_reference(note_type, element.attributes["w:id"]))

        return note_reference

    def read_comment_reference(element):
        return _success(documents.comment_reference(element.attributes["w:id"]))

    def alternate_content(element):
        return read_child_elements(element.find_child("mc:Fallback"))

    def read_sdt(element):
        checkbox = element.find_child_or_null("w:sdtPr").find_child("wordml:checkbox")

        if checkbox is not None:
            checked_element = checkbox.find_child("wordml:checked")
            is_checked = (
                    checked_element is not None and
                    read_boolean_attribute_value(checked_element.attributes.get("wordml:val"))
            )
            return _success(documents.checkbox(checked=is_checked))
        else:
            return read_child_elements(element.find_child_or_null("w:sdtContent"))

    handlers = {
        "w:t": text,
        "w:r": run,
        "w:p": paragraph,
        "w:fldChar": read_fld_char,
        "w:instrText": read_instr_text,
        "w:tab": tab,
        "w:noBreakHyphen": no_break_hyphen,
        "w:softHyphen": soft_hyphen,
        "w:sym": symbol,
        "w:tbl": table,
        "w:tr": table_row,
        "w:tc": table_cell,
        "w:ins": read_child_elements,
        "w:object": read_child_elements,
        "w:smartTag": read_child_elements,
        "w:drawing": read_child_elements,
        "v:group": read_child_elements,
        "v:rect": read_child_elements,
        "v:roundrect": read_child_elements,
        "v:shape": read_child_elements,
        "v:textbox": read_child_elements,
        "w:txbxContent": read_child_elements,
        "w:pict": pict,
        "w:hyperlink": hyperlink,
        "w:bookmarkStart": bookmark_start,
        "w:br": break_,
        "wp:inline": inline,
        "wp:anchor": inline,
        "v:imagedata": read_imagedata,
        "w:footnoteReference": note_reference_reader("footnote"),
        "w:endnoteReference": note_reference_reader("endnote"),
        "w:commentReference": read_comment_reference,
        "mc:AlternateContent": alternate_content,
        "w:sdt": read_sdt
    }

    def read(element):
        handler = handlers.get(element.name)
        if handler is None:
            if element.name not in _ignored_elements:
                warning = results.warning("An unrecognised element was ignored: {0}".format(element.name))
                return _empty_result_with_message(warning)
            else:
                return _empty_result
        else:
            return handler(element)

    def _read_xml_elements(nodes):
        elements = filter(lambda node: isinstance(node, XmlElement), nodes)
        return _ReadResult.concat(lists.map(read, elements))

    return _read_xml_elements


def _inner_text(node):
    if node.node_type == node_types.text:
        return node.value
    else:
        return "".join(_inner_text(child) for child in node.children)


class _ReadResult(object):
    @staticmethod
    def concat(results):
        return _ReadResult(
            lists.flat_map(lambda result: result.elements, results),
            lists.flat_map(lambda result: result.extra, results),
            lists.flat_map(lambda result: result.messages, results))

    @staticmethod
    def map_results(first, second, func):
        return _ReadResult(
            [func(first.elements, second.elements)],
            first.extra + second.extra,
            first.messages + second.messages)

    def __init__(self, elements, extra, messages):
        self.elements = elements
        self.extra = extra
        self.messages = messages

    def map(self, func):
        elements = func(self.elements)
        if not isinstance(elements, list):
            elements = [elements]
        return _ReadResult(
            elements,
            self.extra,
            self.messages)

    def flat_map(self, func):
        result = func(self.elements)
        return _ReadResult(
            result.elements,
            self.extra + result.extra,
            self.messages + result.messages)

    def to_extra(self):
        return _ReadResult([], _concat(self.extra, self.elements), self.messages)

    def append_extra(self):
        return _ReadResult(_concat(self.elements, self.extra), [], self.messages)


def _success(elements):
    if not isinstance(elements, list):
        elements = [elements]
    return _ReadResult(elements, [], [])


def _element_result_with_messages(element, messages):
    return _elements_result_with_messages([element], messages)


def _elements_result_with_messages(elements, messages):
    return _ReadResult(elements, [], messages)


_empty_result = _ReadResult([], [], [])


def _empty_result_with_message(message):
    return _ReadResult([], [], [message])


def _concat(*values):
    result = []
    for value in values:
        for element in value:
            result.append(element)
    return result


def _add_attrs(obj, **kwargs):
    for key, value in kwargs.items():
        setattr(obj, key, value)

    return obj


def _is_int(value):
    if value is None:
        return False

    try:
        int(value)
    except ValueError:
        return False

    return True
