from nose.tools import istest, assert_equal

from mammoth.raw_text import extract_raw_text_from_element
from mammoth import documents


@istest
def raw_text_of_text_element_is_value():
    assert_equal("Hello", extract_raw_text_from_element(documents.Text("Hello")))


@istest
def raw_text_of_paragraph_is_terminated_with_newlines():
    paragraph = documents.paragraph(children=[documents.Text("Hello")])
    assert_equal("Hello\n\n", extract_raw_text_from_element(paragraph))


@istest
def non_text_element_without_children_has_no_raw_text():
    tab = documents.Tab()
    assert not hasattr(tab, "children")
    assert_equal("", extract_raw_text_from_element(documents.Tab()))
