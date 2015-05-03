from __future__ import unicode_literals

import cgi


class HtmlWriter(object):
    #:: Self -> none
    def __init__(self):
        #:: list[str]
        self._fragments = []
    
    #:: Self, str -> none
    def text(self, text):
        self._fragments.append(_escape_html(text))
    
    #:: Self, str, ?attributes: dict[str, str] -> none
    def start(self, name, attributes=None):
        attribute_string = _generate_attribute_string(attributes)
        self._fragments.append("<{0}{1}>".format(name, attribute_string))

    #:: Self, str -> none
    def end(self, name):
        self._fragments.append("</{0}>".format(name))
    
    #:: Self, str, ?attributes: dict[str, str] | none -> none
    def self_closing(self, name, attributes=None):
        attribute_string = _generate_attribute_string(attributes)
        self._fragments.append("<{0}{1} />".format(name, attribute_string))
    
    #:: Self, str -> none
    def append(self, html):
        self._fragments.append(html)
    
    #:: Self -> str
    def as_string(self):
        return "".join(self._fragments)


#:: str -> str
def _escape_html(text):
    return cgi.escape(text, quote=True)


#:: dict[str, str] | none -> str
def _generate_attribute_string(attributes):
    if attributes is None:
        return ""
    else:
        return "".join(
            ' {0}="{1}"'.format(key, _escape_html(attributes[key]))
            for key in sorted(attributes)
        )
