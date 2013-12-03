def read_content_types_xml_element(element):
    extension_defaults = dict(map(
        _read_default,
        element.find_children("content-types:Default")
    ))
    overrides = dict(map(
        _read_override,
        element.find_children("content-types:Override")
    ))
    return ContentTypes(extension_defaults, overrides)


def _read_default(element):
    extension = element.attributes["Extension"]
    content_type = element.attributes["ContentType"]
    return extension, content_type


def _read_override(element):
    part_name = element.attributes["PartName"]
    content_type = element.attributes["ContentType"]
    return part_name.lstrip("/"), content_type


class ContentTypes(object):
    def __init__(self, extension_defaults, overrides):
        self._extension_defaults = extension_defaults
        self._overrides = overrides
    
    def find_content_type(self, path):
        if path in self._overrides:
            return self._overrides[path]
        else:
            extension = path.rpartition(".")[2]
            return self._extension_defaults.get(extension)
