
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
        defaults['run'] = self.load_rpr_default(doc_default.find_child_or_null("w:rPrDefault"))
        defaults['paragraph'] = self.load_ppr_default(doc_default.find_child_or_null("w:pPrDefault"))
        self['defaults'] = defaults

    @staticmethod
    def load_rpr_default(element):
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
    def load_ppr_default(element):
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

