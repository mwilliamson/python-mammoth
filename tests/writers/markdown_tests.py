from __future__ import unicode_literals

from nose.tools import istest, assert_equal

from mammoth.writers.markdown import MarkdownWriter


@istest
def special_markdown_characters_are_escaped():
    writer = _create_writer()
    writer.text(r"\*")
    assert_equal(r"\\\*", writer.as_string())


@istest
def unrecognised_elements_are_treated_as_normal_text():
    writer = _create_writer()
    writer.start("blah");
    writer.text("Hello");
    writer.end("blah");
    assert_equal("Hello", writer.as_string())


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


@istest
def h6_elements_are_converted_to_heading_with_six_leading_hashes():
    writer = _create_writer()
    writer.start("h6");
    writer.text("Hello");
    writer.end("h6");
    assert_equal("###### Hello\n\n", writer.as_string())


@istest
def br_is_written_as_two_spaces_followed_by_newline():
    writer = _create_writer()
    writer.text("Hello");
    writer.self_closing("br");
    assert_equal("Hello  \n", writer.as_string())
    


def _create_writer():
    return MarkdownWriter()
