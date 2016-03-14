from nose.tools import istest, assert_equal

from mammoth import html


@istest
def collapsing_does_nothing_to_single_text_node():
    assert_equal(
        html.collapse([html.text("Bluebells")]),
        [html.text("Bluebells")])


@istest
def consecutive_fresh_elements_are_not_collapsed():
    assert_equal(
        html.collapse([html.element("p"), html.element("p")]),
        [html.element("p"), html.element("p")])


@istest
def consecutive_collapsible_elements_are_collapsed_if_they_have_the_same_tag_and_attributes():
    assert_equal(
        [html.collapsible_element("p", {}, [html.text("One"), html.text("Two")])],
        html.collapse([
            html.collapsible_element("p", {}, [html.text("One")]),
            html.collapsible_element("p", {}, [html.text("Two")])
        ]))
        

@istest
def elements_with_different_tag_names_are_not_collapsed():
    assert_equal(
        [
            html.collapsible_element("p", {}, [html.text("One")]),
            html.collapsible_element("div", {}, [html.text("Two")])
        ],
        
        html.collapse([
            html.collapsible_element("p", {}, [html.text("One")]),
            html.collapsible_element("div", {}, [html.text("Two")])
        ]))
        

@istest
def elements_with_different_attributes_are_not_collapsed():
    assert_equal(
        [
            html.collapsible_element("p", {"id": "a"}, [html.text("One")]),
            html.collapsible_element("p", {}, [html.text("Two")])
        ],
        
        html.collapse([
            html.collapsible_element("p", {"id": "a"}, [html.text("One")]),
            html.collapsible_element("p", {}, [html.text("Two")])
        ]))


@istest
def children_of_collapsed_element_can_collapse_with_children_of_previous_element():
    assert_equal(
        [
            html.collapsible_element("blockquote", {}, [
                html.collapsible_element("p", {}, [
                    html.text("One"),
                    html.text("Two")
                ])
            ]),
        ],
        
        html.collapse([
            html.collapsible_element("blockquote", {}, [
                html.collapsible_element("p", {}, [html.text("One")])
            ]),
            html.collapsible_element("blockquote", {}, [
                html.collapsible_element("p", {}, [html.text("Two")])
            ]),
        ]))


@istest
def collapsible_element_can_collapse_into_previous_fresh_element():
    assert_equal(
        [html.element("p", {}, [html.text("One"), html.text("Two")])],
        html.collapse([
            html.element("p", {}, [html.text("One")]),
            html.collapsible_element("p", {}, [html.text("Two")])
        ]))


@istest
def element_with_choice_of_tag_names_can_collapse_into_previous_element_if_it_has_one_of_those_tag_names_as_its_main_tag_name():
    assert_equal(
        [html.collapsible_element(["ol"])],
        html.collapse([
            html.collapsible_element("ol"),
            html.collapsible_element(["ul", "ol"])
        ]))

    assert_equal(
        [
            html.collapsible_element(["ul", "ol"]),
            html.collapsible_element("ol")
        ],
        html.collapse([
            html.collapsible_element(["ul", "ol"]),
            html.collapsible_element("ol")
        ]))
