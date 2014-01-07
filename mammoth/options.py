from . import style_reader, lists


def read_options(options):
    if options.get("style_map") is None:
        style_map = _default_style_map
    else:
        style_map = _read_style_map(style_map)
    
    options["style_map"] = style_map
    return options


def _read_style_map(style_text):
    lines = filter(None, map(lambda line: line.strip(), style_text.split("\n")))
    return lists.map(style_reader.read_style, lines)
    


_default_style_map = _read_style_map("""
p.Heading1 => h1:fresh
p.Heading2 => h2:fresh
p.Heading3 => h3:fresh
p.Heading4 => h4:fresh
p:unordered-list(1) => ul > li:fresh
p:unordered-list(2) => ul|ol > li > ul > li:fresh
p:unordered-list(3) => ul|ol > li > ul|ol > li > ul > li:fresh
p:unordered-list(4) => ul|ol > li > ul|ol > li > ul|ol > li > ul > li:fresh
p:unordered-list(5) => ul|ol > li > ul|ol > li > ul|ol > li > ul|ol > li > ul > li:fresh
p:ordered-list(1) => ol > li:fresh
p:ordered-list(2) => ul|ol > li > ol > li:fresh
p:ordered-list(3) => ul|ol > li > ul|ol > li > ol > li:fresh
p:ordered-list(4) => ul|ol > li > ul|ol > li > ul|ol > li > ol > li:fresh
p:ordered-list(5) => ul|ol > li > ul|ol > li > ul|ol > li > ul|ol > li > ol > li:fresh
""")

