import io

from hamcrest import assert_that, contains, has_properties
from nose.tools import istest

import mammoth


@istest
def inline_is_available_as_alias_of_img_element():
    assert mammoth.images.inline is mammoth.images.img_element


@istest
def data_uri_encodes_images_in_base64():
    image_bytes = b"abc"
    image = mammoth.documents.Image(
        alt_text=None,
        content_type="image/jpeg",
        size=mammoth.documents.Size(width="800", height="600"),
        open=lambda: io.BytesIO(image_bytes),
    )
    
    result = mammoth.images.data_uri(image)
    
    assert_that(result, contains(
        has_properties(attributes={
            "src": "data:image/jpeg;base64,YWJj",
            "width": "800",
            "height": "600",
        }),
    ))
