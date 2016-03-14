from . import html


def inline(func):
    def convert_image(image):
        attributes = func(image).copy()
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        return [html.self_closing_element("img", attributes)]
    
    return convert_image
