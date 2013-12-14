import cgi


class HtmlGenerator(object):
    def __init__(self):
        self._stack = []
        self._fragments = []
    
    def text(self, text):
        self._fragments.append(_escape_html(text))
    
    def start(self, name):
        self._stack.append(_Element(name))
        self._fragments.append("<{0}>".format(name))

    def end(self):
        element = self._stack.pop()
        self._fragments.append("</{0}>".format(element.name))
    
    def end_all(self):
        while self._stack:
            self.end()
    
    def html_string(self):
        return "".join(self._fragments)


class _Element(object):
    def __init__(self, name):
        self.name = name


def _escape_html(text):
    return cgi.escape(text, quote=True)
