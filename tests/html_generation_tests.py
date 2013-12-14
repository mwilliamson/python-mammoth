from nose.tools import istest, assert_equal

from mammoth.html_generation import HtmlGenerator


@istest
def generates_empty_string_when_newly_created():
    generator = HtmlGenerator()
    assert_equal("", generator.html_string())


@istest
def html_escapes_text():
    generator = HtmlGenerator()
    generator.text("<")
    assert_equal("&lt;", generator.html_string())
