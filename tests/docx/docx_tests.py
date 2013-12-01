from nose.tools import istest, assert_equal

from mammoth import docx, documents
from ..testing import test_path


@istest
class ReadTests(object):
    @istest
    def can_read_document_with_single_paragraph_with_single_run_of_text(self):
        with open(test_path("single-paragraph.docx")) as fileobj:
            result = docx.read(fileobj=fileobj)
            expected_document = documents.document([
                documents.paragraph([
                    documents.run([
                        documents.text("Walking on imported air")
                    ])
                ])
            ])
            assert_equal(expected_document, result.value)
