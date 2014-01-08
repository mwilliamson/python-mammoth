from .results import Result
from . import docx, conversion, options


def convert_to_html(fileobj, transform_document=None, **kwargs):
    if transform_document is None:
        transform_document = lambda x: x
    return docx.read(fileobj).map(transform_document).bind(lambda document: 
        conversion.convert_document_element_to_html(
            document,
            **options.read_options(kwargs)
        )
    )
