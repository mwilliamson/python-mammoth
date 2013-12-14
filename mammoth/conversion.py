from .results import Result
from . import documents


def convert_document_element_to_html(element):
    return _converters[type(element)](element)
    

_converters = {}


def _converter(element_type):
    def add(func):
        _converters[element_type] = func
        
    return add


@_converter(documents.Document)
def convert_document(document):
    return _convert_elements_to_html(document.children)


@_converter(documents.Paragraph)
def convert_paragraph(paragraph):
    return "<p>{0}</p>".format(_convert_elements_to_html(paragraph.children))


@_converter(documents.Run)
def convert_run(run):
    return _convert_elements_to_html(run.children)


@_converter(documents.Text)
def convert_text(text):
    return text.value


def _convert_elements_to_html(elements):
    return "".join(map(convert_document_element_to_html, elements))

