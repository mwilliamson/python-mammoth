# coding=utf-8

import base64
import random
import sys

from . import documents, results, html_paths, images
from .html_generation import HtmlGenerator, satisfy_html_path


def convert_document_element_to_html(element,
        style_map=None,
        convert_image=None,
        convert_underline=None,
        generate_uniquifier=None):
            
    if style_map is None:
        style_map = []
    
    if generate_uniquifier is None:
        generate_uniquifier = lambda: random.randint(0, 1000000000000000)
        
    html_generator = HtmlGenerator()
    converter = DocumentConverter(style_map,
        convert_image=convert_image,
        convert_underline=convert_underline,
        generate_uniquifier=generate_uniquifier)
    converter.convert_element_to_html(element, html_generator,)
    html_generator.end_all()
    return results.Result(html_generator.html_string(), converter.messages)


class DocumentConverter(object):
    def __init__(self, style_map, convert_image, convert_underline, generate_uniquifier):
        self.messages = []
        self._style_map = style_map
        self._uniquifier = generate_uniquifier()
        self._footnote_ids = []
        self._converters = {
            documents.Document: self._convert_document,
            documents.Paragraph: self._convert_paragraph,
            documents.Run: self._convert_run,
            documents.Text: self._convert_text,
            documents.Hyperlink: self._convert_hyperlink,
            documents.Tab: self._convert_tab,
            documents.Table: self._convert_table,
            documents.TableRow: self._convert_table_row,
            documents.TableCell: self._convert_table_cell,
            documents.LineBreak: self._line_break,
            documents.Image: convert_image or images.inline(self._convert_image),
            documents.FootnoteReference: self._convert_footnote_reference,
            documents.Footnote: self._convert_footnote,
        }
        self._convert_underline = convert_underline


    def convert_element_to_html(self, element, html_generator):
        self._converters[type(element)](element, html_generator)


    def _convert_document(self, document, html_generator):
        self._convert_elements_to_html(document.children, html_generator)
        html_generator.end_all()
        html_generator.start("ol")
        footnotes = [
            document.footnotes.find_footnote_by_id(footnote_id)
            for footnote_id in self._footnote_ids
        ]
        self._convert_elements_to_html(footnotes, html_generator)
        html_generator.end()


    def _convert_paragraph(self, paragraph, html_generator):
        html_path = self._find_html_path_for_paragraph(paragraph)
        satisfy_html_path(html_generator, html_path)
        self._convert_elements_to_html(paragraph.children, html_generator)


    def _convert_run(self, run, html_generator):
        run_generator = HtmlGenerator()
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
        if run.is_underline and self._convert_underline is not None:
            self._convert_underline(run_generator)
        self._convert_elements_to_html(run.children, run_generator)
        run_generator.end_all()
        html_generator.append(run_generator)


    def _convert_text(self, text, html_generator):
        html_generator.text(text.value)
    
    
    def _convert_hyperlink(self, hyperlink, html_generator):
        html_generator.start("a", {"href": hyperlink.href})
        self._convert_elements_to_html(hyperlink.children, html_generator)
        html_generator.end()
    
    
    def _convert_tab(self, tab, html_generator):
        html_generator.text("\t")
    
    
    def _convert_table(self, table, html_generator):
        html_generator.end_all()
        html_generator.start("table")
        self._convert_elements_to_html(table.children, html_generator)
        html_generator.end()
    
    
    def _convert_table_row(self, table_row, html_generator):
        html_generator.start("tr")
        self._convert_elements_to_html(table_row.children, html_generator)
        html_generator.end()
    
    
    def _convert_table_cell(self, table_cell, html_generator):
        html_generator.start("td", always_write=True)
        for child in table_cell.children:
            child_generator = HtmlGenerator()
            self.convert_element_to_html(child, child_generator)
            child_generator.end_all()
            html_generator.append(child_generator)
            
        html_generator.end()
    
    
    def _line_break(self, line_break, html_generator):
        html_generator.self_closing("br")
    
    
    def _convert_image(self, image):
        with image.open() as image_bytes:
            encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
        
        return {
            "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
        }
    
    def _convert_footnote_reference(self, footnote_reference, html_generator):
        uid = self._footnote_uid(footnote_reference.footnote_id)
        html_generator.start("sup")
        html_generator.start("a", {
            "href": "#footnote-" + uid,
            "id": "footnote-ref-" + uid
        })
        self._footnote_ids.append(footnote_reference.footnote_id);
        footnote_number = len(self._footnote_ids)
        html_generator.text("[{0}]".format(footnote_number))
        html_generator.end()
        html_generator.end()
    
    def _convert_footnote(self, footnote, html_generator):
        uid = self._footnote_uid(footnote.id)
        html_generator.start("li", {"id": "footnote-{0}".format(uid)})
        footnote_generator = HtmlGenerator()
        self._convert_elements_to_html(footnote.body, footnote_generator)
        footnote_generator.text(" ")
        footnote_generator.start("a", {"href": "#footnote-ref-{0}".format(uid)})
        footnote_generator.text(_up_arrow)
        footnote_generator.end_all()
        html_generator.append(footnote_generator)
        html_generator.end()


    def _convert_elements_to_html(self, elements, html_generator):
        for element in elements:
            self.convert_element_to_html(element, html_generator)


    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element("p", fresh=True)])
        return self._find_html_path(paragraph, "paragraph", default)
    
    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", default=None)
        
    
    def _find_html_path(self, element, element_type, default):
        for style in self._style_map:
            document_matcher = style.document_matcher
            if _document_matcher_matches(document_matcher, element, element_type):
                return style.html_path
        
        if element.style_id is not None:
            self.messages.append(results.warning(
                "Unrecognised {0} style: {1} (Style ID: {2})".format(
                    element_type, element.style_name, element.style_id)
            ))
        
        return default
        

    def _footnote_uid(self, footnote_id):
        return "{0}-{1}".format(self._uniquifier, footnote_id)
        

def _document_matcher_matches(matcher, element, element_type):
    return (
        matcher.element_type == element_type and (
            matcher.style_id is None or
            matcher.style_id == element.style_id
        ) and (
            matcher.style_name is None or
            matcher.style_name == element.style_name
        ) and (
            element_type != "paragraph" or
            matcher.numbering is None or
            matcher.numbering == element.numbering
        )
    )

_up_arrow = "↑"
if sys.version_info[0] < 3:
    _up_arrow = _up_arrow.decode("utf8")
