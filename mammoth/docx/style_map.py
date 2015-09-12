from ..zips import open_zip, update_zip


_style_map_path = "mammoth/style-map"


def write_style_map(fileobj, style_map):
    update_zip(fileobj, {
        _style_map_path: style_map
    })


def read_style_map(fileobj):
    with open_zip(fileobj, "r") as zip_file:
        if zip_file.exists(_style_map_path):
            return zip_file.read_str(_style_map_path)


