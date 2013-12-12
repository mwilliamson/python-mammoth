from nose.tools import istest, assert_equal

from mammoth import html_paths
from mammoth.style_reader import read_html_path


@istest
class ReadHtmlPathTests(object):
    @istest
    def can_read_single_element(self):
        assert_equal(
            html_paths.path([html_paths.element(["p"])]),
            read_html_path("p")
        )
    
    @istest
    def can_read_choice_of_two_elements(self):
        assert_equal(
            html_paths.path([html_paths.element(["ul", "ol"])]),
            read_html_path("ul|ol")
        )

    
    @istest
    def can_read_choice_of_three_elements(self):
        assert_equal(
            html_paths.path([html_paths.element(["ul", "ol", "p"])]),
            read_html_path("ul|ol|p")
        )

    
    @istest
    def can_read_nested_elements(self):
        assert_equal(
            html_paths.path([html_paths.element(["ul"]), html_paths.element(["li"])]),
            read_html_path("ul > li")
        )

    
    @istest
    def can_read_class_on_element(self):
        assert_equal(
            html_paths.path([html_paths.element(["p"], class_names=["tip"])]),
            read_html_path("p.tip")
        )

    
    @istest
    def can_read_multiple_classes_on_element(self):
        assert_equal(
            html_paths.path([html_paths.element(["p"], class_names=["tip", "help"])]),
            read_html_path("p.tip.help")
        )

    
    @istest
    def can_read_when_element_must_be_fresh(self):
        assert_equal(
            html_paths.path([html_paths.element(["p"], fresh=True)]),
            read_html_path("p:fresh")
        )
