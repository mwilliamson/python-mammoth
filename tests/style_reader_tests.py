from nose.tools import istest, assert_equal

from mammoth import html_paths
from mammoth.style_reader import read_html_path


@istest
class ReadHtmlPathTests(object):
    @istest
    def can_read_single_element(self):
        assert_equal(
            html_paths.path([html_paths.element("p")]),
            read_html_path("p")
        )
