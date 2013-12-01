from nose.tools import istest, assert_equal

from mammoth import docx, documents
from mammoth.docx.xmlparser import element as xml_element, text as xml_text
from ..testing import test_path


@istest
class ReadTests(object):
    @istest
    def can_read_document_with_single_paragraph_with_single_run_of_text(self):
        with open(test_path("single-paragraph.docx")) as fileobj:
            result = docx.read(fileobj=fileobj)
            expected_document = documents.Document([
                documents.paragraph([
                    documents.Run([
                        documents.Text("Walking on imported air")
                    ])
                ])
            ])
            assert_equal(expected_document, result.value)
