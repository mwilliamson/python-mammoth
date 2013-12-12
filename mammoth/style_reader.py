from parsimonious.grammar import Grammar

from . import html_paths


def read_html_path(string):
    root_node = _grammar.parse(string)
    tag_names = [root_node.children[0].text]
    
    for choice_node in root_node.children[1].children:
        tag_names.append(choice_node.children[1].text)
    
    return html_paths.path([html_paths.element(tag_names)])


_grammar = Grammar("""

tag_names = identifier ("|" identifier)*

identifier = ~"[A-Z0-9]*"i

""")
