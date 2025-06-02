import copy

from mammoth.debug import is_debug_mode
from mammoth.docx.xmlparser import NullXmlElement
from mammoth.html import MS_BORDER_STYLES, MS_CELL_ALIGNMENT_STYLES

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
        tcpr, borders = self.load_tcpr(doc_default.find_child_or_null("w:tcPrDefault"))
        defaults['tcpr'] = tcpr
        defaults['tblpr'] = self.load_tblpr(doc_default.find_child_or_null("w:tblPrDefault"))
        defaults['borders'] = borders
        defaults['cnf'] = {}
        self['defaults'] = defaults
        self['nodes'] = self.presort_nodes(styles_node)

    @staticmethod
    def _is_int(value):
        if value is None:
            return False

        try:
            int(value)
        except ValueError:
            return False

        return True

    @staticmethod
    def format_to_unit(val, unit):
        if unit == 'dxa':
            return f'{round(float(val) * TWIP_TO_PIXELS,1)}px'
        elif unit == 'pct':
            return f'{round(float(val) * FIFTHPERCENT_TO_PERCENT,1)}%'
        else:
            return f'auto'

    @staticmethod
    def _read_boolean_element(element):
        if element is None:
            return False
        else:
            return WordFormatting._read_boolean_attribute_value(element.attributes.get("w:val"))

    @staticmethod
    def _read_boolean_attribute_value(value):
        return value not in ["false", "0"]

    @staticmethod
    def _read_underline_element(element):
        return element and element.attributes.get("w:val") not in [None, "false", "0", "none"]

    @staticmethod
    def _read_highlight_value(value):
        if not value or value == "none":
            return None
        else:
            return value

    @staticmethod
    def load_rpr(element):
        formatting = {}
        rpr = element.find_child_or_null("w:rPr")

        font_props = rpr.find_child_or_null("w:rFonts")
        font_theme = font_props.attributes.get("w:asciiTheme", "")
        font = font_props.attributes.get("w:ascii", "")
        if len(font_theme) and font_theme == "minorHAnsi":
            formatting['font-family'] = "Calibri, Candara, Segoe, \"Segoe UI\", Optima, Arial, sans-serif"

        font_kerning = int(rpr.find_child_or_null('w:kern').attributes.get("w:val", 0))
        if font_kerning:
            formatting['font-kerning'] = 'normal'

        font_size = int(rpr.find_child_or_null('w:sz').attributes.get("w:val", 22))
        formatting['font-size'] = f'{str(font_size / 2)}pt'

        ligatures = rpr.find_child_or_null('w14:ligatures').attributes.get("w14:val", "normal")
        if ligatures == "standardContextual":
            formatting['font-variant'] = 'contextual'

        text_alignment = rpr \
            .find_child_or_null("w:vertAlign") \
            .attributes.get("w:val")
        if text_alignment is not None:
            if text_alignment == "superscript":
                formatting['vertical-align'] = "super"
            elif text_alignment == "subscript":
                formatting['vertical-align'] = "sub"
            else:
                formatting['vertical-align'] = "baseline"

        font_color = rpr.find_child_or_null("w:color").attributes.get("w:val")
        if font_color is not None and font_color != 'none':
            font_color = font_color
        else:
            font_color = '000000'
        if font_color is not None:
            formatting['color'] = f'#{font_color}'

        is_bold = WordFormatting._read_boolean_element(rpr.find_child("w:b"))
        if is_bold:
            formatting['font-weight'] = 'bold'
        is_italic = WordFormatting._read_boolean_element(rpr.find_child("w:i"))
        if is_italic:
            formatting['font-style'] = 'italic'
        is_underline = WordFormatting._read_underline_element(rpr.find_child("w:u"))
        if is_underline:
            formatting['text-decoration'] = 'underline'
        is_strikethrough = WordFormatting._read_boolean_element(rpr.find_child("w:strike"))
        if is_strikethrough:
            formatting['text-decoration'] = 'line-through'
        is_all_caps = WordFormatting._read_boolean_element(rpr.find_child("w:caps"))
        if is_all_caps:
            formatting['text-transform'] = 'uppercase'
        is_small_caps = WordFormatting._read_boolean_element(rpr.find_child("w:smallCaps"))
        if is_small_caps:
            formatting['font-variant'] = 'common-ligatures small-caps' if is_small_caps else 'normal'
        highlight = WordFormatting._read_highlight_value(rpr.find_child_or_null("w:highlight").attributes.get("w:val"))
        if highlight is not None:
            formatting['background-color'] = highlight

        return formatting

    @staticmethod
    def load_ppr(element):
        formatting = {}
        ppr = element.find_child_or_null("w:pPr")

        line_spacing = ppr.find_child_or_null("w:spacing")
        if not isinstance(line_spacing, NullXmlElement):
            after = int(line_spacing.attributes.get("w:after", 0))
            before = int(line_spacing.attributes.get("w:before", 0))
            line = int(line_spacing.attributes.get("w:line", 240))
            line_rule = line_spacing.attributes.get("w:lineRule", "auto")

            if line_rule in ("atLeast", "exactly"):
                formatting['margin-top'] = f'{round(before / line, 1)}pt'
                formatting['margin-bottom'] = f'{round(after / line, 1)}pt'
            else:
                formatting['margin-top'] = f'{round(before / line, 1)}em'
                formatting['margin-bottom'] = f'{round(after / line, 1)}em'

            formatting.update(WordFormatting.load_shade(element))

        return formatting

    @staticmethod
    def load_tblpr(tblpr):
        formatting = {}
        tblpPR = tblpr.find_child_or_null("w:tblpPr")

        indent = tblpr.find_child_or_null("w:tblInd")
        if not isinstance(indent, NullXmlElement):
            indent_width = indent.attributes.get("w:w", 0)
            indent_type = indent.attributes.get("w:type", 0)
            formatting['padding-left'] = WordFormatting.format_to_unit(indent_width, indent_type)

        horzAnchor = tblpPR.attributes.get("w:horzAnchor", None)
        vertAnchor = tblpPR.attributes.get("w:vertAnchor", None)
        if not (vertAnchor is None or horzAnchor is None):
            tblpX = tblpPR.attributes.get("w:tblpX", 0)
            tblpY = tblpPR.attributes.get("w:tblpY", 0)
            leftFromText = tblpPR.attributes.get("w:leftFromText", 0)
            rightFromText = tblpPR.attributes.get("w:rightFromText", 0)
            topFromText = tblpPR.attributes.get("w:topFromText", 0)
            bottomFromText = tblpPR.attributes.get("w:bottomFromText", 0)

            formatting['position'] = 'relative'
            formatting['left'] = WordFormatting.format_to_unit(tblpX, 'dxa')
            formatting['margin-top'] = WordFormatting.format_to_unit(topFromText, 'dxa')
            formatting['margin-bottom'] = WordFormatting.format_to_unit(bottomFromText, 'dxa')
            formatting['margin-left'] = WordFormatting.format_to_unit(leftFromText, 'dxa')
            formatting['margin-right'] = WordFormatting.format_to_unit(rightFromText, 'dxa')


        tblW = tblpr.find_child_or_null("w:tblW")
        if not tblW is None:
            width = tblW.attributes.get('w:w')
            width_type = tblW.attributes.get('w:type')
            formatting['width'] = WordFormatting.format_to_unit(width, width_type)
        return formatting

    @staticmethod
    def load_tcpr(element):
        tcpr = element.find_child_or_null("w:tcPr")
        tcW = tcpr.find_child_or_null("w:tcW")
        gridspan = tcpr.find_child_or_null("w:gridSpan").attributes.get('w:val')
        vAlign = tcpr.find_child_or_null("w:vAlign").attributes.get("w:val", "top")
        width = tcW.attributes.get("w:w")

        cell_style = {}
        if width is not None:
            cell_style['width'] = f"{round(float(width) * TWIP_TO_PIXELS, 1)}px"

        cell_style['vertical-align'] = MS_CELL_ALIGNMENT_STYLES[vAlign]

        cell_style.update(WordFormatting.load_shade(tcpr))

        return cell_style, WordFormatting.load_tcborders(tcpr)

    @staticmethod
    def load_shade(element):
        formatting = {}

        shade = element.find_child_or_null("w:shd")
        background_color = shade.attributes.get("w:color")
        background_fill = shade.attributes.get("w:fill")
        background_val = shade.attributes.get("w:val")

        if background_fill is not None:
            formatting['background-color'] = f"#{background_fill}"

        return formatting

    @staticmethod
    def load_cell_margin(element):
        formatting = {}

        cell_margin = element.find_child_or_null("w:tblCellMar")
        if not isinstance(cell_margin, NullXmlElement):
            top_margin = cell_margin.find_child_or_null("w:top")
            if not isinstance(top_margin, NullXmlElement):
                top_width = top_margin.attributes.get("w:w")
                top_type = top_margin.attributes.get("w:type")
                formatting['padding-top'] = WordFormatting.format_to_unit(top_width, top_type)

            bottom_margin = cell_margin.find_child_or_null("w:bottom")
            if not isinstance(bottom_margin, NullXmlElement):
                bottom_width = bottom_margin.attributes.get("w:w")
                bottom_type = bottom_margin.attributes.get("w:type")
                formatting['padding-bottom'] = WordFormatting.format_to_unit(bottom_width, bottom_type)

            left_margin = cell_margin.find_child_or_null("w:left")
            if not isinstance(left_margin, NullXmlElement):
                left_width = left_margin.attributes.get("w:w")
                left_type = left_margin.attributes.get("w:type")
                formatting['padding-left'] = WordFormatting.format_to_unit(left_width, left_type)

            right_margin = cell_margin.find_child_or_null("w:right")
            if not isinstance(right_margin, NullXmlElement):
                right_width = right_margin.attributes.get("w:w")
                right_type = right_margin.attributes.get("w:type")
                formatting['padding-right'] = WordFormatting.format_to_unit(right_width, right_type)

        return formatting

    @staticmethod
    def load_tcborders(element):
        tcBorders = element.find_child_or_null("w:tcBorders")
        formatting = copy.deepcopy({'border-collapse': 'collapse'})

        top = tcBorders.find_child_or_null("w:top")
        top_width = top.attributes.get('w:sz')
        top_space = top.attributes.get('w:space')
        top_style = top.attributes.get('w:val')
        top_border = MS_BORDER_STYLES.get(top_style, None)
        top_color = top.attributes.get('w:color')
        if not isinstance(top, NullXmlElement):
            if top_border is not None:
                formatting['border-top-style'] = top_border
            if top_width is not None:
                formatting['border-top-width'] = round(float(top_width) * EIGHTPOINT_TO_PIXEL, 1)
            if top_color is not None and top_color != 'auto':
                formatting['border-top-color'] = top_color

        bottom = tcBorders.find_child_or_null("w:bottom")
        bottom_width = bottom.attributes.get('w:sz')
        bottom_space = bottom.attributes.get('w:space')
        bottom_style = bottom.attributes.get('w:val')
        bottom_border = MS_BORDER_STYLES.get(bottom_style, None)
        bottom_color = bottom.attributes.get('w:color')
        if not isinstance(bottom, NullXmlElement):
            if bottom_border is not None:
                formatting['border-bottom-style'] = bottom_border
            if bottom_width is not None:
                formatting['border-bottom-width'] = round(float(bottom_width) * EIGHTPOINT_TO_PIXEL, 1)
            if bottom_color is not None and bottom_color != 'auto':
                formatting['border-bottom-color'] = bottom_color

        left = tcBorders.find_child_or_null("w:left")
        left = tcBorders.find_child_or_null("w:start") if isinstance(left, NullXmlElement) else left
        left_width = left.attributes.get('w:sz')
        left_space = left.attributes.get('w:space')
        left_style = left.attributes.get('w:val')
        left_border = MS_BORDER_STYLES.get(left_style, None)
        left_color = left.attributes.get('w:color')
        if not isinstance(left, NullXmlElement):
            if left_border is not None:
                formatting['border-left-style'] = left_border
            if left_width is not None:
                formatting['border-left-width'] = round(float(left_width) * EIGHTPOINT_TO_PIXEL, 1)
            if left_color is not None and left_color != 'auto':
                formatting['border-left-color'] = left_color

        right = tcBorders.find_child_or_null("w:right")
        right = tcBorders.find_child_or_null("w:end") if isinstance(right, NullXmlElement) else right
        right_width = right.attributes.get('w:sz')
        right_space = right.attributes.get('w:space')
        right_style = right.attributes.get('w:val')
        right_border = MS_BORDER_STYLES.get(right_style, None)
        right_color = right.attributes.get('w:color')
        if not isinstance(right, NullXmlElement):
            if right_border is not None:
                formatting['border-right-style'] = right_border
            if right_width is not None:
                formatting['border-right-width'] = round(float(right_width) * EIGHTPOINT_TO_PIXEL, 1)
            if right_color is not None and right_color != 'auto':
                formatting['border-right-color'] = right_color

        spacing = [
            float(top_space) if top_space is not None else -1,
            float(bottom_space) if bottom_space is not None else -1,
            float(left_space) if left_space is not None else -1,
            float(right_space) if right_space is not None else -1,
        ]
        max_spacing = max(spacing)
        if max_spacing > -1:
            formatting['border-spacing'] = round(max_spacing * POINT_TO_PIXEL, 1)

        return formatting

    @staticmethod
    def load_tblcnfpr(element):
        formatting = []
        tblFormatting = element.find_child_or_null("w:tblPr")
        cell_margin = WordFormatting.load_cell_margin(tblFormatting)
        for tblStyle in element.find_children("w:tblStylePr"):
            ppr = WordFormatting.load_ppr(tblStyle)
            rpr = WordFormatting.load_rpr(tblStyle)
            tcpr, borders = WordFormatting.load_tcpr(tblStyle)
            tcpr.update(cell_margin)
            tblpr = WordFormatting.load_tblpr(tblFormatting)
            formatting.append({
                "rpr": rpr,
                "ppr": ppr,
                "tcpr": tcpr,
                "tblpr": tblpr,
                "borders": borders
            })
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
            node_cache[style_type][style_name] = style_element

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
        tblpr = node.find_child_or_null("w:tblPr")
        base_formatting["ppr"].update(self.load_ppr(node))
        base_formatting["rpr"].update(self.load_rpr(node))
        base_formatting["ppr"].update(self.load_cell_margin(tblpr))
        tcpr, borders = self.load_tcpr(node)
        base_formatting["tcpr"].update(tcpr)
        base_formatting["tblpr"].update(self.load_tblpr(tblpr))
        base_formatting["borders"].update(borders)
        base_formatting["cnf"] = self.load_tblcnfpr(node)

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

    def _get_formatting_style(self, name, typ="ppr"):
        if is_debug_mode():
            if name is None or len(name) == 0:
                return {}
            if typ in ("ppr", "rpr"):
                return self._load_or_cache("paragraph", name)
            return self._load_or_cache("table", name)
        return {}

    def _classify_element(self, element):
        if element.name == 'w:p':
            return 'paragraph'
        if element.name == 'w:r':
            return 'character'
        if element.name == 'w:tbl':
            return 'table'
        if element.name == 'w:tr':
            return 'row'
        if element.name == 'w:tc':
            return 'cell'
        return 'numbering'

    def _find_style_id(self, element, element_type):
        if element_type == 'paragraph':
            return element.find_child_or_null("w:pPr").find_child_or_null("w:pStyle").attributes.get("w:val", "")
        if element_type == 'character':
            return element.find_child_or_null("w:rPr").find_child_or_null("w:rStyle").attributes.get("w:val", "")
        if element_type == 'table':
            return element.find_child_or_null("w:tblPr").find_child_or_null("w:tblStyle").attributes.get("w:val", "")
        if element_type == 'row':
            return element.find_child_or_null("w:trPr").find_child_or_null("w:trStyle").attributes.get("w:val", "")
        if element_type == 'cell':
            return element.find_child_or_null("w:tcPr").find_child_or_null("w:tcStyle").attributes.get("w:val", "")
        return ""

    def _find_table_root(self, element):
        parent = element.parent
        if isinstance(parent, NullXmlElement):
            return element

        parent_type = self._classify_element(parent)
        if parent_type == "table":
            return parent
        return self._find_table_root(parent)

    def _find_style(self, element):
        interest_node = self._find_table_root(element)
        return self._find_style_id(interest_node, "table")

    def _find_cnf_id(self, element, element_type):
        if element_type == 'paragraph':
            return element.find_child_or_null("w:pPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'character':
            return element.find_child_or_null("w:rPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'table':
            return element.find_child_or_null("w:tblPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        return (element.find_child_or_null("w:tcPr")
                .find_child_or_null("w:cnfStyle")
                .attributes.get("w:val",
                                element.find_child_or_null("w:trPr")
                                .find_child_or_null("w:cnfStyle")
                                .attributes.get("w:val", "")))

    def _find_cnf_index(self, cnf):
        indx = []
        for i in range(len(cnf)):
            if cnf[i] == "1":
                indx.append(i)
        return indx

    def _collapse_cnf(self, cnf_id, formatting):
        cnf_indices = self._find_cnf_index(cnf_id)
        cnf_formattings = [formatting['cnf'][i] for i in cnf_indices]
        cnf = copy.deepcopy(self['defaults'])

        for cnf_format in cnf_formattings:
            cnf['ppr'].update(cnf_format['ppr'])
            cnf['rpr'].update(cnf_format['rpr'])
            cnf['tcpr'].update(cnf_format['tcpr'])
            cnf['tblpr'].update(cnf_format['tblpr'])
            cnf['borders'].update(cnf_format['borders'])

        return cnf

    def get_element_base_formatting(self, element):
        element_type = self._classify_element(element)
        format_id = self._find_style_id(element, element_type)
        formatting = self._get_formatting_style(format_id, element_type)

        text_style = copy.deepcopy(formatting['ppr'])
        text_style.update(formatting['rpr'])

        return {
            'text_style': text_style,
            'cell_style': formatting['tcpr'],
            'border_style': formatting['borders'],
            'table_style': formatting['tblpr'],
        }

    def get_element_formatting(self, element):
        tblpr = element.find_child_or_null("w:tblPr")
        tcPr = element.find_child_or_null("w:tcPr")
        rPr = element.find_child_or_null("w:rPr")
        pPr = element.find_child_or_null("w:pPr")
        base_formatting = self.get_element_base_formatting(element)
        base_formatting.update({
            "table_style": self.load_tblpr(tblpr)
        })

        return base_formatting

    def get_conditional_formatting(self, element):
        element_type = self._classify_element(element)
        format_id = self._find_style(element)
        cnf_id = self._find_cnf_id(element, element_type)
        formatting = self._get_formatting_style(format_id, element_type)
        cnf = self._collapse_cnf(cnf_id, formatting)

        text_style = copy.deepcopy(formatting['ppr'])
        text_style.update(cnf['ppr'])
        text_style.update(formatting['rpr'])
        text_style.update(cnf['rpr'])

        border_style = copy.deepcopy(formatting['borders'])
        border_style.update(cnf['borders'])

        cell_style = copy.deepcopy(formatting['tcpr'])
        cell_style.update(cnf['tcpr'])
        """
        print(element_type)
        print(format_id)
        print(cnf_id)
        print(cnf)
        print(formatting['borders'])
        input()
        """
        #input()

        return {
            'text_style': text_style,
            'cell_style': cell_style,
            'border_style': border_style
        }

