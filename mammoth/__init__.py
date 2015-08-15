from . import docx, conversion, options, images, underline
from .raw_text import extract_raw_text_from_element

__all__ = ["convert_to_html", "extract_raw_text", "images", "underline"]


def convert_to_html(*args, **kwargs):
    return convert(*args, output_format="html", **kwargs)


def convert_to_markdown(*args, **kwargs):
    return convert(*args, output_format="markdown", **kwargs)


def convert(fileobj, transform_document=None, id_prefix=None, **kwargs):
    if transform_document is None:
        transform_document = lambda x: x
    return options.read_options(kwargs).bind(lambda convert_options:
        docx.read(fileobj).map(transform_document).bind(lambda document:
            conversion.convert_document_element_to_html(
                document,
                id_prefix=id_prefix,
                **convert_options
            )
        )
    )
    

def extract_raw_text(fileobj):
    return docx.read(fileobj).map(extract_raw_text_from_element)
