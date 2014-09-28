from __future__ import unicode_literals

import cgi
import sys

from .html_paths import HtmlPath, HtmlPathElement


class HtmlGenerator(object):
    #:: Self -> none
    def __init__(self):
        self._stack = []
        self._fragments = []
    
    #:: Self, str -> none
    def text(self, text):
        if text:
            self._write_all()
            self._fragments.append(_escape_html(text))
    
    #:: Self, str, dict[str, str], bool -> none
    def start(self, name, attributes=None, always_write=False):
        self._stack.append(_Element(name, attributes))
        
        if always_write:
            self._write_all()

    #:: Self -> none
    def end(self):
        element = self._stack.pop()
        if element.written:
            self._fragments.append("</{0}>".format(element.name))
    
    #:: Self -> none
    def end_all(self):
        while self._stack:
            self.end()
    
    #:: Self, str, dict[str, str] -> none
    def self_closing(self, name, attributes=None):
        attribute_string = _generate_attribute_string(attributes)
        self._fragments.append("<{0}{1} />".format(name, attribute_string))
    
    #:: Self -> none
    def _write_all(self):
        for element in self._stack:
            if not element.written:
                element.written = True
                self._write_element(element)
    
    #:: Self, _Element -> none
    def _write_element(self, element):
        attribute_string = _generate_attribute_string(element.attributes)
        self._fragments.append("<{0}{1}>".format(element.name, attribute_string))
    
    #:: Self, Self -> none
    def append(self, other):
        if other._fragments:
            self._write_all()
            for fragment in other._fragments:
                self._fragments.append(fragment)
    
    #:: Self -> str
    def html_string(self):
        return "".join(self._fragments)


class _Element(object):
    #:: Self, str, dict[str, str] -> none
    def __init__(self, name, attributes):
        if attributes is None:
            attributes = {}
        
        self.name = name
        self.attributes = attributes
        self.written = False


#:: str -> str
def _escape_html(text):
    return cgi.escape(text, quote=True)


#:: dict[str, str] -> str
def _generate_attribute_string(attributes):
    if attributes is None:
        return ""
    else:
        return "".join(
            ' {0}="{1}"'.format(key, _escape_html(value))
            for key, value in attributes.items()
        )


#:: HtmlGenerator, HtmlPath -> none
def satisfy_html_path(generator, path):
    first_unsatisfied_index = _find_first_unsatisfied_index(generator, path)
    while len(generator._stack) > first_unsatisfied_index:
        generator.end()
    
    for element in path.elements[first_unsatisfied_index:]:
        attributes = {}
        if element.class_names:
            attributes["class"] = _generate_class_attribute(element)
        generator.start(element.names[0], attributes=attributes)
    

#:: HtmlGenerator, HtmlPath -> int
def _find_first_unsatisfied_index(generator, path):
    for index, (generated_element, path_element) in enumerate(zip(generator._stack, path.elements)):
        if not _is_element_match(generated_element, path_element):
            return index
    
    return len(generator._stack)


#:: _Element, HtmlPathElement -> bool
def _is_element_match(generated_element, path_element):
    return (
        not path_element.fresh and
        generated_element.name in path_element.names and
        generated_element.attributes.get("class", "") == _generate_class_attribute(path_element)
    )


#:: HtmlPathElement -> str
def _generate_class_attribute(path_element):
    return " ".join(path_element.class_names)

