from nose.tools import istest, assert_equal

from mammoth import style_reader
from mammoth.options import read_options, _default_style_map


@istest
def default_style_map_is_used_if_style_map_is_not_set():
    assert_equal(_default_style_map, read_options({})["style_map"])


@istest
def custom_style_mappings_are_prepended_to_default_style_mappings():
    style_map = read_options({
        "style_map": "p.SectionTitle => h2"
    })["style_map"]
    assert_equal(style_reader.read_style("p.SectionTitle => h2"), style_map[0])
    assert_equal(_default_style_map, style_map[1:])


@istest
def default_style_mappings_are_ignored_if_include_default_style_map_is_false():
    style_map = read_options({
        "style_map": "p.SectionTitle => h2",
        "include_default_style_map": False
    })["style_map"]
    assert_equal([style_reader.read_style("p.SectionTitle => h2")], style_map)
