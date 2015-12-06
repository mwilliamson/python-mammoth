from nose.tools import istest, assert_equal

from mammoth.lists import unique


@istest
def unique_of_empty_list_is_empty_list():
    assert_equal([], unique([]))


@istest
def unique_removes_duplicates_while_preserving_order():
    assert_equal(["apple", "banana"], unique(["apple", "banana", "apple"]))
