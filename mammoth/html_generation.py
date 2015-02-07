from __future__ import unicode_literals


class HtmlGenerator(object):
    def __init__(self, create_writer):
        self._stack = []
        self._create_writer = create_writer
        self._writer = create_writer()
    
    def text(self, text):
        if text:
            self._write_all()
            self._writer.text(text)
    
    def start(self, name, attributes=None, always_write=False):
        self._stack.append(_Element(name, attributes))
        
        if always_write:
            self._write_all()

    def end(self):
        element = self._stack.pop()
        if element.written:
            self._writer.end(element.name)
    
    def end_all(self):
        while self._stack:
            self.end()
    
    def self_closing(self, name, attributes=None):
        self._writer.self_closing(name, attributes)
    
    def _write_all(self):
        for element in self._stack:
            if not element.written:
                element.written = True
                self._write_element(element)
    
    def _write_element(self, element):
        self._writer.start(element.name, element.attributes)
    
    def append(self, other):
        other_string = other.as_string()
        if other_string:
            self._write_all()
            self._writer.append(other_string)
    
    def as_string(self):
        return self._writer.as_string()
    
    def child(self):
        return HtmlGenerator(self._create_writer)


class _Element(object):
    def __init__(self, name, attributes):
        if attributes is None:
            attributes = {}
        
        self.name = name
        self.attributes = attributes
        self.written = False


def satisfy_html_path(generator, path):
    first_unsatisfied_index = _find_first_unsatisfied_index(generator, path)
    while len(generator._stack) > first_unsatisfied_index:
        generator.end()
    
    for element in path.elements[first_unsatisfied_index:]:
        attributes = {}
        if element.class_names:
            attributes["class"] = _generate_class_attribute(element)
        generator.start(element.names[0], attributes=attributes)
    

def _find_first_unsatisfied_index(generator, path):
    for index, (generated_element, path_element) in enumerate(zip(generator._stack, path.elements)):
        if not _is_element_match(generated_element, path_element):
            return index
    
    return len(generator._stack)


def _is_element_match(generated_element, path_element):
    return (
        not path_element.fresh and
        generated_element.name in path_element.names and
        generated_element.attributes.get("class", "") == _generate_class_attribute(path_element)
    )


def _generate_class_attribute(path_element):
    return " ".join(path_element.class_names)
