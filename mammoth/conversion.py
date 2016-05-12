# coding=utf-8

from __future__ import unicode_literals

import base64

from . import documents, results, html_paths, images, writers, html, lists
from .docx.files import InvalidFileReferenceError


def convert_document_element_to_html(element,
        style_map=None,
        convert_image=None,
        id_prefix=None,
        output_format=None,
        ignore_empty_paragraphs=True):
            
    if style_map is None:
        style_map = []
    
    if id_prefix is None:
        id_prefix = ""
    
    if convert_image is None:
        convert_image = images.img_element(_generate_image_attributes)
    
    messages = []
    converter = _DocumentConverter(
        messages=messages,
        style_map=style_map,
        convert_image=convert_image,
        id_prefix=id_prefix,
        ignore_empty_paragraphs=ignore_empty_paragraphs,
        note_references=[])
    nodes = converter.visit(element)
    
    writer = writers.writer(output_format)
    html.write(writer, html.collapse(html.strip_empty(nodes)))
    return results.Result(writer.as_string(), messages)
    
    
def _generate_image_attributes(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }


class _DocumentConverter(documents.ElementVisitor):
    def __init__(self, messages, style_map, convert_image, id_prefix, ignore_empty_paragraphs, note_references):
        self._messages = messages
        self._style_map = style_map
        self._id_prefix = id_prefix
        self._ignore_empty_paragraphs = ignore_empty_paragraphs
        self._note_references = note_references
        self._convert_image = convert_image
    
    def visit_image(self, image):
        try:
            return self._convert_image(image)
        except InvalidFileReferenceError as error:
            self._messages.append(results.warning(str(error)))
            return []

    def visit_document(self, document):
        nodes = self._visit_all(document.children)
        notes = [
            document.notes.resolve(reference)
            for reference in self._note_references
        ]
        notes_list = html.element("ol", {}, self._visit_all(notes))
        return nodes + [notes_list]


    def visit_paragraph(self, paragraph):
        content = self._visit_all(paragraph.children)
        if self._ignore_empty_paragraphs:
            children = content
        else:
            children = [html.force_write] + content
        
        html_path = self._find_html_path_for_paragraph(paragraph)
        return html_path.wrap(children)


    def visit_run(self, run):
        nodes = self._visit_all(run.children)
        if run.is_strikethrough:
            nodes = self._find_style_for_run_property("strikethrough", default="s").wrap(nodes)
        if run.is_underline:
            nodes = self._convert_underline(nodes)
        if run.vertical_alignment == documents.VerticalAlignment.subscript:
            nodes = html_paths.element(["sub"], fresh=False).wrap(nodes)
        if run.vertical_alignment == documents.VerticalAlignment.superscript:
            nodes = html_paths.element(["sup"], fresh=False).wrap(nodes)
        if run.is_italic:
            nodes = self._find_style_for_run_property("italic", default="em").wrap(nodes)
        if run.is_bold:
            nodes = self._find_style_for_run_property("bold", default="strong").wrap(nodes)
        html_path = self._find_html_path_for_run(run)
        if html_path:
            nodes = html_path.wrap(nodes)
        return nodes
    
    
    def _convert_underline(self, nodes):
        return self._find_style_for_run_property("underline").wrap(nodes)
    
    
    def _find_style_for_run_property(self, element_type, default=None):
        style = self._find_style(None, element_type)
        if style is not None:
            return style.html_path
        elif default is not None:
            return html_paths.element(default, fresh=False)
        else:
            return html_paths.empty

    def visit_text(self, text):
        return [html.text(text.value)]
    
    
    def visit_hyperlink(self, hyperlink):
        if hyperlink.anchor is None:
            href = hyperlink.href
        else:
            href = "#{0}".format(self._html_id(hyperlink.anchor))
        
        nodes = self._visit_all(hyperlink.children)
        return [html.collapsible_element("a", {"href": href}, nodes)]
    
    
    def visit_bookmark(self, bookmark):
        element = html.collapsible_element(
            "a",
            {"id": self._html_id(bookmark.name)},
            [html.force_write])
        return [element]
    
    
    def visit_tab(self, tab):
        return [html.text("\t")]
    
    
    def visit_table(self, table):
        return [html.element("table", {}, self._visit_all(table.children))]
    
    
    def visit_table_row(self, table_row):
        return [html.element("tr", {}, self._visit_all(table_row.children))]
    
    
    def visit_table_cell(self, table_cell):
        attributes = {}
        if table_cell.colspan != 1:
            attributes["colspan"] = str(table_cell.colspan)
        if table_cell.rowspan != 1:
            attributes["rowspan"] = str(table_cell.rowspan)
        nodes = [html.force_write] + self._visit_all(table_cell.children)
        return [
            html.element("td", attributes, nodes)
        ]
    
    
    def visit_line_break(self, line_break):
        return [html.self_closing_element("br")]
    
    def visit_note_reference(self, note_reference):
        self._note_references.append(note_reference);
        note_number = len(self._note_references)
        return [
            html.element("sup", {}, [
                html.element("a", {
                    "href": "#" + self._note_html_id(note_reference),
                    "id": self._note_ref_html_id(note_reference),
                }, [html.text("[{0}]".format(note_number))])
            ])
        ]
    
    def visit_note(self, note):
        note_body = self._visit_all(note.body) + [
            html.collapsible_element("p", {}, [
                html.text(" "),
                html.element("a", {"href": "#" + self._note_ref_html_id(note)}, [
                    html.text(_up_arrow)
                ]),
            ])
        ]
        return [
            html.element("li", {"id": self._note_html_id(note)}, note_body)
        ]
        self._html_generator.start("li", {"id": self._note_html_id(note)})
        note_generator = self._html_generator.child()
        self._with_html_generator(note_generator)._visit_all(note.body)
        note_generator.text(" ")
        note_generator.start("a", {"href": "#" + self._note_ref_html_id(note)})
        note_generator.text(_up_arrow)
        note_generator.end_all()
        self._html_generator.append(note_generator)
        self._html_generator.end()


    def _visit_all(self, elements):
        return lists.flat_map(self.visit, elements)


    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element("p", fresh=True)])
        return self._find_html_path(paragraph, "paragraph", default)
    
    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", default=None)
        
    
    def _find_html_path(self, element, element_type, default):
        style = self._find_style(element, element_type)
        if style is not None:
            return style.html_path
        
        if element.style_id is not None:
            self._messages.append(results.warning(
                "Unrecognised {0} style: {1} (Style ID: {2})".format(
                    element_type, element.style_name, element.style_id)
            ))
        
        return default
    
    def _find_style(self, element, element_type):
        for style in self._style_map:
            document_matcher = style.document_matcher
            if _document_matcher_matches(document_matcher, element, element_type):
                return style

    def _note_html_id(self, note):
        return self._html_id("{0}-{1}".format(note.note_type, note.note_id))
        
    def _note_ref_html_id(self, note):
        return self._html_id("{0}-ref-{1}".format(note.note_type, note.note_id))
    
    def _html_id(self, suffix):
        return "{0}{1}".format(self._id_prefix, suffix)
        

def _document_matcher_matches(matcher, element, element_type):
    if matcher.element_type in ["underline", "strikethrough", "bold", "italic"]:
        return matcher.element_type == element_type
    else:
        return (
            matcher.element_type == element_type and (
                matcher.style_id is None or
                matcher.style_id == element.style_id
            ) and (
                matcher.style_name is None or
                element.style_name is not None and (matcher.style_name.upper() == element.style_name.upper())
            ) and (
                element_type != "paragraph" or
                matcher.numbering is None or
                matcher.numbering == element.numbering
            )
        )

_up_arrow = "↑"
