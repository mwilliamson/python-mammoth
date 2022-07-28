import io
import base64

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
        open=lambda: io.BytesIO(image_bytes),
    )
    
    result = mammoth.images.data_uri(image)
    
    assert_that(result, contains(
        has_properties(attributes={"src": "data:image/jpeg;base64,YWJj"}),
    ))


@istest
def modifying_alt_text_during_conversion():
    def convert_image(image):
        with image.open() as image_bytes:
            encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
            alt_text = "alt text output test"
        
        return {
            "alt": alt_text,
            "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
        }

    image_bytes = b"abc"
    image = mammoth.documents.Image(
        alt_text=None,
        content_type="image/jpeg",
        open=lambda: io.BytesIO(image_bytes),
    )
    
    result = mammoth.images.img_element(convert_image)(image)
    
    assert_that(
        result, 
        contains(
            has_properties(
                attributes={
                    "alt": "alt text output test",
                    "src": "data:image/jpeg;base64,YWJj"
                    }
                ),
        )
    )

