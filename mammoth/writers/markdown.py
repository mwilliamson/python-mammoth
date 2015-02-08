from __future__ import unicode_literals

import re


def _symmetric_wrapped(end):
    return _Wrapped(end, end)


class _Wrapped(object):
    def __init__(self, start, end):
        self._start = start
        self._end = end
    
    def __call__(self, attributes):
        return self._start, self._end


def _hyperlink(attributes):
    href = attributes.get("href", "")
    if href:
        return "[", "]({0})".format(href)
    else:
        return _default_output


def _init_writers():
    writers = {
        "p": _Wrapped("", "\n\n"),
        "br": _Wrapped("", "  \n"),
        "strong": _symmetric_wrapped("__"),
        "em": _symmetric_wrapped("*"),
        "a": _hyperlink,
    }
    
    for level in range(1, 7):
        writers["h{0}".format(level)] = _Wrapped("#" * level + " ", "\n\n")
    
    return writers


_writers = _init_writers()
_default_output = ("", "")
_default_writer = lambda attributes: _default_output


class MarkdownWriter(object):
    def __init__(self):
        self._fragments = []
        self._element_stack = []
    
    def text(self, text):
        self._fragments.append(_escape_markdown(text))
    
    def start(self, name, attributes=None):
        if attributes is None:
            attributes = {}
        
        start, end = _writers.get(name, _default_writer)(attributes)
        self._fragments.append(start)
        self._element_stack.append(end)

    def end(self, name):
        end = self._element_stack.pop()
        self._fragments.append(end)
    
    def self_closing(self, name, attributes=None):
        self.start(name, attributes)
        self.end(name)
    
    def append(self, other):
        self._fragments.append(other)
    
    def as_string(self):
        return "".join(self._fragments)


def _escape_markdown(value):
    return re.sub(r"([\`\*_\{\}\[\]\(\)\#\+\-\.\!])", r"\\\1", re.sub("\\\\", "\\\\\\\\", value))
