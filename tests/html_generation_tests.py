from nose.tools import istest, assert_equal

from mammoth.html_generation import HtmlGenerator, satisfy_html_path, append_html_path
from mammoth import html_paths
from mammoth.writers import HtmlWriter


@istest
def generates_empty_string_when_newly_created():
    generator = _create_html_generator()
    assert_equal("", generator.as_string())


@istest
def html_escapes_text():
    generator = _create_html_generator()
    generator.text("<")
    assert_equal("&lt;", generator.as_string())


@istest
def self_closing_tag_is_self_closing():
    generator = _create_html_generator()
    generator.self_closing("br")
    assert_equal("<br />", generator.as_string())


@istest
def all_elements_are_closed_by_end_all():
    generator = _create_html_generator()
    generator.start("p")
    generator.start("span")
    generator.text("Hello!")
    generator.end_all()
    assert_equal("<p><span>Hello!</span></p>", generator.as_string())


@istest
def elements_with_no_text_are_not_generator():
    generator = _create_html_generator()
    generator.start("p")
    generator.start("span")
    generator.end_all()
    assert_equal("", generator.as_string())
    

@istest
def elements_with_empty_string_text_are_not_generator():
    generator = _create_html_generator()
    generator.start("p")
    generator.start("span")
    generator.text("")
    generator.end_all()
    assert_equal("", generator.as_string())
    

@istest
def self_closing_tag_can_have_attributes():
    generator = _create_html_generator()
    generator.self_closing("br", {"data-blah": "42"})
    assert_equal('<br data-blah="42" />', generator.as_string())


@istest
def attribute_values_are_escaped():
    generator = _create_html_generator()
    generator.self_closing("br", {"data-blah": "<"})
    assert_equal('<br data-blah="&lt;" />', generator.as_string())


@istest
def opening_tag_can_have_attributes():
    generator = _create_html_generator()
    generator.start("p", {"data-blah": "42"})
    generator.text("Hello!")
    generator.end()
    assert_equal('<p data-blah="42">Hello!</p>', generator.as_string())


@istest
def appending_another_html_generator_does_nothing_if_empty():
    generator = _create_html_generator()
    generator.start("p")
    generator.append(_create_html_generator())
    assert_equal('', generator.as_string())


@istest
def appending_another_html_generator_writes_out_elements_if_other_generator_is_not_empty():
    generator = _create_html_generator()
    generator.start("p")
    other = _create_html_generator()
    other.text("Hello!")
    generator.append(other)
    assert_equal('<p>Hello!', generator.as_string())


@istest
class SatisfyPathTests(object):
    @istest
    def plain_elements_are_generated_to_satisfy_plain_path_elements(self):
        generator = _create_html_generator()
        path = html_paths.path([html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("Hello!")
        assert_equal('<p>Hello!', generator.as_string())
    
    
    @istest
    def no_elements_are_generated_if_all_path_elements_are_already_satisfied(self):
        generator = _create_html_generator()
        generator.start("p")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<p>Hellothere', generator.as_string())
    
    
    @istest
    def only_missing_elements_are_generated_to_satisfy_plain_path_elements(self):
        generator = _create_html_generator()
        generator.start("blockquote")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["blockquote"]), html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<blockquote>Hello<p>there', generator.as_string())
    
    
    @istest
    def mismatched_elements_are_closed_to_satisfy_plain_path_elements(self):
        generator = _create_html_generator()
        generator.start("blockquote")
        generator.start("span")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["blockquote"]), html_paths.element(["p"])])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<blockquote><span>Hello</span><p>there', generator.as_string())
    
    
    @istest
    def fresh_element_matches_nothing(self):
        generator = _create_html_generator()
        generator.start("blockquote")
        generator.start("p")
        generator.text("Hello")
        path = html_paths.path([html_paths.element(["blockquote"]), html_paths.element(["p"], fresh=True)])
        satisfy_html_path(generator, path)
        generator.text("there")
        assert_equal('<blockquote><p>Hello</p><p>there', generator.as_string())
    
    
    @istest
    def attributes_are_generated_when_satisfying_elements(self):
        generator = _create_html_generator()
        path = html_paths.path([html_paths.element(["p"], class_names=["tip"])])
        satisfy_html_path(generator, path)
        generator.text("Hello")
        assert_equal('<p class="tip">Hello', generator.as_string())
    
    
    @istest
    def elements_do_not_match_if_class_names_do_not_match(self):
        generator = _create_html_generator()
        generator.start("p", {"class": "help"})
        generator.text("Help")
        path = html_paths.path([html_paths.element(["p"], class_names=["tip"])])
        satisfy_html_path(generator, path)
        generator.text("Tip")
        assert_equal('<p class="help">Help</p><p class="tip">Tip', generator.as_string())
    
    
    @istest
    def class_names_match_if_they_are_the_same(self):
        generator = _create_html_generator()
        generator.start("p", {"class": "tip"})
        generator.text("Help")
        path = html_paths.path([html_paths.element(["p"], class_names=["tip"])])
        satisfy_html_path(generator, path)
        generator.text("Tip")
        assert_equal('<p class="tip">HelpTip', generator.as_string())


@istest
class AppendPathTests(object):
    @istest
    def already_opened_elements_are_not_closed(self):
        generator = _create_html_generator()
        generator.start("strong")
        path = html_paths.path([html_paths.element(["em"])])
        append_html_path(generator, path)
        generator.text("Hello!")
        assert_equal('<strong><em>Hello!', generator.as_string())


def _create_html_generator():
    return HtmlGenerator(HtmlWriter)
