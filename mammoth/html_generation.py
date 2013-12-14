import cgi


class HtmlGenerator(object):
    def __init__(self):
        self._stack = []
        self._fragments = []
    
    def text(self, text):
        if text:
            self._write_all()
            self._fragments.append(_escape_html(text))
    
    def start(self, name):
        self._stack.append(_Element(name))

    def end(self):
        element = self._stack.pop()
        if element.written:
            self._fragments.append("</{0}>".format(element.name))
    
    def end_all(self):
        while self._stack:
            self.end()
    
    def self_closing(self, name, attributes=None):
        attribute_string = _generate_attribute_string(attributes)
        self._fragments.append("<{0}{1} />".format(name, attribute_string))
    
    def _write_all(self):
        for element in self._stack:
            if not element.written:
                element.written = True
                self._write_element(element)
    
    def _write_element(self, element):
        self._fragments.append("<{0}>".format(element.name))
    
    def html_string(self):
        return "".join(self._fragments)


class _Element(object):
    def __init__(self, name):
        self.name = name
        self.written = False


def _escape_html(text):
    return cgi.escape(text, quote=True)


def _generate_attribute_string(attributes):
    if attributes is None:
        return ""
    else:
        return "".join(
            ' {0}="{1}"'.format(key, value)
            for key, value in attributes.iteritems()
        )
