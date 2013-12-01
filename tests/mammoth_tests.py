from nose.tools import istest, assert_equal

from .testing import test_path

import mammoth


@istest
def docx_containing_one_paragraph_is_converted_to_single_p_element():
    with open(test_path("single-paragraph.docx")) as fileobj:
        result = mammoth.convert_to_html(fileobj=fileobj)
        assert_equal("<p>Walking on imported air</p>", result.value)
        assert_equal([], result.messages)
