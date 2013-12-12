from parsimonious.grammar import Grammar

from .. import document_matchers


def read_document_matcher(string):
    paragraph_node = _grammar.parse(string)
    return _read_paragraph_node(paragraph_node)
    


def _read_paragraph_node(paragraph_node):
    style_name = _read_style_node(paragraph_node.children[1])
    return document_matchers.paragraph(style_name=style_name)


def _read_style_node(style_node):
    if style_node.children:
        return style_node.children[0].children[1].text
    else:
        return None


_grammar = Grammar(r"""
paragraph = "p" style_name?

style_name = "." style_identifier

style_identifier = ~"[A-Z0-9]*"i
""")

