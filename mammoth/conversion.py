import base64

from . import documents, results, html_paths, images
from .html_generation import HtmlGenerator, satisfy_html_path


def convert_document_element_to_html(element, style_map=None, convert_image=None):
    if style_map is None:
        style_map = []
    html_generator = HtmlGenerator()
    converter = DocumentConverter(style_map, convert_image=convert_image)
    converter.convert_element_to_html(element, html_generator,)
    html_generator.end_all()
    return results.Result(html_generator.html_string(), converter.messages)


class DocumentConverter(object):
    def __init__(self, style_map, convert_image):
        self.messages = []
        self._style_map = style_map
        self._converters = {
            documents.Document: self._convert_document,
            documents.Paragraph: self._convert_paragraph,
            documents.Run: self._convert_run,
            documents.Text: self._convert_text,
            documents.Hyperlink: self._convert_hyperlink,
            documents.Tab: self._convert_tab,
            documents.Table: self._convert_table,
            documents.TableRow: self._convert_table_row,
            documents.TableCell: self._convert_table_cell,
            documents.Image: convert_image or images.inline(self._convert_image),
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
    
    
    def _convert_table(self, table, html_generator):
        html_generator.end_all()
        html_generator.start("table")
        self._convert_elements_to_html(table.children, html_generator)
        html_generator.end()
    
    
    def _convert_table_row(self, table_row, html_generator):
        html_generator.start("tr")
        self._convert_elements_to_html(table_row.children, html_generator)
        html_generator.end()
    
    
    def _convert_table_cell(self, table_cell, html_generator):
        html_generator.start("td", always_write=True)
        for child in table_cell.children:
            child_generator = HtmlGenerator()
            self.convert_element_to_html(child, child_generator)
            child_generator.end_all()
            html_generator.append(child_generator)
            
        html_generator.end()
    
    
    def _convert_image(self, image):
        with image.open() as image_bytes:
            encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
        
        return {
            "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
        }


    def _convert_elements_to_html(self, elements, html_generator):
        for element in elements:
            self.convert_element_to_html(element, html_generator)


    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element("p", fresh=True)])
        return self._find_html_path(paragraph, "paragraph", default)
    
    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", default=None)
        
    
    def _find_html_path(self, element, element_type, default):
        for style in self._style_map:
            document_matcher = style.document_matcher
            if _document_matcher_matches(document_matcher, element, element_type):
                return style.html_path
        
        if element.style_id is not None:
            self.messages.append(results.warning(
                "Unrecognised {0} style: {1} (Style ID: {2})".format(
                    element_type, element.style_name, element.style_id)
            ))
        
        return default
        

def _document_matcher_matches(matcher, element, element_type):
    return (
        matcher.element_type == element_type and (
            matcher.style_id is None or
            matcher.style_id == element.style_id
        ) and (
            matcher.style_name is None or
            matcher.style_name == element.style_name
        ) and (
            element_type != "paragraph" or
            matcher.numbering is None or
            matcher.numbering == element.numbering
        )
    )
