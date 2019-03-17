import cobble

from ..documents import numbering_level
from .styles_xml import Styles


def read_numbering_xml_element(element, styles):
    abstract_nums = _read_abstract_nums(element)
    nums = _read_nums(element)
    return Numbering(abstract_nums=abstract_nums, nums=nums, styles=styles)


def _read_abstract_nums(element):
    abstract_num_elements = element.find_children("w:abstractNum")
    return dict(map(_read_abstract_num, abstract_num_elements))


def _read_abstract_num(element):
    abstract_num_id = element.attributes.get("w:abstractNumId")
    levels = _read_abstract_num_levels(element)
    num_style_link = element.find_child_or_null("w:numStyleLink").attributes.get("w:val")
    return abstract_num_id, _AbstractNum(levels=levels, num_style_link=num_style_link)


@cobble.data
class _AbstractNum(object):
    levels = cobble.field()
    num_style_link = cobble.field()


def _read_abstract_num_levels(element):
    levels = map(_read_abstract_num_level, element.find_children("w:lvl"))
    return dict(
        (level.level_index, level)
        for level in levels
    )


def _read_abstract_num_level(element):
    level_index = element.attributes["w:ilvl"]
    num_fmt = element.find_child_or_null("w:numFmt").attributes.get("w:val")
    is_ordered = num_fmt != "bullet"
    return numbering_level(level_index, is_ordered)


def _read_nums(element):
    num_elements = element.find_children("w:num")
    return dict(
        _read_num(num_element)
        for num_element in num_elements
    )


def _read_num(element):
    num_id = element.attributes.get("w:numId")
    abstract_num_id = element.find_child_or_null("w:abstractNumId").attributes["w:val"]
    return num_id, _Num(abstract_num_id=abstract_num_id)


@cobble.data
class _Num(object):
    abstract_num_id = cobble.field()


class Numbering(object):
    def __init__(self, abstract_nums, nums, styles):
        self._abstract_nums = abstract_nums
        self._nums = nums
        self._styles = styles

    def find_level(self, num_id, level):
        num = self._nums.get(num_id)
        if num is None:
            return None
        else:
            abstract_num = self._abstract_nums[num.abstract_num_id]
            if abstract_num.num_style_link is None:
                return abstract_num.levels.get(level)
            else:
                style = self._styles.find_numbering_style_by_id(abstract_num.num_style_link)
                return self.find_level(style.num_id, level)


Numbering.EMPTY = Numbering(abstract_nums={}, nums={}, styles=Styles.EMPTY)
