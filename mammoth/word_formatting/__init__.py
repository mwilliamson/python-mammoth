import copy

from mammoth.debug import is_debug_mode

# Conversion units
EMU_TO_INCHES = 914400
EMU_TO_PIXELS = 9525
POINT_TO_PIXEL = (1 / 0.75)  # Per W3C
TWIP_TO_PIXELS = POINT_TO_PIXEL / 20 # 20 -> 1 inch; 72pt / in per PostScript -> 72 points
EIGHTPOINT_TO_PIXEL = POINT_TO_PIXEL / 8
FIFTHPERCENT_TO_PERCENT = 0.02


class WordFormatting(dict):
    def __init__(self, styles_node):
        super().__init__()
        defaults = {}
        doc_default = styles_node.find_child_or_null("w:docDefaults")
        defaults['rpr'] = self.load_rpr(doc_default.find_child_or_null("w:rPrDefault"))
        defaults['ppr'] = self.load_ppr(doc_default.find_child_or_null("w:pPrDefault"))
        self['defaults'] = defaults
        self['nodes'] = self.presort_nodes(styles_node)

    @staticmethod
    def load_rpr(element):
        formatting = {}
        rpr = element.find_child_or_null("w:rPr")

        font_props = rpr.find_child_or_null("w:rFonts")
        font_theme = font_props.attributes.get("w:asciiTheme", "")
        font = font_props.attributes.get("w:ascii", "")
        if len(font_theme) and font_theme == "minorHAnsi":
            formatting['font-family'] = "Calibri, Candara, Segoe, \"Segoe UI\", Optima, Arial, sans-serif"
        else:
            formatting['font-family'] = font

        font_kerning = int(rpr.find_child_or_null('w:kern').attributes.get("w:val", 0))
        if font_kerning:
            formatting['font-kerning'] = 'normal'
        else:
            formatting['font-kerning'] = 'none'

        font_size = int(rpr.find_child_or_null('w:sz').attributes.get("w:val", 0))
        formatting['font-size'] = f'{str(font_size / 2)}pt'

        ligatures = rpr.find_child_or_null('w14:ligatures').attributes.get("w14:val", "normal")
        if ligatures == "standardContextual":
            formatting['font-variant'] = 'contextual'

        return formatting

    @staticmethod
    def load_ppr(element):
        formatting = {}
        ppr = element.find_child_or_null("w:pPr")

        line_spacing = ppr.find_child_or_null("w:spacing")
        after = int(line_spacing.attributes.get("w:after", 0))
        before = int(line_spacing.attributes.get("w:before", 0))
        line = int(line_spacing.attributes.get("w:line", 240))
        line_rule = line_spacing.attributes.get("w:lineRule", "auto")

        if line_rule in ("atLeast", "exactly"):
            formatting['margin-top'] = f'{round(before / line, 1)}pt'
            formatting['margin-after'] = f'{round(after / line, 1)}pt'
        else:
            formatting['margin-top'] = f'{round(before / line, 1)}em'
            formatting['margin-after'] = f'{round(after / line, 1)}em'

        return formatting

    @staticmethod
    def presort_nodes(element):
        node_cache = {}
        for style_element in element.find_children("w:style"):
            style_type = style_element.attributes["w:type"]
            style_name = style_element.attributes["w:styleId"]
            default_style = bool(int(style_element.attributes.get("w:default", False)))
            if not style_type in node_cache:
                node_cache[style_type] = {"default": None}
            node_cache[style_name] = style_element

            if default_style:
                node_cache[style_type]["default"] = style_element
        return node_cache


    def _load_from_cache(self, typ, name):
        root = self.get(typ, None)
        if not root is None:
            formatting = root.get(name, None)
            if not formatting is None:
                return formatting
        return None

    def _load_from_nodes(self, typ, name):
        node = self["nodes"][typ][name]

        # Attempt to generate a merged version of the styles information
        inherits = node.find_child_or_null("w:basedOn").attributes.get("w:val")
        base_formatting = copy.deepcopy(self['defaults'])
        if not inherits is None:
            base_formatting.update(self._load_or_cache(typ, inherits))

        # Apply formatting here!
        base_formatting["ppr"].update(self.load_ppr(node))
        base_formatting["rpr"].update(self.load_rpr(node))
        return base_formatting

    def _update_cache(self, typ, name, cache_item):
        if not typ in self:
            self[typ] = {}

        self[typ].update({
            name: cache_item
        })

    def _load_or_cache(self, typ, name):
        formatting = self._load_from_cache(typ, name)
        if formatting is None:
            formatting = self._load_from_nodes(typ, name)
            self._update_cache(typ, name, formatting)
        return formatting

    def get_formatting_style(self, name, typ="ppr"):
        if is_debug_mode():
            if typ in ("ppr", "rpr"):
                return self._load_or_cache("paragraph", name)[typ]
            return self._load_or_cache("table", name)[typ]
        return {}

