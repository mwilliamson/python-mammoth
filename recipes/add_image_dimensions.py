from __future__ import division
import base64

# An example of how to add the source file dimensions to the img tag
# mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(add_dimensions))

def add_dimensions(image):
    # There are 914400 EMUs per inch and MS Word seems to work at 72 DPI 
    def getPixels( emus, dpi ):
        emu = 914400
        if dpi is None: dpi = 72
        return str(int((emus/emu)*dpi))

    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")

    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src),
        "width" : getPixels( image.width,  dpi=72 ),
        "height": getPixels( image.height, dpi=72 )
    }