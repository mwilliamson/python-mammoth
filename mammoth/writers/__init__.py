from .html import HtmlWriter
#~ from .markdown import MarkdownWriter


#:structural-type Writer:
#:  start: str, ?attributes: dict[str, str] -> none
#:  end: str -> none
#:  self_closing: str, ?attributes: dict[str, str] | none -> none
#:  text: str -> none
#:  append: str -> none
#:  as_string: -> str
Writer = None


#:: ?str -> Writer
def writer(output_format=None):
    if output_format is None:
        output_format = "html"
    
    return _writers[output_format]()


#:: -> list[str]
def formats():
    return list(_writers.keys())


_writers = {
    "html": HtmlWriter,
    #~ "markdown": MarkdownWriter,
}
