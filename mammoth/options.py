from . import style_reader, lists


def read_options(options):
    custom_style_map = _read_style_map(options.get("style_map") or "")
    include_default_style_map = options.get("include_default_style_map", True)
    
    options["style_map"] = custom_style_map + \
        (_default_style_map if include_default_style_map else [])
    return options


def _read_style_map(style_text):
    lines = filter(None, map(_get_line, style_text.split("\n")))
    return lists.map(style_reader.read_style, lines)
    

def _get_line(line):
    line = line.strip()
    if line.startswith("#"):
        return None
    else:
        return line


_default_style_map = _read_style_map("""
p[style-name='Normal'] => p:fresh

p.Heading1 => h1:fresh
p.Heading2 => h2:fresh
p.Heading3 => h3:fresh
p.Heading4 => h4:fresh
p[style-name='Heading 1'] => h1:fresh
p[style-name='Heading 2'] => h2:fresh
p[style-name='Heading 3'] => h3:fresh
p[style-name='Heading 4'] => h4:fresh
p[style-name='heading 1'] => h1:fresh
p[style-name='heading 2'] => h2:fresh
p[style-name='heading 3'] => h3:fresh
p[style-name='heading 4'] => h4:fresh
p[style-name='heading 4'] => h4:fresh

p[style-name='footnote text'] => p
r[style-name='footnote reference'] =>
p[style-name='endnote text'] => p
r[style-name='endnote reference'] =>
        
# LibreOffice
p[style-name='Footnote'] => p
r[style-name='Footnote anchor'] =>
p[style-name='Endnote'] => p
r[style-name='Endnote anchor'] =>

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

