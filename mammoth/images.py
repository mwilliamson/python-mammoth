from .documents import Image
from .html_generation import HtmlGenerator


#:: (Image -> dict[str, str]) -> (Image, HtmlGenerator -> none)
def inline(func):
    #:: Image, HtmlGenerator -> none
    def convert_image(image, html_generator):
        attributes = func(image).copy()
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        html_generator.self_closing("img", attributes)
    
    return convert_image
