from nose.tools import istest, assert_equal

from mammoth import document_matchers


@istest
def equal_to_matcher_is_case_insensitive():
    matcher = document_matchers.equal_to("Heading 1")
    assert_equal(True, matcher.matches("heaDING 1"))
    assert_equal(False, matcher.matches("heaDING 2"))
