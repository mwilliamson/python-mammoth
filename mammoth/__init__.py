from .results import Result
from . import docx, conversion


def convert_to_html(fileobj):
    return docx.read(fileobj).bind(conversion.convert_document_element_to_html)
