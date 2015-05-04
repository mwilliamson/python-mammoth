# coding=utf-8

from __future__ import unicode_literals

import base64
import random

from . import documents, results, html_paths, images, writers
from .html_paths import HtmlPath
from .document_matchers import DocumentMatcher
from .html_generation import HtmlGenerator, satisfy_html_path
from .documents import (Node, Document, Paragraph, Run, Text, Hyperlink,
    Bookmark, Tab, Table, TableRow, TableCell, LineBreak, Image,
    NoteReference, Note, Numbering)
from .results import Result, Message
from .images import ImageConverter
from .styles import Style
from .writers import Writer


#:: Node, ?style_map: list[Style], ?convert_image: ImageConverter, ?convert_underline: object, ?id_prefix: str, ?output_format: str -> Result[str]
def convert_document_element_to_html(element,
        style_map=None,
        convert_image=None,
        convert_underline=None,
        id_prefix=None,
        output_format=None):
            
    if style_map is None:
        #:: list[Style]
        style_map = []
    
    if id_prefix is None:
        id_prefix = str(random.randint(0, 1000000000000000))
    
    if output_format is None:
        output_format = "html"
    
    #:: -> Writer
    def create_writer():
        return writers.writer(output_format)
    
    html_generator = HtmlGenerator(create_writer)
    converter = DocumentConverter(style_map,
        convert_image=convert_image,
        convert_underline=convert_underline,
        id_prefix=id_prefix)
    converter.convert_element_to_html(element, html_generator,)
    html_generator.end_all()
    return results.Result(html_generator.as_string(), converter.messages)


#:structural-type StyledElement:
#:  style_id: str | none
#:  style_name: str | none
StyledElement = None


#:structural-type NoteIdentifier:
#:  note_type: str
#:  note_id: str
NoteIdentifier = None


class DocumentConverter(object):
    #:: Self, style_map: list[Style], convert_image: ImageConverter | none, convert_underline: object, id_prefix: str -> none
    def __init__(self, style_map, convert_image, convert_underline, id_prefix):
        #:: list[Message]
        self.messages = []
        self._style_map = style_map
        self._id_prefix = id_prefix
        #:: list[NoteReference]
        self._note_references = []
        self._converters = {
            documents.Document: self._convert_document,
            documents.Paragraph: self._convert_paragraph,
            documents.Run: self._convert_run,
            documents.Text: self._convert_text,
            documents.Hyperlink: self._convert_hyperlink,
            documents.Bookmark: self._convert_bookmark,
            documents.Tab: self._convert_tab,
            documents.Table: self._convert_table,
            documents.TableRow: self._convert_table_row,
            documents.TableCell: self._convert_table_cell,
            documents.LineBreak: self._line_break,
            documents.Image: convert_image or images.inline(self._convert_image),
            documents.NoteReference: self._convert_note_reference,
            documents.Note: self._convert_note,
        }
        self._convert_underline = convert_underline


    #:: Self, Node, HtmlGenerator -> none
    def convert_element_to_html(self, element, html_generator):
        #self._converters[type(element)](element, html_generator)
        return None

    
    #:: Self, Document, HtmlGenerator -> none
    def _convert_document(self, document, html_generator):
        self._convert_elements_to_html(document.children, html_generator)
        html_generator.end_all()
        html_generator.start("ol")
        notes = [
            document.notes.resolve(reference)
            for reference in self._note_references
        ]
        self._convert_elements_to_html(notes, html_generator)
        html_generator.end()


    #:: Self, Paragraph, HtmlGenerator -> none
    def _convert_paragraph(self, paragraph, html_generator):
        html_path = self._find_html_path_for_paragraph(paragraph)
        if html_path is not None:
            satisfy_html_path(html_generator, html_path)
        self._convert_elements_to_html(paragraph.children, html_generator)


    #:: Self, Run, HtmlGenerator -> none
    def _convert_run(self, run, html_generator):
        run_generator = html_generator.child()
        html_path = self._find_html_path_for_run(run)
        if html_path is not None:
            satisfy_html_path(run_generator, html_path)
        if run.is_bold:
            run_generator.start("strong")
        if run.is_italic:
            run_generator.start("em")
        if run.vertical_alignment == documents.VerticalAlignment.superscript:
            run_generator.start("sup")
        if run.vertical_alignment == documents.VerticalAlignment.subscript:
            run_generator.start("sub")
        #~ if run.is_underline and self._convert_underline is not None:
            #~ self._convert_underline(run_generator)
        self._convert_elements_to_html(run.children, run_generator)
        run_generator.end_all()
        html_generator.append(run_generator)


    #:: Self, Text, HtmlGenerator -> none
    def _convert_text(self, text, html_generator):
        html_generator.text(text.value)
    
    
    #:: Self, Hyperlink, HtmlGenerator -> none
    def _convert_hyperlink(self, hyperlink, html_generator):
        anchor = hyperlink.anchor
        if anchor is None:
            href = hyperlink.href
        else:
            href = "#{0}".format(self._html_id(anchor))
            
        if href is None:
            href = ""
            
        html_generator.start("a", {"href": href})
        self._convert_elements_to_html(hyperlink.children, html_generator)
        html_generator.end()
    
    
    #:: Self, Bookmark, HtmlGenerator -> none
    def _convert_bookmark(self, bookmark, html_generator):
        html_generator.start("a", {"id": self._html_id(bookmark.name)}, always_write=True)
        html_generator.end()
    
    
    #:: Self, Tab, HtmlGenerator -> none
    def _convert_tab(self, tab, html_generator):
        html_generator.text("\t")
    
    
    #:: Self, Table, HtmlGenerator -> none
    def _convert_table(self, table, html_generator):
        html_generator.end_all()
        html_generator.start("table")
        self._convert_elements_to_html(table.children, html_generator)
        html_generator.end()
    
    
    #:: Self, TableRow, HtmlGenerator -> none
    def _convert_table_row(self, table_row, html_generator):
        html_generator.start("tr")
        self._convert_elements_to_html(table_row.children, html_generator)
        html_generator.end()
    
    
    #:: Self, TableCell, HtmlGenerator -> none
    def _convert_table_cell(self, table_cell, html_generator):
        html_generator.start("td", always_write=True)
        for child in table_cell.children:
            child_generator = html_generator.child()
            self.convert_element_to_html(child, child_generator)
            child_generator.end_all()
            html_generator.append(child_generator)
            
        html_generator.end()
    
    
    #:: Self, LineBreak, HtmlGenerator -> none
    def _line_break(self, line_break, html_generator):
        html_generator.self_closing("br")
    
    
    #:: Self, Image -> dict[str, str]
    def _convert_image(self, image):
        # TODO:
        #~ with image.open() as image_bytes:
            #~ encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
        encoded_src = ""
        
        return {
            "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
        }
    
    #:: Self, NoteReference, HtmlGenerator -> none
    def _convert_note_reference(self, note_reference, html_generator):
        html_generator.start("sup")
        html_generator.start("a", {
            "href": "#" + self._note_html_id(note_reference),
            "id": self._note_ref_html_id(note_reference),
        })
        self._note_references.append(note_reference);
        note_number = len(self._note_references)
        html_generator.text("[{0}]".format(note_number))
        html_generator.end()
        html_generator.end()
    
    #:: Self, Note, HtmlGenerator -> none
    def _convert_note(self, note, html_generator):
        html_generator.start("li", {"id": self._note_html_id(note)})
        note_generator = html_generator.child()
        self._convert_elements_to_html(note.body, note_generator)
        note_generator.text(" ")
        note_generator.start("a", {"href": "#" + self._note_ref_html_id(note)})
        note_generator.text(_up_arrow)
        note_generator.end_all()
        html_generator.append(note_generator)
        html_generator.end()


    #:: Self, iterable[object], HtmlGenerator -> none
    def _convert_elements_to_html(self, elements, html_generator):
        for element in elements:
            self.convert_element_to_html(element, html_generator)

    #:: Self, Paragraph -> HtmlPath | none
    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element(["p"], class_names=[], fresh=True)])
        return self._find_html_path(paragraph, "paragraph", numbering=paragraph.numbering, default=default)
    
    #:: Self, Run -> HtmlPath | none
    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", numbering=None, default=None)
        
    #:: Self, StyledElement, str, numbering: Numbering | none, default: HtmlPath | none -> HtmlPath | none
    def _find_html_path(self, element, element_type, numbering, default):
        for style in self._style_map:
            document_matcher = style.document_matcher
            if _document_matcher_matches(document_matcher, element, element_type, numbering):
                return style.html_path
        
        if element.style_id is not None:
            self.messages.append(results.warning(
                "Unrecognised {0} style: {1} (Style ID: {2})".format(
                    element_type, element.style_name, element.style_id)
            ))
        
        return default
        
    
    #:: Self, NoteIdentifier -> str
    def _note_html_id(self, note):
        return self._html_id("{0}-{1}".format(note.note_type, note.note_id))
    
    #:: Self, NoteIdentifier -> str
    def _note_ref_html_id(self, note):
        return self._html_id("{0}-ref-{1}".format(note.note_type, note.note_id))
    
    #:: Self, str -> str
    def _html_id(self, suffix):
        return "{0}-{1}".format(self._id_prefix, suffix)


#:: DocumentMatcher, StyledElement, str, Numbering | none -> bool
def _document_matcher_matches(matcher, element, element_type, numbering):
    matcher_style_id = matcher.style_id
    if matcher_style_id is not None:
        if matcher_style_id != element.style_id:
            return False
    
    matcher_style_name = matcher.style_name
    if matcher_style_name is not None:
        if matcher_style_name != element.style_name:
            return False
    
    matcher_numbering = matcher.numbering
    if matcher_numbering is not None:
        if matcher_numbering != numbering:
            return False
    
    return True

_up_arrow = "↑"
