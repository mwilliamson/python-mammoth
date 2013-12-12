from . import html_paths


def read_html_path(string):
    return html_paths.path([html_paths.element(string)])
