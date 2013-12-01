from .results import Result
from . import docx, documents


def convert_to_html(fileobj):
    document = docx.read(fileobj).value
    html = _convert_element_to_html(document)
    return Result(html, [])


def _convert_element_to_html(element):
    return _converters[type(element)](element)
    

_converters = {}


def converter(element_type):
    def add(func):
        _converters[element_type] = func
        
    return add


@converter(documents.Document)
def convert_document(document):
    return _convert_elements_to_html(document.children)


@converter(documents.Paragraph)
def convert_paragraph(paragraph):
    return "<p>{0}</p>".format(_convert_elements_to_html(paragraph.children))


@converter(documents.Run)
def convert_run(run):
    return _convert_elements_to_html(run.children)


@converter(documents.Text)
def convert_text(text):
    return text.value


def _convert_elements_to_html(elements):
    return "".join(map(_convert_element_to_html, elements))
