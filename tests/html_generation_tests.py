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


@istest
def all_elements_are_closed_by_end_all():
    generator = HtmlGenerator()
    generator.start("p")
    generator.start("span")
    generator.text("Hello!")
    generator.end_all()
    assert_equal("<p><span>Hello!</span></p>", generator.html_string())


@istest
def elements_with_no_text_are_not_generator():
    generator = HtmlGenerator()
    generator.start("p")
    generator.start("span")
    generator.end_all()
    assert_equal("", generator.html_string())
    
