def read_content_types_xml_element(element):
    extension_defaults = dict(map(
        _read_default,
        element.find_children("content-types:Default"))
    )
    return ContentTypes(extension_defaults)


def _read_default(element):
    extension = element.attributes["Extension"]
    content_type = element.attributes["ContentType"]
    return extension, content_type


class ContentTypes(object):
    def __init__(self, extension_defaults):
        self._extension_defaults = extension_defaults
    
    def find_content_type(self, path):
        extension = path.rpartition(".")[2]
        return self._extension_defaults.get(extension)
