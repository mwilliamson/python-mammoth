import contextlib

from .. import documents
from .. import results
from .. import lists
from .xmlparser import node_types


def reader(numbering=None,
        content_types=None,
        relationships=None,
        styles=None,
        docx_file=None,
        files=None):
    
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
        return results.Result(result.value, result.messages)
    
    def read_all(self, elements):
        result = self._read_all(elements)
        return results.Result(result.value, result.messages)


def _create_reader(numbering, content_types, relationships, styles, docx_file, files):
    _ignored_elements = set([
        "office-word:wrap",
        "v:shadow",
        "v:shapetype",
        "w:bookmarkStart",
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
        style_id = properties \
            .find_child_or_null("w:rStyle") \
            .attributes.get("w:val")
        
        if style_id is None:
            style_name = None
        else:
            style_name = styles.find_character_style_by_id(style_id).name
        
        vertical_alignment = properties \
            .find_child_or_null("w:vertAlign") \
            .attributes.get("w:val")
        
        is_bold = properties.find_child("w:b")
        is_italic = properties.find_child("w:i")
        is_underline = properties.find_child("w:u")
        is_strikethrough = properties.find_child("w:strike")
        
        return _read_xml_elements(element.children) \
            .map(lambda children: documents.run(
                children=children,
                style_id=style_id,
                style_name=style_name,
                is_bold=is_bold,
                is_italic=is_italic,
                is_underline=is_underline,
                is_strikethrough=is_strikethrough,
                vertical_alignment=vertical_alignment,
            ))


    def paragraph(element):
        properties = element.find_child_or_null("w:pPr")
        style_id = properties \
            .find_child_or_null("w:pStyle") \
            .attributes.get("w:val")
        
        if style_id is None:
            style_name = None
        else:
            style_name = styles.find_paragraph_style_by_id(style_id).name
        
        numbering = _read_numbering_properties(properties.find_child_or_null("w:numPr"))
        
        return _read_xml_elements(element.children) \
            .map(lambda children: documents.paragraph(
                children=children,
                style_id=style_id,
                style_name=style_name,
                numbering=numbering,
            )) \
            .append_extra()

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
            .map(documents.table)
    
    
    def table_row(element):
        return _read_xml_elements(element.children) \
            .map(documents.table_row)
    
    
    def table_cell(element):
        return _read_xml_elements(element.children) \
            .map(documents.table_cell)
    
    
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
            return _empty_result_with_messages([warning])
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
        return _combine_results(map(lambda blip: _read_blip(blip, alt_text), blips))
    
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
                return _empty_result_with_messages([warning])
            else:
                return _success(None)
        else:
            return handler(element)
        

    def _read_xml_elements(elements):
        return _combine_results(map(read, elements)) \
            .map(lambda values: lists.collect(values))
    
    return read, _read_xml_elements


def _find(predicate, iterable):
    for item in iterable:
        if predicate(item):
            return item


def _find_child(element, name):
    return _find(lambda child: child.name == name, element.children)


def _inner_text(node):
    if node.node_type == node_types.text:
        return node.value
    else:
        return "".join(_inner_text(child) for child in node.children)



class _ReadResult(object):
    def __init__(self, value, extra, messages):
        if extra is None:
            extra = []
        self._result = results.Result((value, extra), messages)
    
    @property
    def value(self):
        return self._result.value[0]
    
    @property
    def extra(self):
        return self._result.value[1]
    
    @property
    def messages(self):
        return self._result.messages
    
    def map(self, func):
        result = self._result.map(lambda value: func(value[0]))
        return _ReadResult(result.value, self.extra, result.messages)
    
    def to_extra(self):
        return _ReadResult(None, _concat(self.extra, self.value), self.messages)
    
    def append_extra(self):
        return _ReadResult(_concat(self.value, self.extra), None, self.messages)

def _success(element):
    return _ReadResult(element, None, [])

def _element_result_with_messages(element, messages):
    return _ReadResult(element, None, messages)

def _combine_results(read_results):
    combined = results.combine(result._result for result in read_results)
    if combined.value:
        value, extras = map(list, zip(*combined.value))
        extra = sum(extras, [])
    else:
        value, extra = [], None
    return _ReadResult(value, extra, combined.messages)

_empty_result = _success(None)

def _empty_result_with_messages(messages):
    return _ReadResult(None, None, messages)

def _concat(*values):
    valid_values = list(filter(None, values))
    if not valid_values:
        return None
    elif len(valid_values) == 1:
        return valid_values[0]
    else:
        return sum(list(map(_to_list, valid_values)), [])

def _to_list(value):
    if isinstance(value, list):
        return value
    else:
        return [value]
