from parsimonious.grammar import Grammar

from .. import document_matchers, documents


def read_document_matcher(string):
    root_node = _grammar.parse(string)
    element_node = root_node.children[0]
    if element_node.expr_name == "paragraph":
        return _read_paragraph_node(element_node)
    elif element_node.expr_name == "run":
        return _read_run_node(element_node)
    

def _read_paragraph_node(paragraph_node):
    style_name = _read_style_node(paragraph_node.children[1])
    numbering = _read_list_node(paragraph_node.children[2])
    return document_matchers.paragraph(style_name=style_name, numbering=numbering)
    

def _read_run_node(run_node):
    style_name = _read_style_node(run_node.children[1])
    return document_matchers.run(style_name=style_name)


def _read_style_node(style_node):
    if style_node.children:
        return style_node.children[0].children[1].text
    else:
        return None


def _read_list_node(list_node):
    if list_node.children:
        return documents.NumberingLevel(
            int(list_node.children[0].children[1].text),
            is_ordered=True,
        )
    else:
        return None


_grammar = Grammar(r"""
matcher = paragraph / run

paragraph = "p" style_name? list?

run = "r" style_name?

style_name = "." style_identifier

style_identifier = ~"[A-Z0-9]*"i

list = ":ordered-list(" ~"[0-9]+" ")"
""")

