import base64

from . import html
from .attributes import compose_attributes


def img_element(func):
    def convert_image(image):
        attributes = compose_attributes(image, func(image))
        return [html.element("img", attributes)]

    return convert_image

# Undocumented, but retained for backwards-compatibility with 0.3.x
inline = img_element


@img_element
def data_uri(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")

    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }
