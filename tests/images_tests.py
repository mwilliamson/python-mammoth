import io

from precisely import assert_that, equal_to, has_attrs, is_sequence

import mammoth


def test_inline_is_available_as_alias_of_img_element():
    assert mammoth.images.inline is mammoth.images.img_element


def test_data_uri_encodes_images_in_base64():
    image_bytes = b"abc"
    image = mammoth.documents.Image(
        alt_text=None,
        content_type="image/jpeg",
        open=lambda: io.BytesIO(image_bytes),
    )

    result = mammoth.images.data_uri(image)

    assert_that(result, is_sequence(
        has_attrs(attributes={"src": "data:image/jpeg;base64,YWJj"}),
    ))


class ImgElementTests:
    def test_when_element_does_not_have_alt_text_then_alt_attribute_is_not_set(self):
        image_bytes = b"abc"
        image = mammoth.documents.Image(
            alt_text=None,
            content_type="image/jpeg",
            open=lambda: io.BytesIO(image_bytes),
        )

        @mammoth.images.img_element
        def convert_image(image):
            return {"src": "<src>"}

        result = convert_image(image)

        assert_that(result, is_sequence(
            has_attrs(attributes={"src": "<src>"}),
        ))

    def test_when_element_se_alt_text_then_alt_attribute_is_set(self):
        image_bytes = b"abc"
        image = mammoth.documents.Image(
            alt_text="<alt>",
            content_type="image/jpeg",
            open=lambda: io.BytesIO(image_bytes),
        )

        @mammoth.images.img_element
        def convert_image(image):
            return {"src": "<src>"}

        result = convert_image(image)

        assert_that(result, is_sequence(
            has_attrs(attributes={"alt": "<alt>", "src": "<src>"}),
        ))

    def test_image_alt_text_can_be_overridden_by_alt_attribute_returned_from_function(self):
        image_bytes = b"abc"
        image = mammoth.documents.Image(
            alt_text="<alt>",
            content_type="image/jpeg",
            open=lambda: io.BytesIO(image_bytes),
        )

        @mammoth.images.img_element
        def convert_image(image):
            return {"alt": "<alt override>", "src": "<src>"}

        result = convert_image(image)

        assert_that(result, is_sequence(
            has_attrs(attributes={"alt": "<alt override>", "src": "<src>"}),
        ))


class ImageFilenameExtensionTests:
    def test_extension_is_derived_from_subtype_of_content_type(self):
        image = self._image_with_content_type("image/gif")

        result = mammoth.images.image_filename_extension(image)

        assert_that(result, equal_to("gif"))

    def test_data_after_second_slash_is_ignored(self):
        image = self._image_with_content_type("image/gif/jpeg")

        result = mammoth.images.image_filename_extension(image)

        assert_that(result, equal_to("gif"))

    def test_backslashes_are_treated_as_forward_slashes(self):
        image = self._image_with_content_type("image\\gif\\..\\")

        result = mammoth.images.image_filename_extension(image)

        assert_that(result, equal_to("gif"))

    def test_when_there_is_no_subtype_then_none_is_returned(self):
        image = self._image_with_content_type("image")

        result = mammoth.images.image_filename_extension(image)

        assert_that(result, equal_to(None))

    def _image_with_content_type(self, content_type):
        return mammoth.documents.Image(alt_text="", content_type=content_type, open=None)
