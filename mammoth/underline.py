from .html_generation import HtmlGenerator

#:type UnderlineConverter = (HtmlGenerator -> none)
UnderlineConverter = None

#:: str -> UnderlineConverter
def element(name):
    #:: HtmlGenerator -> none
    def convert_underline(html_generator):
        html_generator.start(name)
        
    return convert_underline
