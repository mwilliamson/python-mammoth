from .results import Result
from . import docx, conversion, style_reader, lists


def convert_to_html(fileobj, styles=None, convert_image=None):
    if styles is None:
        styles = _default_styles
    
    return docx.read(fileobj).bind(lambda document: 
        conversion.convert_document_element_to_html(document, styles=_read_styles(styles), convert_image=convert_image)
    )


def _read_styles(style_text):
    lines = filter(None, map(lambda line: line.strip(), style_text.split("\n")))
    return lists.map(style_reader.read_style, lines)
    


_default_styles = """
p.Heading1 => h1:fresh
p.Heading2 => h2:fresh
p.Heading3 => h3:fresh
p.Heading4 => h4:fresh
p:unordered-list(1) => ul > li:fresh
p:unordered-list(2) => ul|ol > li > ul > li:fresh
p:unordered-list(3) => ul|ol > li > ul|ol > li > ul > li:fresh
p:unordered-list(4) => ul|ol > li > ul|ol > li > ul|ol > li > ul > li:fresh
p:unordered-list(5) => ul|ol > li > ul|ol > li > ul|ol > li > ul|ol > li > ul > li:fresh
p:ordered-list(1) => ol > li:fresh
p:ordered-list(2) => ul|ol > li > ol > li:fresh
p:ordered-list(3) => ul|ol > li > ul|ol > li > ol > li:fresh
p:ordered-list(4) => ul|ol > li > ul|ol > li > ul|ol > li > ol > li:fresh
p:ordered-list(5) => ul|ol > li > ul|ol > li > ul|ol > li > ul|ol > li > ol > li:fresh
"""
