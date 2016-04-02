from . import html


def img_element(func):
    def convert_image(image):
        attributes = func(image).copy()
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        return [html.self_closing_element("img", attributes)]
    
    return convert_image

# Undocumented, but retained for backwards-compatibility with 0.3.x
inline = img_element
