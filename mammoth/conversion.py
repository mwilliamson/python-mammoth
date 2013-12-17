import base64
import io

from . import documents, results, html_paths
from .html_generation import HtmlGenerator, satisfy_html_path


def convert_document_element_to_html(element, styles=None, convert_image=None):
    if styles is None:
        styles = []
    html_generator = HtmlGenerator()
    converter = DocumentConverter(styles, convert_image=convert_image)
    converter.convert_element_to_html(element, html_generator,)
    html_generator.end_all()
    return results.Result(html_generator.html_string(), converter.messages)


class DocumentConverter(object):
    def __init__(self, styles, convert_image):
        self.messages = []
        self._styles = styles
        self._converters = {
            documents.Document: self._convert_document,
            documents.Paragraph: self._convert_paragraph,
            documents.Run: self._convert_run,
            documents.Text: self._convert_text,
            documents.Hyperlink: self._convert_hyperlink,
            documents.Tab: self._convert_tab,
            documents.Image: convert_image or self._convert_image,
        }


    def convert_element_to_html(self, element, html_generator):
        self._converters[type(element)](element, html_generator)


    def _convert_document(self, document, html_generator):
        self._convert_elements_to_html(document.children, html_generator)


    def _convert_paragraph(self, paragraph, html_generator):
        html_path = self._find_html_path_for_paragraph(paragraph)
        satisfy_html_path(html_generator, html_path)
        self._convert_elements_to_html(paragraph.children, html_generator)


    def _convert_run(self, run, html_generator):
        run_generator = HtmlGenerator()
        html_path = self._find_html_path_for_run(run)
        if html_path:
            satisfy_html_path(run_generator, html_path)
        if run.is_bold:
            run_generator.start("strong")
        if run.is_italic:
            run_generator.start("em")
        self._convert_elements_to_html(run.children, run_generator)
        run_generator.end_all()
        html_generator.append(run_generator)


    def _convert_text(self, text, html_generator):
        html_generator.text(text.value)
    
    
    def _convert_hyperlink(self, hyperlink, html_generator):
        html_generator.start("a", {"href": hyperlink.href})
        self._convert_elements_to_html(hyperlink.children, html_generator)
        html_generator.end()
    
    
    def _convert_tab(self, tab, html_generator):
        html_generator.text("\t")
    
    
    def _convert_image(self, image, html_generator):
        with image.open() as image_bytes:
            encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
        
        attributes = {
            "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
        }
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        html_generator.self_closing("img", attributes)


    def _convert_elements_to_html(self, elements, html_generator):
        for element in elements:
            self.convert_element_to_html(element, html_generator)


    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element("p", fresh=True)])
        return self._find_html_path(paragraph, "paragraph", default)
    
    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", default=None)
        
    
    def _find_html_path(self, element, element_type, default):
        for style in self._styles:
            document_matcher = style.document_matcher
            if _document_matcher_matches(document_matcher, element, element_type):
                return style.html_path
        
        if element.style_name is not None:
            self.messages.append(results.warning("Unrecognised {0} style: {1}".format(element_type, element.style_name)))
        
        return default
        

def _document_matcher_matches(matcher, element, element_type):
    return (
        matcher.element_type == element_type and (
            matcher.style_name is None or
            matcher.style_name == element.style_name
        ) and (
            element_type != "paragraph" or
            matcher.numbering is None or
            matcher.numbering == element.numbering
        )
    )
