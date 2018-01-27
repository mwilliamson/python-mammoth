from nose.tools import istest, assert_equal

from mammoth import zips


@istest
def split_path_splits_zip_paths_on_last_forward_slash():
    assert_equal(("a", "b"), zips.split_path("a/b"))
    assert_equal(("a/b", "c"), zips.split_path("a/b/c"))
    assert_equal(("/a/b", "c"), zips.split_path("/a/b/c"))


@istest
def when_path_has_no_forward_slashes_then_split_path_returns_empty_dirname():
    assert_equal(("", "name"), zips.split_path("name"))


@istest
def join_path_joins_arguments_with_forward_slashes():
    assert_equal("a/b", zips.join_path("a", "b"))
    assert_equal("a/b/c", zips.join_path("a/b", "c"))
    assert_equal("/a/b/c", zips.join_path("/a/b", "c"))


@istest
def empty_parts_are_ignored_when_joining_paths():
    assert_equal("a", zips.join_path("a", ""))
    assert_equal("b", zips.join_path("", "b"))
    assert_equal("a/b", zips.join_path("a", "", "b"))
    
