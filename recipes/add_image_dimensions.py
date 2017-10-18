from __future__ import division
import re
import base64

# An example of how to add the source file dimensions to the img tag
# mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(add_dimensions))

def add_dimensions(image):
    # There are 914400 EMUs per inch and MS Word seems to work at 72 DPI
    emu = 914400
    dpi = 72

    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")

    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src),
        "width" : str(int((float(re.findall('\d+', image.content_width  )[0])/emu)*dpi)),
        "height": str(int((float(re.findall('\d+', image.content_height )[0])/emu)*dpi))
    }