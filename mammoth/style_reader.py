from parsimonious.grammar import Grammar

from . import html_paths


def read_html_path(string):
    path_node = _grammar.parse(string)
    return _read_path_node(path_node)
    


def _read_path_node(path_node):
    elements = [
        _read_element_node(child)
        for child in _repeated_children_with_separator(path_node, has_whitespace=True)
    ]
    return html_paths.path(elements)


def _read_element_node(node):
    tag_names = _read_tag_names_node(node.children[0])
    class_names = _read_class_names_node(node.children[1])
    return html_paths.element(tag_names, class_names=class_names)


def _read_tag_names_node(node):
    return [
        child.text
        for child in _repeated_children_with_separator(node, has_whitespace=False)
    ]


def _read_class_names_node(class_names_node):
    return [
        _read_class_name_node(node)
        for node in class_names_node.children
    ]


def _read_class_name_node(node):
    return node.children[1].text


def _repeated_children_with_separator(node, has_whitespace):
    yield node.children[0]
    
    if has_whitespace:
        sequence_node_index = 2
    else:
        sequence_node_index = 1
    
    sequence_node = node.children[sequence_node_index]
    for child in sequence_node.children:
        yield child.children[sequence_node_index]


_grammar = Grammar(r"""

path = element whitespace* (">" whitespace* element)*

element = tag_names class_name*

class_name = "." identifier

tag_names = identifier ("|" identifier)*

identifier = ~"[A-Z0-9]*"i

whitespace = ~"\s"*

""")
