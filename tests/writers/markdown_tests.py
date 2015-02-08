from __future__ import unicode_literals

from nose.tools import istest, assert_equal

from mammoth.writers.markdown import MarkdownWriter


@istest
def special_markdown_characters_are_escaped():
    writer = _create_writer()
    writer.text(r"\*")
    assert_equal(r"\\\*", writer.as_string())


@istest
def paragraphs_are_terminated_with_double_new_line():
    writer = _create_writer()
    writer.start("p");
    writer.text("Hello");
    writer.end("p");
    assert_equal("Hello\n\n", writer.as_string())


@istest
def h1_elements_are_converted_to_heading_with_leading_hash():
    writer = _create_writer()
    writer.start("h1");
    writer.text("Hello");
    writer.end("h1");
    assert_equal("# Hello\n\n", writer.as_string())
    


def _create_writer():
    return MarkdownWriter()
