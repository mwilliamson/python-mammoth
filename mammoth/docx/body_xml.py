import contextlib

from .. import documents
from .. import results
from .. import lists
from .xmlparser import node_types, XmlElement
from .styles_xml import Styles


def reader(numbering=None,
        content_types=None,
        relationships=None,
        styles=None,
        docx_file=None,
        files=None):
    
    if styles is None:
        styles = Styles({}, {})
    
    read, read_all = _create_reader(
        numbering=numbering,
        content_types=content_types,
        relationships=relationships,
        styles=styles,
        docx_file=docx_file,
        files=files,
    )
    return _BodyReader(read, read_all)



class _BodyReader(object):
    def __init__(self, read, read_all):
        self._read = read
        self._read_all = read_all
    
    def read(self, element):
        result = self._read(element)
        if result.elements:
            element = result.elements[0]
        else:
            element = None
        return results.Result(element, result.messages)
    
    def read_all(self, elements):
        result = self._read_all(elements)
        return results.Result(result.elements, result.messages)


def _create_reader(numbering, content_types, relationships, styles, docx_file, files):
    _ignored_elements = set([
        "office-word:wrap",
        "v:shadow",
        "v:shapetype",
        "w:bookmarkEnd",
        "w:sectPr",
        "w:proofErr",
        "w:lastRenderedPageBreak",
        "w:commentRangeStart",
        "w:commentRangeEnd",
        "w:commentReference",
        "w:del",
        "w:footnoteRef",
        "w:endnoteRef",
        "w:pPr",
        "w:rPr",
        "w:tblPr",
        "w:tblGrid",
        "w:tcPr",
    ])

    def text(element):
        return _success(documents.Text(_inner_text(element)))


    def run(element):
        properties = element.find_child_or_null("w:rPr")
        vertical_alignment = properties \
            .find_child_or_null("w:vertAlign") \
            .attributes.get("w:val")
        
        is_bold = properties.find_child("w:b")
        is_italic = properties.find_child("w:i")
        is_underline = properties.find_child("w:u")
        is_strikethrough = properties.find_child("w:strike")
        
        return _ReadResult.map_results(
            _read_run_style(properties),
            _read_xml_elements(element.children),
            lambda style, children: documents.run(
                children=children,
                style_id=style[0],
                style_name=style[1],
                is_bold=is_bold,
                is_italic=is_italic,
                is_underline=is_underline,
                is_strikethrough=is_strikethrough,
                vertical_alignment=vertical_alignment,
            ))


    def paragraph(element):
        properties = element.find_child_or_null("w:pPr")
        numbering = _read_numbering_properties(properties.find_child_or_null("w:numPr"))
        
        return _ReadResult.map_results(
            _read_paragraph_style(properties),
            _read_xml_elements(element.children),
            lambda style, children: documents.paragraph(
                children=children,
                style_id=style[0],
                style_name=style[1],
                numbering=numbering,
            )).append_extra()
    
    def _read_paragraph_style(properties):
        return _read_style(properties, "w:pStyle", "Paragraph", styles.find_paragraph_style_by_id)
    
    def _read_run_style(properties):
        return _read_style(properties, "w:rStyle", "Run", styles.find_character_style_by_id)
    
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

    def _read_numbering_properties(element):
        num_id = element.find_child_or_null("w:numId").attributes.get("w:val")
        level_index = element.find_child_or_null("w:ilvl").attributes.get("w:val")
        if num_id is None or level_index is None:
            return None
        else:
            return numbering.find_level(num_id, level_index)


    def tab(element):
        return _success(documents.tab())
    
    
    def table(element):
        return _read_xml_elements(element.children) \
            .flat_map(calculate_row_spans) \
            .map(documents.table)
    
    
    def table_row(element):
        return _read_xml_elements(element.children) \
            .map(documents.table_row)
    
    
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
        children_result = _read_xml_elements(element.children)
        if relationship_id is not None:
            href = relationships[relationship_id].target
            return children_result.map(lambda children: documents.hyperlink(href=href, children=children))
        elif anchor is not None:
            return children_result.map(lambda children: documents.hyperlink(anchor=anchor, children=children))
        else:
            return children_result
    
    def bookmark_start(element):
        name = element.attributes.get("w:name")
        if name == "_GoBack":
            return _empty_result
        else:
            return _success(documents.bookmark(name))
    
    
    def br(element):
        break_type = element.attributes.get("w:type")
        if break_type:
            warning = results.warning("Unsupported break type: {0}".format(break_type))
            return _empty_result_with_message(warning)
        else:
            return _success(documents.line_break())
    
    def inline(element):
        alt_text = element.find_child_or_null("wp:docPr").attributes.get("descr")
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
        image_path = "word/" + relationships[relationship_id].target.lstrip("/")
        
        def open_image():
            image_file = docx_file.open(image_path)
            if hasattr(image_file, "__exit__"):
                return image_file
            else:
                return contextlib.closing(image_file)
        
        return image_path, open_image
    
    
    def _find_linked_image(relationship_id):
        image_path = relationships[relationship_id].target
        
        def open_image():
            return files.open(image_path)
        
        return image_path, open_image
    
    def read_imagedata(element):
        title = element.attributes.get("o:title")
        return _read_image(lambda: _find_embedded_image(element.attributes["r:id"]), title)
    
    def note_reference_reader(note_type):
        def note_reference(element):
            return _success(documents.note_reference(note_type, element.attributes["w:id"]))
        
        return note_reference
    
    def alternate_content(element):
        return read_child_elements(element.find_child("mc:Fallback"))
    
    handlers = {
        "w:t": text,
        "w:r": run,
        "w:p": paragraph,
        "w:tab": tab,
        "w:tbl": table,
        "w:tr": table_row,
        "w:tc": table_cell,
        "w:ins": read_child_elements,
        "w:smartTag": read_child_elements,
        "w:drawing": read_child_elements,
        "v:roundrect": read_child_elements,
        "v:shape": read_child_elements,
        "v:textbox": read_child_elements,
        "w:txbxContent": read_child_elements,
        "w:pict": pict,
        "w:hyperlink": hyperlink,
        "w:bookmarkStart": bookmark_start,
        "w:br": br,
        "wp:inline": inline,
        "wp:anchor": inline,
        "v:imagedata": read_imagedata,
        "w:footnoteReference": note_reference_reader("footnote"),
        "w:endnoteReference": note_reference_reader("endnote"),
        "mc:AlternateContent": alternate_content,
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
    
    return read, _read_xml_elements


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
