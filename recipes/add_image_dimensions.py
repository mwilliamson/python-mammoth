import base64
import io
from PIL import Image

# An example of how to add the source file dimensions to the img tag
# mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(add_dimensions))

def add_dimensions(image):

    with image.open() as image_source:
        image_bytes = image_source.read()
        encoded_src = base64.b64encode(image_bytes).decode("ascii")
        img_size = Image.open(io.BytesIO(image_bytes)).size

    img = {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }

    if img_size:
        img["width"]  = str(img_size[0]);
        img["height"] = str(img_size[1]);

    return img