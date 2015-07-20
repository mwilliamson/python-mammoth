def read_content_types_xml_element(element):
    extension_defaults = dict(map(
        _read_default,
        element.find_children("content-types:Default")
    ))
    overrides = dict(map(
        _read_override,
        element.find_children("content-types:Override")
    ))
    return _ContentTypes([
        _XmlContentTypes(extension_defaults, overrides),
        _FallbackContentTypes(),
    ])


def _read_default(element):
    extension = element.attributes["Extension"]
    content_type = element.attributes["ContentType"]
    return extension, content_type


def _read_override(element):
    part_name = element.attributes["PartName"]
    content_type = element.attributes["ContentType"]
    return part_name.lstrip("/"), content_type


class _ContentTypes(object):
    def __init__(self, finders):
        self._finders = finders
    
    def find_content_type(self, path):
        for finder in self._finders:
            content_type = finder.find_content_type(path)
            if content_type is not None:
                return content_type


class _FallbackContentTypes(object):
    _image_content_types = {
        "png": "png",
        "gif": "gif",
        "jpeg": "jpeg",
        "jpg": "jpeg",
        "tif": "tiff",
        "tiff": "tiff",
        "bmp": "bmp",
    }
    
    def find_content_type(self, path):
        extension = _get_extension(path).lower()
        if extension in self._image_content_types:
            return "image/" + self._image_content_types[extension]
        else:
            return None


class _XmlContentTypes(object):
    def __init__(self, extension_defaults, overrides):
        self._extension_defaults = extension_defaults
        self._overrides = overrides
    
    def find_content_type(self, path):
        if path in self._overrides:
            return self._overrides[path]
        else:
            extension = _get_extension(path)
            return self._extension_defaults.get(extension)


def _get_extension(path):
    return path.rpartition(".")[2]
