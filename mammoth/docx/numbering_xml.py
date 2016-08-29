from ..documents import numbering_level


def read_numbering_xml_element(element):
    abstract_nums = _read_abstract_nums(element)
    nums = _read_nums(element, abstract_nums)
    return Numbering(nums)


def _read_abstract_nums(element):
    abstract_num_elements = element.find_children("w:abstractNum")
    return dict(map(_read_abstract_num, abstract_num_elements))


def _read_abstract_num(element):
    abstract_num_id = element.attributes.get("w:abstractNumId")
    levels = _read_abstract_num_levels(element)
    return abstract_num_id, levels


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


def _read_nums(element, abstract_nums):
    num_elements = element.find_children("w:num")
    return dict(
        _read_num(num_element, abstract_nums)
        for num_element in num_elements
    )


def _read_num(element, abstract_nums):
    num_id = element.attributes.get("w:numId")
    abstract_num_id = element.find_child_or_null("w:abstractNumId").attributes["w:val"]
    return num_id, abstract_nums[abstract_num_id]


class Numbering(object):
    def __init__(self, nums):
        self._nums = nums
    
    def find_level(self, num_id, level):
        num = self._nums.get(num_id)
        if num is None:
            return None
        else:
            return num.get(level)
