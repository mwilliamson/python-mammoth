from nose.tools import istest, assert_equal

from mammoth import html_paths
from mammoth.styles.parser.html_path_parser import parse_html_path
from mammoth.styles.parser.tokeniser import tokenise
from mammoth.styles.parser.token_iterator import TokenIterator


@istest
def can_read_empty_path():
    assert_equal(
        html_paths.empty,
        read_html_path("")
    )

@istest
def can_read_single_element():
    assert_equal(
        html_paths.path([html_paths.element(["p"])]),
        read_html_path("p")
    )


@istest
def can_read_choice_of_two_elements():
    assert_equal(
        html_paths.path([html_paths.element(["ul", "ol"])]),
        read_html_path("ul|ol")
    )


@istest
def can_read_choice_of_three_elements():
    assert_equal(
        html_paths.path([html_paths.element(["ul", "ol", "p"])]),
        read_html_path("ul|ol|p")
    )


@istest
def can_read_nested_elements():
    assert_equal(
        html_paths.path([html_paths.element(["ul"]), html_paths.element(["li"])]),
        read_html_path("ul > li")
    )


@istest
def can_read_class_on_element():
    assert_equal(
        html_paths.path([html_paths.element(["p"], class_names=["tip"])]),
        read_html_path("p.tip")
    )


@istest
def can_read_multiple_classes_on_element():
    assert_equal(
        html_paths.path([html_paths.element(["p"], class_names=["tip", "help"])]),
        read_html_path("p.tip.help")
    )


@istest
def can_read_when_element_must_be_fresh():
    assert_equal(
        html_paths.path([html_paths.element(["p"], fresh=True)]),
        read_html_path("p:fresh")
    )


@istest
def can_read_separator_for_elements():
    assert_equal(
        html_paths.path([html_paths.element(["p"], separator="x")]),
        read_html_path("p:separator('x')")
    )


@istest
def can_read_ignore_element():
    assert_equal(
        html_paths.ignore,
        read_html_path("!")
    )

def read_html_path(string):
    return parse_html_path(TokenIterator(tokenise(string)))
