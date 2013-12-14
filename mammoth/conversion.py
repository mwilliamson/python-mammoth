from . import documents, results, html_paths
from .html_generation import HtmlGenerator, satisfy_html_path


def convert_document_element_to_html(element, styles=None):
    if styles is None:
        styles = []
    html_generator = HtmlGenerator()
    converter = DocumentConverter(styles)
    converter.convert_element_to_html(element, html_generator)
    html_generator.end_all()
    return results.Result(html_generator.html_string(), converter.messages)


class DocumentConverter(object):
    def __init__(self, styles):
        self.messages = []
        self._styles = styles
        self._converters = {
            documents.Document: self._convert_document,
            documents.Paragraph: self._convert_paragraph,
            documents.Run: self._convert_run,
            documents.Text: self._convert_text,
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


    def _convert_elements_to_html(self, elements, html_generator):
        for element in elements:
            self.convert_element_to_html(element, html_generator)


    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element("p")])
        return self._find_html_path(paragraph, "paragraph", default)
    
    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", default=None)
        
    
    def _find_html_path(self, element, element_type, default):
        for style in self._styles:
            document_matcher = style.document_matcher
            if document_matcher.element_type == element_type and (
                    document_matcher.style_name is None or
                    document_matcher.style_name == element.style_name):
                return style.html_path
        
        if element.style_name is not None:
            self.messages.append(results.warning("Unrecognised {0} style: {1}".format(element_type, element.style_name)))
        
        return default
        
