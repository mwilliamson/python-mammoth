from parsimonious.grammar import Grammar

from .. import document_matchers


def read_document_matcher(string):
    paragraph_node = _grammar.parse(string)
    return _read_paragraph_node(paragraph_node)
    


def _read_paragraph_node(paragraph_node):
    return document_matchers.paragraph()


_grammar = Grammar(r"""
paragraph = "p"
""")

