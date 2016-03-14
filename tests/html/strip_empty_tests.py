from nose.tools import istest, assert_equal

from mammoth import html


@istest
def text_nodes_with_text_are_not_stripped():
    assert_equal(
        [html.text("H")],
        html.strip_empty([html.text("H")]))


@istest
def empty_text_nodes_are_stripped():
    assert_equal(
        [],
        html.strip_empty([html.text("")]))


@istest
def elements_with_non_empty_children_are_not_stripped():
    assert_equal(
        [html.element("p", {}, [html.text("H")])],
        html.strip_empty([html.element("p", {}, [html.text("H")])]))


@istest
def elements_with_no_children_are_stripped():
    assert_equal(
        [],
        html.strip_empty([html.element("p")]))


@istest
def elements_with_only_empty_children_are_stripped():
    assert_equal(
        [],
        html.strip_empty([html.element("p", {}, [html.text("")])]))


@istest
def empty_children_are_removed():
    assert_equal(
        html.strip_empty([html.element("ul", {}, [
            html.element("li", {}, [html.text("")]),
            html.element("li", {}, [html.text("H")]),
        ])]),
        
        [html.element("ul", {}, [
            html.element("li", {}, [html.text("H")])
        ])])


@istest
def self_closing_elements_are_never_empty():
    assert_equal(
        [html.self_closing_element("br")],
        html.strip_empty([html.self_closing_element("br")]))


@istest
def force_writes_are_never_empty():
    assert_equal(
        [html.force_write],
        html.strip_empty([html.force_write]))
