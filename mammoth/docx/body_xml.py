import contextlib
import re
import sys

from .. import documents
from .. import results
from .. import lists
from . import complex_fields
from .dingbats import dingbats
from .xmlparser import node_types, XmlElement
from .styles_xml import Styles
from .uris import replace_fragment, uri_to_zip_entry_name

if sys.version_info >= (3, ):
    unichr = chr


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
        properties = element.find_child_or_null("w:rPr")
        vertical_alignment = properties \
            .find_child_or_null("w:vertAlign") \
            .attributes.get("w:val")
        font = properties.find_child_or_null("w:rFonts").attributes.get("w:ascii")

        font_size_string = properties.find_child_or_null("w:sz").attributes.get("w:val")
        if _is_int(font_size_string):
            # w:sz gives the font size in half points, so halve the value to get the size in points
            font_size = int(font_size_string) / 2
        else:
            font_size = None

        is_bold = read_boolean_element(properties.find_child("w:b"))
        is_italic = read_boolean_element(properties.find_child("w:i"))
        is_underline = read_underline_element(properties.find_child("w:u"))
        is_strikethrough = read_boolean_element(properties.find_child("w:strike"))
        is_all_caps = read_boolean_element(properties.find_child("w:caps"))
        is_small_caps = read_boolean_element(properties.find_child("w:smallCaps"))

        def add_complex_field_hyperlink(children):
            hyperlink_href = current_hyperlink_href()
            if hyperlink_href is None:
                return children
            else:
                return [documents.hyperlink(href=hyperlink_href, children=children)]

        return _ReadResult.map_results(
            _read_run_style(properties),
            _read_xml_elements(element.children).map(add_complex_field_hyperlink),
            lambda style, children: documents.run(
                children=children,
                style_id=style[0],
                style_name=style[1],
                is_bold=is_bold,
                is_italic=is_italic,
                is_underline=is_underline,
                is_strikethrough=is_strikethrough,
                is_all_caps=is_all_caps,
                is_small_caps=is_small_caps,
                vertical_alignment=vertical_alignment,
                font=font,
                font_size=font_size,
            ))

    def _read_run_style(properties):
        return _read_style(properties, "w:rStyle", "Run", styles.find_character_style_by_id)

    def read_boolean_element(element):
        return element and element.attributes.get("w:val") not in ["false", "0"]

    def read_underline_element(element):
        return element and element.attributes.get("w:val") not in ["false", "0", "none"]

    def paragraph(element):
        properties = element.find_child_or_null("w:pPr")
        alignment = properties.find_child_or_null("w:jc").attributes.get("w:val")
        indent = _read_paragraph_indent(properties.find_child_or_null("w:ind"))

        return _ReadResult.map_results(
            _read_paragraph_style(properties),
            _read_xml_elements(element.children),
            lambda style, children: documents.paragraph(
                children=children,
                style_id=style[0],
                style_name=style[1],
                numbering=_read_numbering_properties(
                    paragraph_style_id=style[0],
                    element=properties.find_child_or_null("w:numPr"),
                ),
                alignment=alignment,
                indent=indent,
            )).append_extra()

    def _read_paragraph_style(properties):
        return _read_style(properties, "w:pStyle", "Paragraph", styles.find_paragraph_style_by_id)

    current_instr_text = []
    complex_field_stack = []

    def current_hyperlink_href():
        for complex_field in reversed(complex_field_stack):
            if isinstance(complex_field, complex_fields.Hyperlink):
                return complex_field.href

        return None

    def read_fld_char(element):
        fld_char_type = element.attributes.get("w:fldCharType")
        if fld_char_type == "begin":
            complex_field_stack.append(complex_fields.unknown)
            del current_instr_text[:]
        elif fld_char_type == "end":
            complex_field_stack.pop()
        elif fld_char_type == "separate":
            instr_text = "".join(current_instr_text)
            hyperlink_href = parse_hyperlink_field_code(instr_text)
            if hyperlink_href is None:
                complex_field = complex_fields.unknown
            else:
                complex_field = complex_fields.hyperlink(hyperlink_href)
            complex_field_stack.pop()
            complex_field_stack.append(complex_field)
        return _empty_result

    def parse_hyperlink_field_code(instr_text):
        result = re.match(r'\s*HYPERLINK "(.*)"', instr_text)
        if result is None:
            return None
        else:
            return result.group(1)

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
        return results.warning("{0} style with ID {1} was referenced but not defined in the document".format(style_type, style_id))

    def _read_numbering_properties(paragraph_style_id, element):
        if paragraph_style_id is not None:
            level = numbering.find_level_by_paragraph_style_id(paragraph_style_id)
            if level is not None:
                return level

        num_id = element.find_child_or_null("w:numId").attributes.get("w:val")
        level_index = element.find_child_or_null("w:ilvl").attributes.get("w:val")
        if num_id is None or level_index is None:
            return None
        else:
            return numbering.find_level(num_id, level_index)

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
            warning = results.warning("A w:sym element with an unsupported character was ignored: char {0} in font {1}".format(
                char,
                font,
            ))
            return _empty_result_with_message(warning)
        else:
            return _success(documents.text(unichr(unicode_code_point)))


    def table(element):
        properties = element.find_child_or_null("w:tblPr")
        return _ReadResult.map_results(
            read_table_style(properties),
            _read_xml_elements(element.children)
                .flat_map(calculate_row_spans),

            lambda style, children: documents.table(
                children=children,
                style_id=style[0],
                style_name=style[1],
            ),
        )


    def read_table_style(properties):
        return _read_style(properties, "w:tblStyle", "Table", styles.find_table_style_by_id)


    def table_row(element):
        properties = element.find_child_or_null("w:trPr")
        is_header = bool(properties.find_child("w:tblHeader"))
        return _read_xml_elements(element.children) \
            .map(lambda children: documents.table_row(
                children=children,
                is_header=is_header,
            ))


    def table_cell(element):
        properties = element.find_child_or_null("w:tcPr")
        gridspan = properties \
            .find_child_or_null("w:gridSpan") \
            .attributes.get("w:val")

        if gridspan is None:
            colspan = 1
        else:
            colspan = int(gridspan)

        return _read_xml_elements(element.children) \
            .map(lambda children: _add_attrs(
                documents.table_cell(
                    children=children,
                    colspan=colspan
                ),
                _vmerge=read_vmerge(properties),
            ))

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
                    columns[cell_index].rowspan += 1
                else:
                    columns[cell_index] = cell
                    cell._vmerge = False
                cell_index += cell.colspan

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
        blips = element.find_children("a:graphic") \
            .find_children("a:graphicData") \
            .find_children("pic:pic") \
            .find_children("pic:blipFill") \
            .find_children("a:blip")
        return _read_blips(blips, alt_text)

    def _read_blips(blips, alt_text):
        return _ReadResult.concat(lists.map(lambda blip: _read_blip(blip, alt_text), blips))

    def _read_blip(element, alt_text):
        return _read_image(lambda: _find_blip_image(element), alt_text)

    def _read_image(find_image, alt_text):
        image_path, open_image = find_image()
        content_type = content_types.find_content_type(image_path)
        image = documents.image(alt_text=alt_text, content_type=content_type, open=open_image)

        if content_type in ["image/png", "image/gif", "image/jpeg", "image/svg+xml", "image/tiff"]:
            messages = []
        else:
            messages = [results.warning("Image of type {0} is unlikely to display in web browsers".format(content_type))]

        return _element_result_with_messages(image, messages)

    def _find_blip_image(element):
        embed_relationship_id = element.attributes.get("r:embed")
        link_relationship_id = element.attributes.get("r:link")
        if embed_relationship_id is not None:
            return _find_embedded_image(embed_relationship_id)
        elif link_relationship_id is not None:
            return _find_linked_image(link_relationship_id)

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
            return _read_image(lambda: _find_embedded_image(relationship_id), title)

    def note_reference_reader(note_type):
        def note_reference(element):
            return _success(documents.note_reference(note_type, element.attributes["w:id"]))

        return note_reference

    def read_comment_reference(element):
        return _success(documents.comment_reference(element.attributes["w:id"]))

    def alternate_content(element):
        return read_child_elements(element.find_child("mc:Fallback"))

    def read_sdt(element):
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
