from .results import Result
from . import docx, conversion


def convert_to_html(fileobj):
    document = docx.read(fileobj).value
    html = conversion.convert_document_element_to_html(document)
    return Result(html, [])
