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
def self_closing_tag_is_self_closing():
    generator = HtmlGenerator()
    generator.self_closing("br")
    assert_equal("<br />", generator.html_string())


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
    

@istest
def elements_with_empty_string_text_are_not_generator():
    generator = HtmlGenerator()
    generator.start("p")
    generator.start("span")
    generator.text("")
    generator.end_all()
    assert_equal("", generator.html_string())
    

@istest
def self_closing_tag_can_have_attributes():
    generator = HtmlGenerator()
    generator.self_closing("br", {"data-blah": "42"})
    assert_equal('<br data-blah="42" />', generator.html_string())


@istest
def attribute_values_are_escaped():
    generator = HtmlGenerator()
    generator.self_closing("br", {"data-blah": "<"})
    assert_equal('<br data-blah="&lt;" />', generator.html_string())


@istest
def opening_tag_can_have_attributes():
    generator = HtmlGenerator()
    generator.start("p", {"data-blah": "42"})
    generator.text("Hello!")
    generator.end()
    assert_equal('<p data-blah="42">Hello!</p>', generator.html_string())


@istest
def appending_another_html_generator_does_nothing_if_empty():
    generator = HtmlGenerator()
    generator.start("p")
    generator.append(HtmlGenerator())
    assert_equal('', generator.html_string())


@istest
def appending_another_html_generator_writes_out_elements_if_other_generator_is_not_empty():
    generator = HtmlGenerator()
    generator.start("p")
    other = HtmlGenerator()
    other.text("Hello!")
    generator.append(other)
    assert_equal('<p>Hello!', generator.html_string())
