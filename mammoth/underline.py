from .html_generation import HtmlGenerator

#:: str -> (HtmlGenerator -> none)
def element(name):
    #:: HtmlGenerator -> none
    def convert_underline(html_generator):
        html_generator.start(name)
        
    return convert_underline
