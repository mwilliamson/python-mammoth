from .html_generation import HtmlGenerator
from .documents import Image


#:type ImageConverter = (Image, HtmlGenerator -> none)
ImageConverter = None

#:: (Image -> dict[str, str]) -> ImageConverter
def inline(func):
    #:: ImageConverter
    def convert_image(image, html_generator):
        attributes = func(image).copy()
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        html_generator.self_closing("img", attributes)
    
    return convert_image
