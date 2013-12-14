from .results import Result
from . import docx, conversion, style_reader


def convert_to_html(fileobj):
    return docx.read(fileobj).bind(lambda document: 
        conversion.convert_document_element_to_html(document, styles=_create_default_styles())
    )


def _create_default_styles():
    lines = filter(None, map(lambda line: line.strip(), _default_styles.split("\n")))
    return map(style_reader.read_style, lines)

_default_styles = """
p:unordered-list(1) => ul > li:fresh
"""
