import contextlib

from .. import documents
from .. import results
from .. import lists
from .xmlparser import node_types


def read_document_xml_element(element,
        numbering=None,
        content_types=None,
        relationships=None,
        styles=None,
        footnote_elements=None,
        endnote_elements=None,
        docx_file=None):
    
    note_elements = (footnote_elements or []) + (endnote_elements or [])
    
    reader = _create_reader(
        numbering=numbering,
        content_types=content_types,
        relationships=relationships,
        styles=styles,
        note_elements=note_elements,
        docx_file=docx_file,
    )
    result = reader(element)
    return results.Result(result.value, result.messages)

def _create_reader(numbering, content_types, relationships, styles, note_elements, docx_file):
    _handlers = {}
    _ignored_elements = set([
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

    def handler(name):
        def add(func):
            _handlers[name] = func
            return func
            
        return add

    @handler("w:t")
    def text(element):
        return _success(documents.Text(_inner_text(element)))


    @handler("w:r")
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


    @handler("w:p")
    def paragraph(element):
        properties = element.find_child_or_null("w:pPr")
        style_id = properties \
            .find_child_or_null("w:pStyle") \
            .attributes.get("w:val")
        
        if style_id is None:
            style_name = None
        else:
            style_name = styles.find_paragraph_style_by_id(style_id).name
        
        numbering_properties = properties.find_child("w:numPr")
        if numbering_properties is None:
            numbering = None
        else:
            numbering = _read_numbering_properties(numbering_properties)
        
        return _read_xml_elements(element.children) \
            .map(lambda children: documents.paragraph(
                children=children,
                style_id=style_id,
                style_name=style_name,
                numbering=numbering,
            )) \
            .append_extra()

    def _read_numbering_properties(element):
        num_id = element.find_child("w:numId").attributes["w:val"]
        level_index = element.find_child("w:ilvl").attributes["w:val"]
        return numbering.find_level(num_id, level_index)


    @handler("w:body")
    def body(element):
        return _read_xml_elements(element.children)


    @handler("w:document")
    def document(element):
        body_element = _find_child(element, "w:body")
        children_result = _read_xml_elements(body_element.children)
        notes_result = _combine_results(map(_read_note, note_elements)).map(documents.notes)
        return results.map(documents.document, children_result, notes_result)
    
    
    def _read_note(element):
        return _read_xml_elements(element.body).map(
            lambda body: documents.note(element.note_type, element.id, body))
     
    
    @handler("w:tab")
    def tab(element):
        return _success(documents.tab())
    
    
    @handler("w:tbl")
    def table(element):
        return _read_xml_elements(element.children) \
            .map(documents.table)
    
    
    @handler("w:tr")
    def table_row(element):
        return _read_xml_elements(element.children) \
            .map(documents.table_row)
    
    
    @handler("w:tc")
    def table_cell(element):
        return _read_xml_elements(element.children) \
            .map(documents.table_cell)
    
    
    @handler("w:ins")
    @handler("w:smartTag")
    @handler("w:drawing")
    @handler("v:shape")
    @handler("v:textbox")
    @handler("w:txbxContent")
    def read_child_elements(element):
        return _read_xml_elements(element.children)
    
    
    @handler("w:pict")
    def pict(element):
        return read_child_elements(element).to_extra()
    
    
    @handler("w:hyperlink")
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
    
    @handler("w:bookmarkStart")
    def bookmark_start(element):
        name = element.attributes.get("w:name")
        if name == "_GoBack":
            return _empty_result
        else:
            return _success(documents.bookmark(name))
    
    
    @handler("w:br")
    def br(element):
        break_type = element.attributes.get("w:type")
        if break_type:
            warning = results.warning("Unsupported break type: {0}".format(break_type))
            return _empty_result_with_messages([warning])
        else:
            return _success(documents.line_break())
    
    @handler("wp:inline")
    @handler("wp:anchor")
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
        relationship_id = element.attributes["r:embed"]
        image_path = "word/" + relationships[relationship_id].target.lstrip("/")
        content_type = content_types.find_content_type(image_path)
        
        def open_image():
            image_file = docx_file.open(image_path)
            if hasattr(image_file, "__exit__"):
                return image_file
            else:
                return contextlib.closing(image_file)
        
        image = documents.image(alt_text=alt_text, content_type=content_type, open=open_image)
        
        if content_type in ["image/png", "image/gif", "image/jpeg", "image/svg+xml", "image/tiff"]:
            messages = []
        else:
            messages = [results.warning("Image of type {0} is unlikely to display in web browsers".format(content_type))]
            
        return _element_result_with_messages(image, messages)
    
    def note_reference_reader(note_type):
        @handler("w:{0}Reference".format(note_type))
        def note_reference(element):
            return _success(documents.note_reference(note_type, element.attributes["w:id"]))
        
        return note_reference
    
    note_reference_reader("footnote")
    note_reference_reader("endnote")
    
    @handler("mc:AlternateContent")
    def alternate_content(element):
        return read_child_elements(element.find_child("mc:Fallback"))
    
    def read(element):
        handler = _handlers.get(element.name)
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
    
    return read


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
