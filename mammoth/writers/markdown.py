from __future__ import unicode_literals

import re


class MarkdownWriter(object):
    def __init__(self):
        self._fragments = []
    
    def text(self, text):
        self._fragments.append(_escape_markdown(text))
    
    def start(self, name, attributes=None):
        if name == "h1":
            self._fragments.append("# ")

    def end(self, name):
        if name in ["p", "h1"]:
            self._fragments.append("\n\n")
    
    def self_closing(self, name, attributes=None):
        pass
    
    def append(self, other):
        self._fragments.append(other)
    
    def as_string(self):
        return "".join(self._fragments)


def _escape_markdown(value):
    return re.sub(r"([\`\*_\{\}\[\]\(\)\#\+\-\.\!])", r"\\\1", re.sub("\\\\", "\\\\\\\\", value))
