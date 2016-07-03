from parsimonious.grammar import Grammar

from .. import document_matchers, documents


def read_document_matcher(string):
    root_node = _grammar.parse(string)
    return read_document_matcher_node(root_node)


def read_document_matcher_node(root_node):
    element_node = root_node.children[0]
    if element_node.expr_name == "paragraph":
        return _read_paragraph_node(element_node)
    elif element_node.expr_name == "run":
        return _read_run_node(element_node)
    elif element_node.expr_name == "bold":
        return document_matchers.bold
    elif element_node.expr_name == "italic":
        return document_matchers.italic
    elif element_node.expr_name == "underline":
        return document_matchers.underline
    elif element_node.expr_name == "strikethrough":
        return document_matchers.strikethrough
    elif element_node.expr_name == "comment_reference":
        return document_matchers.comment_reference
    

def _read_paragraph_node(paragraph_node):
    style_id = _read_style_id_node(paragraph_node.children[1])
    style_name = _read_style_name_node(paragraph_node.children[2])
    numbering = _read_list_node(paragraph_node.children[3])
    return document_matchers.paragraph(style_id=style_id, style_name=style_name, numbering=numbering)
    

def _read_run_node(run_node):
    style_id = _read_style_id_node(run_node.children[1])
    style_name = _read_style_name_node(run_node.children[2])
    return document_matchers.run(style_id=style_id, style_name=style_name)


def _read_style_id_node(style_id_node):
    if style_id_node.children:
        return style_id_node.children[0].children[1].text
    else:
        return None


def _read_style_name_node(style_name_node):
    if style_name_node.children:
        return style_name_node.children[0].children[1].text
    else:
        return None


def _read_list_node(list_node):
    if list_node.children:
        return documents.numbering_level(
            int(list_node.children[0].children[3].text) - 1,
            is_ordered=list_node.children[0].children[1].text == "ordered-list",
        )
    else:
        return None

grammar_text = r"""
document_matcher = paragraph / run / underline / strikethrough / bold / italic / comment_reference

underline = "u"

strikethrough = "strike"

bold = "b"

italic = "i"

comment_reference = "comment-reference"

paragraph = "p" style_id? style_name_specifier? list?

run = "r" style_id? style_name_specifier?

style_id = "." style_identifier

style_identifier = ~"[A-Z0-9]*"i

style_name_specifier = "[style-name='" style_name "']"

style_name = ~"[^']+"

list = ":" list_type "(" ~"[0-9]+" ")"

list_type = "ordered-list" / "unordered-list"
"""
_grammar = Grammar(grammar_text)

