from nose.tools import istest, assert_equal

from mammoth.zips import uri_to_zip_entry_name


@istest
def when_path_does_not_have_leading_slash_then_path_is_resolved_relative_to_base():
    assert_equal(
        "one/two/three/four",
        uri_to_zip_entry_name("one/two", "three/four"),
    )


@istest
def when_path_has_leading_slash_then_base_is_ignored():
    assert_equal(
        "three/four",
        uri_to_zip_entry_name("one/two", "/three/four"),
    )
