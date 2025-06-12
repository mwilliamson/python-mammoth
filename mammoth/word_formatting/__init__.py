import copy
import itertools

from mammoth.debug import is_debug_mode, print_debug, pause_debug
from mammoth.docx.xmlparser import NullXmlElement
from mammoth.html import MS_BORDER_STYLES, MS_CELL_ALIGNMENT_STYLES

NULL_ELEMENT = NullXmlElement()

# Conversion units
EMU_TO_INCHES = 914400
EMU_TO_PIXELS = 9525
POINT_TO_PIXEL = (1 / 0.75)  # Per W3C
TWIP_TO_PIXELS = POINT_TO_PIXEL / 20  # 20 -> 1 inch; 72pt / in per PostScript -> 72 points
EIGHTPOINT_TO_PIXEL = POINT_TO_PIXEL / 8
FIFTHPERCENT_TO_PERCENT = 0.02


def is_odd(ls, itm):
    try:
        indx = ls.index(itm)
        return bool(indx % 2)
    except:
        return False

def get_odd_items(ls):
    odd = True
    odd_ls = []
    for itm in ls:
        if odd:
            odd_ls.append(itm)
        odd = not odd
    return odd_ls

class WordFormatting(dict):
    CNF_IDS = {
        "firstRow": 0,
        "lastRow": 1,
        "firstCol": 2,
        "lastCol": 3,
        "band1Vert": 4,
        "band2Vert": 5,
        "band1Horz": 6,
        "band2Horz": 7,
        "neCell": 8,
        "nwCell": 9,
        "seCell": 10,
        "swCell": 11,
    }
    def __init__(self, styles_node):
        super().__init__()
        defaults = {}
        doc_default = styles_node.find_child_or_null("w:docDefaults")
        defaults['rpr'] = self.load_rpr(doc_default.find_child_or_null("w:rPrDefault"))
        defaults['ppr'] = self.load_ppr(doc_default.find_child_or_null("w:pPrDefault"))
        tcpr, borders, attributes = self.load_tcpr(doc_default.find_child_or_null("w:tcPrDefault"))
        defaults['attributes'] = attributes
        defaults['tcpr'] = tcpr
        defaults['tblpr'] = self.load_tblpr(doc_default.find_child_or_null("w:tblPrDefault"))
        defaults['trpr'] = self.load_trpr(doc_default.find_child_or_null("w:trPrDefault"))
        defaults['borders'] = borders
        self['defaults'] = defaults
        self['style_nodes'] = self.presort_nodes(styles_node)
        self['cnf_styles'] = {}
        self['styles_node'] = styles_node

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
            return f'{round(float(val) * TWIP_TO_PIXELS, 1)}px'
        elif unit == 'pct':
            return f'{round(float(val) * FIFTHPERCENT_TO_PERCENT, 1)}%'
        elif unit == 'eop':
            return f'{round(float(val) * EIGHTPOINT_TO_PIXEL, 1)}px'
        elif unit == 'ptp':
            return f'{round(float(val) * POINT_TO_PIXEL, 1)}px'
        elif unit == 'px':
            return f'{round(val, 1)}px'
        elif unit == 'pt':
            return f'{round(val, 1)}pt'
        elif unit == 'em':
            return f'{round(val, 1)}em'
        else:
            return f'auto'

    @staticmethod
    def format_color(val):
        if val is None or val == 'none':
            return '#000000'
        elif val == 'auto':
            return 'auto'
        else:
            return f'#{val}'

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
    def merge_formatting(base_formatting, new_formatting):
        result_format = {}
        # print_debug('{} vs. {}'.format(type(base_formatting), type(new_formatting)))
        is_base_dict = isinstance(base_formatting, dict)
        is_new_dict = isinstance(new_formatting, dict)
        if is_base_dict and is_new_dict:
            is_base_empty = not len(base_formatting)
            is_new_empty = not len(new_formatting)
            if is_base_empty:
                return new_formatting
            elif is_new_empty:
                return base_formatting
            else:
                for k in new_formatting:
                    if k in base_formatting:
                        lhs = base_formatting[k]
                        rhs = new_formatting[k]
                        is_base_empty = not bool(lhs)
                        is_new_empty = not bool(rhs)
                        # print_debug('~~~~~{}~~~~~'.format(k))
                        # print_debug(lhs)
                        # print_debug(rhs)
                        # print_debug(is_base_empty)
                        # print_debug(is_new_empty)
                        # print_debug((not is_base_empty and not is_new_empty))
                        # print_debug(not is_new_empty)
                        result_format[k] = lhs
                        if is_base_empty or (not is_base_empty and not is_new_empty) or not is_new_empty:
                            result_format[k].update(rhs)
                    else:
                        result_format[k] = new_formatting[k]
        #elif not is_base_dict and not is_new_dict:
        #    is_base_empty = base_formatting is None and not len(str(base_formatting))
        #    is_new_empty = new_formatting is None and not len(str(new_formatting))
        #    if not is_base_empty and not is_new_empty:
        #        return base_formatting
        #    elif is_base_empty and not is_new_empty:
        #        return new_formatting
        #    elif not is_base_empty and is_new_empty:
        #        return base_formatting
        elif not is_base_dict or not is_new_dict:
            #print_debug('???')
            is_base_empty = base_formatting is None or not len(base_formatting)
            is_new_empty = new_formatting is None or not len(new_formatting)
            #print_debug(base_formatting)
            #print_debug('_________________')
            #print_debug(new_formatting)
            if is_new_empty:
                return base_formatting
            elif is_base_empty:
                return new_formatting
            else:
                return base_formatting
        return result_format

    @staticmethod
    def load_rpr(element):
        formatting = {}
        rpr = element.find_child_or_null("w:rPr")

        if isinstance(rpr, NullXmlElement):
            rpr = element.find_parent().find_child_or_null("w:rPr")

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
        formatting['color'] = WordFormatting.format_color(font_color)

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
            formatting['background-color'] = WordFormatting.format_color(highlight)
        is_deleted = WordFormatting._read_boolean_element(rpr.find_child("w:del"))

        formatting['_props'] = {
            'vertical_alignment': text_alignment,
            'font': font,
            'font_size': font_size,
            'font_color': font_color,
            'is_bold': is_bold,
            'is_italic': is_italic,
            'is_underline': is_underline,
            'is_strikethrough': is_strikethrough,
            'is_all_caps': is_all_caps,
            'is_small_caps': is_small_caps,
            'highlight': highlight,
            'is_deleted': is_deleted,
        }

        return formatting

    @staticmethod
    def load_ppr(element):
        formatting = {}
        ppr = element.find_child_or_null("w:pPr")

        if isinstance(ppr, NullXmlElement):
            ppr = element.find_parent().find_child_or_null("w:pPr")

        line_spacing = ppr.find_child_or_null("w:spacing")
        if not isinstance(line_spacing, NullXmlElement):
            after = int(line_spacing.attributes.get("w:after", 0))
            before = int(line_spacing.attributes.get("w:before", 0))
            line = int(line_spacing.attributes.get("w:line", 240))
            line_rule = line_spacing.attributes.get("w:lineRule", "auto")

            if line_rule in ("atLeast", "exactly"):
                formatting['margin-top'] = WordFormatting.format_to_unit(before / line, 'pt')
                formatting['margin-bottom'] = WordFormatting.format_to_unit(after / line, 'pt')
            else:
                formatting['margin-top'] = WordFormatting.format_to_unit(before / line, 'em')
                formatting['margin-bottom'] = WordFormatting.format_to_unit(before / line, 'em')

            formatting.update(WordFormatting.load_shade(element))

        return formatting

    @staticmethod
    def load_tblpr(element):
        formatting = {}
        tblpr = element.find_child_or_null("w:tblPr")
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
            formatting['top'] = WordFormatting.format_to_unit(topFromText, 'dxa')
            formatting['bottom'] = WordFormatting.format_to_unit(bottomFromText, 'dxa')
            formatting['left'] = WordFormatting.format_to_unit(leftFromText, 'dxa')
            formatting['right'] = WordFormatting.format_to_unit(rightFromText, 'dxa')

        tblW = tblpr.find_child_or_null("w:tblW")
        if not tblW is None:
            width = tblW.attributes.get('w:w')
            width_type = tblW.attributes.get('w:type')
            formatting['width'] = WordFormatting.format_to_unit(width, width_type)
        return formatting

    @staticmethod
    def load_trpr(element):
        formatting = {}
        trpr = element.find_child_or_null("w:trPr")

        trHeight = trpr.find_child_or_null("w:trHeight")
        height = trHeight.attributes.get("w:val", 0)
        formatting['height'] = WordFormatting.format_to_unit(height, 'dxa')

        jc = trpr.find_child_or_null("w:jc")
        text_alignment = jc.attributes.get("w:val", "start")
        if text_alignment == "left":
            formatting['text-align'] = "start"
        elif text_alignment == "right":
            formatting['text-align'] = "end"
        else:
            formatting['text-align'] = text_alignment
        return formatting

    @staticmethod
    def load_tcpr(element):
        cell_style = {}
        attributes = {}
        borders = {'border-collapse': 'collapse'}

        for tcpr in element.find_children("w:tcPr"):
            tcW = tcpr.find_child_or_null("w:tcW")
            gridspan = tcpr.find_child_or_null("w:gridSpan").attributes.get('w:val')
            vAlign = tcpr.find_child_or_null("w:vAlign").attributes.get("w:val", "top")
            width = tcW.attributes.get("w:w")

            if width is not None:
                cell_style['width'] = f"{round(float(width) * TWIP_TO_PIXELS, 1)}px"

            cell_style['vertical-align'] = MS_CELL_ALIGNMENT_STYLES[vAlign]

            cell_style.update(WordFormatting.load_shade(tcpr))

            cell_style.update(WordFormatting.load_margins(tcpr))

            attributes.update({
                'colspan': 1 if gridspan is None else int(gridspan),
                'rowspan': 1,
            })

            borders.update(WordFormatting.load_tcborders(tcpr))

        return (
            cell_style,
            borders,
            attributes
        )

    @staticmethod
    def load_margins(element):
        formatting = {}
        margin = element.find_child_or_null("w:tcMar")

        if isinstance(margin, NullXmlElement):
            margin = element.find_child_or_null("w:tblCellMar")

        if not isinstance(margin, NullXmlElement):
            top = margin.find_child_or_null("w:top")
            if not isinstance(top, NullXmlElement):
                formatting['padding-top'] = WordFormatting.format_to_unit(
                    top.attributes.get("w:w", 0),
                    top.attributes.get("w:type", "dxa")
                )
            bottom = margin.find_child_or_null("w:bottom")
            if not isinstance(bottom, NullXmlElement):
                formatting['padding-bottom'] = WordFormatting.format_to_unit(
                    bottom.attributes.get("w:w", 0),
                    bottom.attributes.get("w:type", "dxa")
                )
            left = margin.find_child_or_null("w:left")
            if not isinstance(left, NullXmlElement):
                formatting['padding-left'] = WordFormatting.format_to_unit(
                    left.attributes.get("w:w", 0),
                    left.attributes.get("w:type", "dxa")
                )
            right = margin.find_child_or_null("w:right")
            if not isinstance(right, NullXmlElement):
                formatting['padding-right'] = WordFormatting.format_to_unit(
                    right.attributes.get("w:w", 0),
                    right.attributes.get("w:type", "dxa")
                )

        return formatting

    @staticmethod
    def load_shade(element):
        formatting = {}

        shade = element.find_child_or_null("w:shd")
        background_color = shade.attributes.get("w:color")
        background_fill = shade.attributes.get("w:fill")
        background_val = shade.attributes.get("w:val")

        if background_color is not None:
            formatting['background-color'] = WordFormatting.format_color(background_fill)

        return formatting

    @staticmethod
    def load_tblborders(element):
        element_type = WordFormatting._classify_element(element)
        table = element
        if element_type in ("row", "cell"):
            table = WordFormatting._find_table_root(element)
        tblBorders = table.find_child_or_null('w:tblPr').find_child_or_null("w:tblBorders")
        #print_debug(element_type)
        #print_debug(isinstance(table.find_child_or_null('w:tblPr'), NullXmlElement))
        #print_debug(isinstance(tblBorders, NullXmlElement))
        if isinstance(tblBorders, NullXmlElement):
            return {}
        return WordFormatting.load_borders(tblBorders)

    @staticmethod
    def load_tcborders(element):
        tcBorders = element.find_child_or_null("w:tcBorders")
        return WordFormatting.load_borders(tcBorders)

    @staticmethod
    def load_borders(borders_element):
        formatting = {'border-collapse': 'collapse'}

        top = borders_element.find_child_or_null("w:top")
        top_width = top.attributes.get('w:sz')
        top_space = top.attributes.get('w:space')
        top_style = top.attributes.get('w:val')
        top_border = MS_BORDER_STYLES.get(top_style, None)
        top_color = top.attributes.get('w:color')
        if not isinstance(top, NullXmlElement):
            if top_border is not None:
                formatting['border-top-style'] = top_border
            if top_width is not None:
                formatting['border-top-width'] = WordFormatting.format_to_unit(top_width, 'eop')
            if top_color is not None and top_color != 'auto':
                formatting['border-top-color'] = WordFormatting.format_color(top_color)

        bottom = borders_element.find_child_or_null("w:bottom")
        bottom_width = bottom.attributes.get('w:sz')
        bottom_space = bottom.attributes.get('w:space')
        bottom_style = bottom.attributes.get('w:val')
        bottom_border = MS_BORDER_STYLES.get(bottom_style, None)
        bottom_color = bottom.attributes.get('w:color')
        if not isinstance(bottom, NullXmlElement):
            if bottom_border is not None:
                formatting['border-bottom-style'] = bottom_border
            if bottom_width is not None:
                formatting['border-bottom-width'] = WordFormatting.format_to_unit(bottom_width, 'eop')
            if bottom_color is not None and bottom_color != 'auto':
                formatting['border-bottom-color'] = WordFormatting.format_color(bottom_color)

        left = borders_element.find_child_or_null("w:left")
        left = borders_element.find_child_or_null("w:start") if isinstance(left, NullXmlElement) else left
        left_width = left.attributes.get('w:sz')
        left_space = left.attributes.get('w:space')
        left_style = left.attributes.get('w:val')
        left_border = MS_BORDER_STYLES.get(left_style, None)
        left_color = left.attributes.get('w:color')
        if not isinstance(left, NullXmlElement):
            if left_border is not None:
                formatting['border-left-style'] = left_border
            if left_width is not None:
                formatting['border-left-width'] = WordFormatting.format_to_unit(left_width, 'eop')
            if left_color is not None and left_color != 'auto':
                formatting['border-left-color'] = WordFormatting.format_color(left_color)

        right = borders_element.find_child_or_null("w:right")
        right = borders_element.find_child_or_null("w:end") if isinstance(right, NullXmlElement) else right
        right_width = right.attributes.get('w:sz')
        right_space = right.attributes.get('w:space')
        right_style = right.attributes.get('w:val')
        right_border = MS_BORDER_STYLES.get(right_style, None)
        right_color = right.attributes.get('w:color')
        if not isinstance(right, NullXmlElement):
            if right_border is not None:
                formatting['border-right-style'] = right_border
            if right_width is not None:
                formatting['border-right-width'] = WordFormatting.format_to_unit(right_width, 'eop')
            if right_color is not None and right_color != 'auto':
                formatting['border-right-color'] = WordFormatting.format_color(right_color)

        spacing = [
            float(top_space) if top_space is not None else -1,
            float(bottom_space) if bottom_space is not None else -1,
            float(left_space) if left_space is not None else -1,
            float(right_space) if right_space is not None else -1,
        ]
        max_spacing = max(spacing)
        if max_spacing > -1:
            formatting['border-spacing'] = WordFormatting.format_to_unit(max_spacing, 'ptp')

        return formatting

    def load_global_default_style(self):
        return copy.deepcopy(self['defaults'])

    def load_node_conditional_styles(self, name):
        formatting = [self.load_blank_style()] * 12
        style_node = self.load_style_node(name)
        for tblStyle in style_node.find_children("w:tblStylePr"):
            style_id = WordFormatting.CNF_IDS[tblStyle.attributes.get("w:type", "")]
            table_style = WordFormatting.load_style(tblStyle)
            formatting[style_id] = table_style
        return formatting

    def load_node_default_style(self, name):
        if len(name) == 0:
            return self.load_blank_style()
        # Find inheritance node name
        style_node = self.load_style_node(name)
        target = style_node.find_child_or_null("w:basedOn").attributes.get("w:val", "")
        inherited_node = self.load_style_node(target)

        # Find inheritance recursively and return the merged formatting of inheritance and current
        inherited_style = WordFormatting.load_style(inherited_node)
        style_style = WordFormatting.load_style(style_node)
        return self.merge_formatting(inherited_style, style_style)

    @staticmethod
    def load_style(element):
        tblPr = element.find_child_or_null("w:tblPr")
        cell_margin = WordFormatting.load_margins(tblPr)
        tblFormatting = WordFormatting.load_tblpr(element)
        trFormatting = WordFormatting.load_trpr(element)
        tblBorder = WordFormatting.load_tblborders(element)
        ppr = WordFormatting.load_ppr(element)
        rpr = WordFormatting.load_rpr(element)
        tcpr, borders, attributes = WordFormatting.load_tcpr(element)
        tcpr.update(cell_margin)
        tblBorder.update(borders)
        return {
                "rpr": rpr,
                "ppr": ppr,
                "tcpr": tcpr,
                "tblpr": tblFormatting,
                "trpr": trFormatting,
                "borders": tblBorder,
                "attributes": attributes
        }

    @staticmethod
    def load_blank_style():
        return {
                "rpr": {},
                "ppr": {},
                "tcpr": {},
                "tblpr": {},
                "trpr": {},
                "borders": {},
                "attributes": {}
        }

    @staticmethod
    def presort_nodes(element):
        node_cache = {}
        for style_element in element.find_children("w:style"):
            style_name = style_element.attributes["w:styleId"]
            node_cache[style_name] = style_element
        return node_cache

    def _load_from_cache(self, typ, name):
        root = self.get(typ, None)
        if not root is None:
            formatting = root.get(name, None)
            if not formatting is None:
                return formatting
        return None

    def load_style_node(self, name):
        return self["style_nodes"].get(name, NULL_ELEMENT)

    def _load_from_nodes(self, typ, name):
        node = self.load_style_node(name)

        # Attempt to generate a merged version of the styles information
        inherits = node.find_child_or_null("w:basedOn").attributes.get("w:val")
        base_formatting = copy.deepcopy(self['defaults'])
        if not inherits is None:
            base_formatting.update(self._load_or_cache(typ, inherits))

        # Apply formatting here!
        tblpr = node.find_child_or_null("w:tblPr")
        base_formatting["ppr"].update(self.load_ppr(node))
        base_formatting["rpr"].update(self.load_rpr(node))
        base_formatting["ppr"].update(self.load_margins(tblpr))
        tcpr, borders, attributes = self.load_tcpr(node)
        base_formatting["attributes"].update(attributes)
        base_formatting["tcpr"].update(tcpr)
        base_formatting["tblpr"].update(self.load_tblpr(node))
        base_formatting["trpr"].update(self.load_trpr(node))
        base_formatting["borders"].update(borders)
        #print_debug(base_formatting["cnf"])

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

    def _get_default_table_style(self, name):
        node = self.load_style_node('table', name)
        tblBorder = WordFormatting.load_tblborders(node)
        return {
                "rpr": {},
                "ppr": {},
                "tcpr": {},
                "tblpr": {},
                "trpr": {},
                "borders": tblBorder,
                "attributes": {}
        }

    def _get_cnf_style(self, name, typ="table"):
        #print_debug(name)
        #print_debug(typ)
        formatting = self._get_formatting_style(name, typ)
        if typ == 'table' and not name in self['cnf_styles'] and len(formatting):
            self['cnf_styles'][name] = formatting['cnf']
        elif typ != "table":
            #print_debug('=====> {}'.format(self['cnf_styles'].get(name, {})))
            formatting['cnf'] = WordFormatting.merge_formatting(formatting.get('cnf', {}), self['cnf_styles'].get(name, {}))

        #print_debug('=====> {}'.format(formatting['cnf']))
        return formatting

    @staticmethod
    def _classify_element(element):
        if not isinstance(element, NullXmlElement):
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
        return 'null'

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

    @staticmethod
    def _find_table_root(element):
        parent_type = WordFormatting._classify_element(element)
        if parent_type == "table":
            return element

        parent = element.find_parent()
        if isinstance(parent, NullXmlElement):
            return element

        parent_type = WordFormatting._classify_element(parent)
        if parent_type == "table":
            return parent
        return WordFormatting._find_table_root(parent)

    def _find_style(self, element):
        interest_node = WordFormatting._find_table_root(element)
        return self._find_style_id(interest_node, "table")

    def _merge_cnf_ids(self, a, b):
        if len(a) + len(b) == 0:
            return ''
        a_group = [c for c in a] if len(a) else [0] * 12
        b_group = [c for c in b] if len(b) else [0] * 12
        result = ''
        for i in range(len(max(a, b))):
            v = int(a_group[i]) | int(b_group[i])
            result += str(v)
        return result

    def _find_table_cnf_id(self, element):
        table = self._find_table_root(element)

        tblLook = table.find_child_or_null("w:tblPr").find_child_or_null("w:tblLook")
        if not isinstance(tblLook, NullXmlElement):
            look = {
                "firstRow": int(tblLook.attributes.get("w:firstRow", '0')),
                "lastRow": int(tblLook.attributes.get("w:lastRow", '0')),
                "firstColumn": int(tblLook.attributes.get("w:firstColumn", '0')),
                "lastColumn": int(tblLook.attributes.get("w:lastColumn", '0')),
                "noHBand": int(tblLook.attributes.get("w:noHBand", '0')),
                "noVBand": int(tblLook.attributes.get("w:noVBand", '0')),
            }
            #print_debug(look)
            look = self._adjust_element_look(table, element, look)
            #print_debug(look)
            return '{firstRow}{lastRow}{firstColumn}{lastColumn}{noHBand}{noHBand}{noVBand}{noVBand}0000'.format(**look)
        return ''

    def _adjust_element_look(self, table, element, default_look={}):
        default_look = copy.deepcopy(default_look)
        element_id = id(element)

        table_children = [r for r in table.find_children('w:tr')]
        rows = [[c for c in r.find_children('w:tc')] for r in table_children]

        first_row = [id(c) for c in rows[0]]
        last_row = [id(c) for c in rows[-1]]

        default_look['firstRow'] = int(element_id in first_row) & default_look['firstRow']
        default_look['lastRow'] = int(element_id in last_row) & default_look['lastRow']

        first_column = [id(r[0]) for r in rows[1:]]
        last_column = [id(r[-1]) for r in rows[1:]]

        default_look['firstColumn'] = int(element_id in first_column) & default_look['firstColumn']
        default_look['lastColumn'] = int(element_id in last_column) & default_look['lastColumn']
        default_look['noVBand'] = 0

        odd_rows = get_odd_items(table_children[1:])
        odd_rows = [id(r) for r in odd_rows]
        default_look['noHBand'] = int(element_id in odd_rows) & int(not default_look['noHBand'])


        return default_look

    def _find_node_cnf_id(self, element, element_type):
        if element_type == 'paragraph':
            return element.find_child_or_null("w:pPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'character':
            return element.find_child_or_null("w:rPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'table':
            return element.find_child_or_null("w:tblPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'row':
            return element.find_child_or_null("w:trPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        return (element.find_child_or_null("w:tcPr")
                .find_child_or_null("w:cnfStyle")
                .attributes.get("w:val",
                                element.find_parent().find_child_or_null("w:trPr")
                                .find_child_or_null("w:cnfStyle")
                                .attributes.get("w:val", "")))

    def _find_inherited_cnf_id(self, element, element_type):
        if element_type == 'paragraph':
            return element.find_child_or_null("w:pPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'character':
            return element.find_child_or_null("w:rPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
        if element_type == 'cell':
            cell_cnf = element.find_child_or_null("w:tcPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
            parent = element.find_parent()
            return self._merge_cnf_ids(
                cell_cnf,
                self._find_inherited_cnf_id(parent, self._classify_element(parent))
            )
        if element_type == 'row':
            row_cnf = element.find_child_or_null("w:trPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")
            parent = element.find_parent()
            return self._merge_cnf_ids(
                row_cnf,
                self._find_inherited_cnf_id(parent, self._classify_element(parent))
            )
        return element.find_child_or_null("w:tblPr").find_child_or_null("w:cnfStyle").attributes.get("w:val", "")

    def _find_cnf_index(self, cnf):
        indx = []
        for i in range(0, len(cnf), 1):
            if cnf[i] == "1":
                indx.append(i)
        return indx

    def _collapse_cnf(self, cnf_id, formatting):
        #print_debug('~~~~~~~~')
        cnf = self.load_blank_style()
        try:
            cnf_indices = self._find_cnf_index(cnf_id)
            cnf_indices.sort(reverse=True)
            cnf_formattings = [formatting[i] for i in cnf_indices]

            #print_debug('{}'.format(formatting['cnf']))
            #print_debug('?{}'.format(cnf_indices))
            for cnf_format in cnf_formattings:
                #print_debug(cnf_format)
                cnf['ppr'].update(cnf_format['ppr'])
                cnf['rpr'].update(cnf_format['rpr'])
                cnf['tcpr'].update(cnf_format['tcpr'])
                cnf['tblpr'].update(cnf_format['tblpr'])
                cnf['trpr'].update(cnf_format['trpr'])
                cnf['borders'].update(cnf_format['borders'])
                #print_debug('CNF: {}'.format(cnf_format['borders']))
            #print_debug('{}'.format(cnf))
            #print_debug('~~~~~~~~')
        except Exception as e:
            print_debug(e)
            pass

        return cnf

    def get_element_base_formatting(self, element):
        element_type = WordFormatting._classify_element(element)
        format_id = self._find_style_id(element, element_type)
        formatting = self._get_formatting_style(format_id, element_type)

        text_style = copy.deepcopy(formatting.get('ppr', {}))
        text_style.update(formatting.get('rpr', {}))

        return {
            'text_style': text_style,
            'cell_style': formatting.get('tcpr', {}),
            'border_style': formatting.get('borders', {}),
            'table_style': formatting.get('tblpr', {}),
            'table_row_style': formatting.get('trpr', {}),
        }

    def get_element_formatting(self, element):
        format_id = self._find_style(element)
        #print_debug('==========={}==========='.format(format_id))
        # TODO: combine cnf and base formatting such that we get the definitions from the conditional styles and the element wise style.

        global_default_style = self.load_global_default_style()
        #print_debug('-----Global Default------')
        #print_debug(global_default_style)
        #print_debug('-------------------------')
        default_style = self.load_node_default_style(format_id)
        #print_debug('=====Style Default======')
        #print_debug(default_style)
        #print_debug('========================')
        conditional_style = self.get_conditional_style(element)
        #print_debug('++++++Conditional Style+++++')
        #print_debug(conditional_style)
        #print_debug('++++++++++++++++++++++++++++')
        node_style = self.load_style(element)
        #print_debug('~~~~~Node Style~~~~~~')
        #print_debug(node_style)
        #print_debug('~~~~~~~~~~~~~~~~~~~~~')

        style = self.merge_formatting(global_default_style, default_style)
        style = self.merge_formatting(style, conditional_style)
        style = self.merge_formatting(style, node_style)

        text_style = copy.deepcopy(style.get('ppr', {}))
        text_style.update(style.get('rpr', {}))

        format_item = {
            'text_style': text_style,
            'cell_style': style.get('tcpr', {}),
            'border_style': style.get('borders', {}),
            'table_style': style.get('tblpr', {}),
            'table_row_style': style.get('trpr', {}),
            "attributes": style.get('attributes', {})
        }
        #print_debug('#####Merged results######')
        #print_debug(format_item)
        #print_debug('###########')
        #print_debug('###########')

        #if is_debug_mode() and format_id == "PlainTable3":
        #    input()
        #    element_formatting = WordFormatting.merge_formatting(cnf, element_formatting)
        #    print_debug(cnf)
        #    print_debug('')
        #    print_debug(element_formatting)
        #    input()
        #if is_debug_mode() and format_id == "GridTable3":
        #    pause_debug()

        return format_item

    def get_conditional_style(self, element):
        #print_debug('++++++++++++++++++++++++++++')
        element_type = WordFormatting._classify_element(element)
        format_id = self._find_style(element)
        cnf_id = self._find_node_cnf_id(element, element_type)
        if len(cnf_id) == 0:
            cnf_id = self._find_table_cnf_id(element)

        formatting = self.load_node_conditional_styles(format_id)
        #table_conditional_style = self._collapse_cnf(table_cnf_id, formatting)
        #print_debug('Name: {} | {} => CNF ID:{} Parent ID: {}'.format(element.name, element_type, cnf_id, table_cnf_id))
        #print_debug(table_conditional_style)

        node_conditional_style = self._collapse_cnf(cnf_id, formatting)
        #print_debug(node_conditional_style)
        #merged_style = self.merge_formatting(table_conditional_style, node_conditional_style)
        #print_debug(merged_style)
        return node_conditional_style
