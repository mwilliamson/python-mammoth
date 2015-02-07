from __future__ import unicode_literals


class MarkdownWriter(object):
    def __init__(self):
        self._fragments = []
    
    def text(self, text):
        self._fragments.append(text)
    
    def start(self, name, attributes=None):
        pass

    def end(self, name):
        if name == "p":
            self._fragments.append("\n\n")
    
    def self_closing(self, name, attributes=None):
        pass
    
    def append(self, other):
        self._fragments.append(other)
    
    def as_string(self):
        return "".join(self._fragments)
