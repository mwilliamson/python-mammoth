from nose.tools import istest, assert_equal

from mammoth.html_generation import HtmlGenerator, satisfy_html_path
from mammoth import html_paths


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


@istest
class SatisfyPathTests(object):
    @istest
    def plain_elements_are_generated_to_satisfy_plain_path_elements(self):
        generator = HtmlGenerator()
        path = html_paths.path([html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("Hello!")
        assert_equal('<p>Hello!', generator.html_string())
    
    
    @istest
    def only_missing_elements_are_generated_to_satisfy_plain_path_elements(self):
        generator = HtmlGenerator()
        generator.start("blockquote")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["blockquote"]), html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<blockquote>Hello<p>there', generator.html_string())
    
    
    @istest
    def mismatched_elements_are_closed_to_satisfy_plain_path_elements(self):
        generator = HtmlGenerator()
        generator.start("blockquote")
        generator.start("span")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["blockquote"]), html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<blockquote><span>Hello</span><p>there', generator.html_string())
    
    
    @istest
    def fresh_element_matches_nothing(self):
        generator = HtmlGenerator()
        generator.start("blockquote")
        generator.start("p")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["blockquote"]), html_paths.element(["p"], fresh=True)])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<blockquote><p>Hello</p><p>there', generator.html_string())
