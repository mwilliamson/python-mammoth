from nose.tools import istest, assert_equal

import spur

from .testing import test_path


_local = spur.LocalShell()

@istest
def html_is_printed_to_stdout_if_output_file_is_not_set():
    docx_path = test_path("single-paragraph.docx")
    result = _local.run(["mammoth", docx_path])
    assert_equal("", result.stderr_output)
    assert_equal("<p>Walking on imported air</p>", result.output)
