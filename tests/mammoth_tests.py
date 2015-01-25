# coding=utf-8

from __future__ import unicode_literals

from nose.tools import istest, assert_equal

from .testing import test_path

import mammoth


@istest
def docx_containing_one_paragraph_is_converted_to_single_p_element():
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<p>Walking on imported air</p>", result.value)
        assert_equal([], result.messages)


@istest
def can_read_xml_files_with_utf8_bom():
    with open(test_path("utf8-bom.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<p>This XML has a byte order mark.</p>", result.value)
        assert_equal([], result.messages)


@istest
def inline_images_are_included_in_output():
    with open(test_path("tiny-picture.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("""<p><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAOvgAADr4B6kKxwAAAABNJREFUKFNj/M+ADzDhlWUYqdIAQSwBE8U+X40AAAAASUVORK5CYII=" /></p>""", result.value)
        assert_equal([], result.messages)
        

@istest
def simple_list_is_converted_to_list_elements():
    with open(test_path("simple-list.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal([], result.messages)
        assert_equal("<ul><li>Apple</li><li>Banana</li></ul>", result.value)


@istest
def word_tables_are_converted_to_html_tables():
    expected_html = ("<p>Above</p>" +
        "<table>" +
        "<tr><td><p>Top left</p></td><td><p>Top right</p></td></tr>" +
        "<tr><td><p>Bottom left</p></td><td><p>Bottom right</p></td></tr>" +
        "</table>" +
        "<p>Below</p>")
    
    
    with open(test_path("tables.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def footnotes_are_appended_to_text():
    # TODO: don't duplicate footnotes with multiple references
    expected_html = ('<p>Ouch' +
        '<sup><a href="#footnote-42-1" id="footnote-ref-42-1">[1]</a></sup>.' +
        '<sup><a href="#footnote-42-2" id="footnote-ref-42-2">[2]</a></sup></p>' +
        '<ol><li id="footnote-42-1"><p> A tachyon walks into a bar. <a href="#footnote-ref-42-1">↑</a></p></li>' +
        '<li id="footnote-42-2"><p> Fin. <a href="#footnote-ref-42-2">↑</a></p></li></ol>')
    
    with open(test_path("footnotes.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, generate_uniquifier=lambda: 42)
        assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def endnotes_are_appended_to_text():
    expected_html = ('<p>Ouch' +
        '<sup><a href="#endnote-42-2" id="endnote-ref-42-2">[1]</a></sup>.' +
        '<sup><a href="#endnote-42-3" id="endnote-ref-42-3">[2]</a></sup></p>' +
        '<ol><li id="endnote-42-2"><p> A tachyon walks into a bar. <a href="#endnote-ref-42-2">↑</a></p></li>' +
        '<li id="endnote-42-3"><p> Fin. <a href="#endnote-ref-42-3">↑</a></p></li></ol>')
    
    with open(test_path("endnotes.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, generate_uniquifier=lambda: 42)
        # TODO: get rid of warnings
        #~ assert_equal([], result.messages)
        assert_equal(expected_html, result.value)


@istest
def transform_document_is_applied_to_document_before_conversion():
    def transform_document(document):
        document.children[0].style_id = "Heading1"
        return document
    
    with open(test_path("single-paragraph.docx"), "rb") as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj, transform_document=transform_document)
        assert_equal("<h1>Walking on imported air</h1>", result.value)
        assert_equal([], result.messages)


@istest
def can_extract_raw_text():
    with open(test_path("simple-list.docx"), "rb") as fileobj:
        result = mammoth.extract_raw_text(fileobj=fileobj)
        assert_equal([], result.messages)
        assert_equal("Apple\n\nBanana\n\n", result.value)
        
