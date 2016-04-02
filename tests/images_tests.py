from nose.tools import istest

import mammoth


@istest
def inline_is_available_as_alias_of_img_element():
    assert mammoth.images.inline is mammoth.images.img_element
