from .results import Result
from . import docx, conversion, options


def convert_to_html(fileobj, **kwargs):
    return docx.read(fileobj).bind(lambda document: 
        conversion.convert_document_element_to_html(
            document,
            **options.read_options(kwargs)
        )
    )
