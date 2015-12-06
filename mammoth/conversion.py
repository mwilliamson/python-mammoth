# coding=utf-8

from __future__ import unicode_literals

import base64
import random

from . import documents, results, html_paths, images, writers
from .html_generation import HtmlGenerator, satisfy_html_path, append_html_path
from .docx.files import InvalidFileReferenceError


def convert_document_element_to_html(element,
        style_map=None,
        convert_image=None,
        convert_underline=None,
        id_prefix=None,
        output_format=None,
        ignore_empty_paragraphs=True):
            
    if style_map is None:
        style_map = []
    
    if id_prefix is None:
        id_prefix = str(random.randint(0, 1000000000000000))
    
    if convert_image is None:
        convert_image = images.inline(_generate_image_attributes)
    
    def create_writer():
        return writers.writer(output_format)
    
    html_generator = HtmlGenerator(create_writer)
    messages = []
    converter = _DocumentConverter(
        messages=messages,
        style_map=style_map,
        convert_image=convert_image,
        convert_underline=convert_underline,
        id_prefix=id_prefix,
        ignore_empty_paragraphs=ignore_empty_paragraphs,
        html_generator=html_generator,
        note_references=[])
    converter.visit(element)
    html_generator.end_all()
    return results.Result(html_generator.as_string(), messages)
    
    
def _generate_image_attributes(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }


class _DocumentConverter(documents.ElementVisitor):
    def __init__(self, messages, style_map, convert_image, convert_underline, id_prefix, ignore_empty_paragraphs, html_generator, note_references):
        self._messages = messages
        self._style_map = style_map
        self._id_prefix = id_prefix
        self._ignore_empty_paragraphs = ignore_empty_paragraphs
        self._note_references = note_references
        self._convert_underline = convert_underline or self._default_convert_underline
        self._convert_image = convert_image
        self._html_generator = html_generator
    
    def _with_html_generator(self, html_generator):
        return _DocumentConverter(
            messages=self._messages,
            style_map=self._style_map,
            convert_image=self._convert_image,
            convert_underline=self._convert_underline,
            id_prefix=self._id_prefix,
            ignore_empty_paragraphs=self._ignore_empty_paragraphs,
            html_generator=html_generator,
            note_references=self._note_references
        )

    def visit_image(self, image):
        try:
            self._convert_image(image, self._html_generator)
        except InvalidFileReferenceError as error:
            self._messages.append(results.warning(str(error)))

    def visit_document(self, document):
        self._visit_all(document.children)
        self._html_generator.end_all()
        self._html_generator.start("ol")
        notes = [
            document.notes.resolve(reference)
            for reference in self._note_references
        ]
        self._visit_all(notes)
        self._html_generator.end()


    def visit_paragraph(self, paragraph):
        html_path = self._find_html_path_for_paragraph(paragraph)
        satisfy_html_path(self._html_generator, html_path)
        if not self._ignore_empty_paragraphs:
            self._html_generator.write_all()
        self._visit_all(paragraph.children)


    def visit_run(self, run):
        run_generator = self._html_generator.child()
        html_path = self._find_html_path_for_run(run)
        if html_path:
            satisfy_html_path(run_generator, html_path)
        if run.is_bold:
            run_generator.start("strong")
        if run.is_italic:
            run_generator.start("em")
        if run.vertical_alignment == documents.VerticalAlignment.superscript:
            run_generator.start("sup")
        if run.vertical_alignment == documents.VerticalAlignment.subscript:
            run_generator.start("sub")
        if run.is_underline:
            self._convert_underline(run_generator)
        if run.is_strikethrough:
            self._convert_strikethrough(run_generator)
        self._with_html_generator(run_generator)._visit_all(run.children)
        run_generator.end_all()
        self._html_generator.append(run_generator)
    
    
    def _default_convert_underline(self, run_generator):
        style = self._find_style(None, "underline")
        if style is not None:
            append_html_path(run_generator, style.html_path)
    
    
    def _convert_strikethrough(self, run_generator):
        style = self._find_style(None, "strikethrough")
        if style is None:
            run_generator.start("s")
        else:
            append_html_path(run_generator, style.html_path)
        
    

    def visit_text(self, text):
        self._html_generator.text(text.value)
    
    
    def visit_hyperlink(self, hyperlink):
        if hyperlink.anchor is None:
            href = hyperlink.href
        else:
            href = "#{0}".format(self._html_id(hyperlink.anchor))
        self._html_generator.start("a", {"href": href})
        self._visit_all(hyperlink.children)
        self._html_generator.end()
    
    
    def visit_bookmark(self, bookmark):
        self._html_generator.start("a", {"id": self._html_id(bookmark.name)}, always_write=True)
        self._html_generator.end()
    
    
    def visit_tab(self, tab):
        self._html_generator.text("\t")
    
    
    def visit_table(self, table):
        self._html_generator.end_all()
        self._html_generator.start("table")
        self._visit_all(table.children)
        self._html_generator.end()
    
    
    def visit_table_row(self, table_row):
        self._html_generator.start("tr")
        self._visit_all(table_row.children)
        self._html_generator.end()
    
    
    def visit_table_cell(self, table_cell):
        self._html_generator.start("td", always_write=True)
        for child in table_cell.children:
            child_generator = self._html_generator.child()
            self._with_html_generator(child_generator).visit(child)
            child_generator.end_all()
            self._html_generator.append(child_generator)
            
        self._html_generator.end()
    
    
    def visit_line_break(self, line_break):
        self._html_generator.self_closing("br")
    
    def visit_note_reference(self, note_reference):
        self._html_generator.start("sup")
        self._html_generator.start("a", {
            "href": "#" + self._note_html_id(note_reference),
            "id": self._note_ref_html_id(note_reference),
        })
        self._note_references.append(note_reference);
        note_number = len(self._note_references)
        self._html_generator.text("[{0}]".format(note_number))
        self._html_generator.end()
        self._html_generator.end()
    
    def visit_note(self, note):
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
        for element in elements:
            self.visit(element)


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
        return "{0}-{1}".format(self._id_prefix, suffix)
        

def _document_matcher_matches(matcher, element, element_type):
    if matcher.element_type in ["underline", "strikethrough"]:
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
