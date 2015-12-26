from __future__ import unicode_literals

import io

from nose.tools import istest, assert_equal

from mammoth.docx import xmlparser as xml, office_xml


@istest
def alternate_content_is_replaced_by_contents_of_fallback():
    xml_string = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<numbering xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">' +
        '<mc:AlternateContent>' +
        '<mc:Choice Requires="w14">' +
        '<choice/>' +
        '</mc:Choice>' +
        '<mc:Fallback>' +
        '<fallback/>' +
        '</mc:Fallback>' +
        '</mc:AlternateContent>' +
        '</numbering>')
    
    result = office_xml.read(io.StringIO(xml_string))
    assert_equal([xml.element("fallback")], result.children)
