from .documents import Image
from .html_generation import HtmlGenerator


#:type ImageConverter = (Image, HtmlGenerator -> none)
ImageConverter = None

#:: (Image -> dict[str, str]) -> ImageConverter
def inline(func):
    #:: Image, HtmlGenerator -> none
    def convert_image(image, html_generator):
        attributes = func(image).copy()
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        html_generator.self_closing("img", attributes)
    
    return convert_image
