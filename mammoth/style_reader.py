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
    return html_paths.element(_read_tag_names_node(node))


def _read_tag_names_node(node):
    return [
        child.text
        for child in _repeated_children_with_separator(node, has_whitespace=False)
    ]


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

element = tag_names

tag_names = identifier ("|" identifier)*

identifier = ~"[A-Z0-9]*"i

whitespace = ~"\s"*

""")
