import cgi


class HtmlGenerator(object):
    def __init__(self):
        self._fragments = []
    
    def text(self, text):
        self._fragments.append(_escape_html(text))
        
    
    def html_string(self):
        return "".join(self._fragments)


def _escape_html(text):
    return cgi.escape(text, quote=True)
