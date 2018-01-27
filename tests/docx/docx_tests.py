import io
import textwrap
import zipfile

from nose.tools import istest, assert_equal

from mammoth import docx, documents, zips
from ..testing import assert_raises, test_path


@istest
class ReadTests(object):
    @istest
    def can_read_document_with_single_paragraph_with_single_run_of_text(self):
        with open(test_path("single-paragraph.docx"), "rb") as fileobj:
            result = docx.read(fileobj=fileobj)
            expected_document = documents.document([
                documents.paragraph([
                    documents.run([
                        documents.text("Walking on imported air")
                    ])
                ])
            ])
            assert_equal(expected_document, result.value)


_relationship_namespaces = {
    "r": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@istest
def main_document_is_found_using_package_relationships():
    fileobj = _create_zip({
        "word/document2.xml": textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8" ?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:body>
                    <w:p>
                        <w:r>
                            <w:t>Hello.</w:t>
                        </w:r>
                    </w:p>
                </w:body>
            </w:document>
        """),
        "_rels/.rels": textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/word/document2.xml" Id="rId1"/>
            </Relationships>
        """),
    })
    result = docx.read(fileobj=fileobj)
    expected_document = documents.document([
        documents.paragraph([
            documents.run([
                documents.text("Hello.")
            ])
        ])
    ])
    assert_equal(expected_document, result.value)


@istest
def error_is_raised_when_main_document_part_does_not_exist():
    fileobj = _create_zip({
        "_rels/.rels": textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/word/document2.xml" Id="rId1"/>
            </Relationships>
        """),
    })
    error = assert_raises(IOError, lambda: docx.read(fileobj=fileobj))
    assert_equal(
        "Could not find main document part. Are you sure this is a valid .docx file?",
        str(error),
    )

class TestPartPaths(object):
    @istest
    def main_document_part_is_found_using_package_relationships(self):
        fileobj = _create_zip({
            "word/document2.xml": " ",
            "_rels/.rels": textwrap.dedent("""\
                <?xml version="1.0" encoding="utf-8"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                    <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/word/document2.xml" Id="rId1"/>
                </Relationships>
            """),
        })
        part_paths = self._find_part_paths(fileobj)
        assert_equal("word/document2.xml", part_paths.main_document)
        
    @istest
    def when_relationship_for_main_document_cannot_be_found_then_fallback_is_used(self):
        fileobj = _create_zip({
            "word/document.xml": " ",
        })
        part_paths = self._find_part_paths(fileobj)
        assert_equal("word/document.xml", part_paths.main_document)
    
    @istest
    def comments_part_is_found_using_main_document_relationships(self):
        fileobj = _create_zip({
            "_rels/.rels": textwrap.dedent("""\
                <?xml version="1.0" encoding="utf-8"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                    <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/word/document.xml" Id="rId1"/>
                </Relationships>
            """),
            "word/document.xml": " ",
            "word/_rels/document.xml.rels": textwrap.dedent("""\
                <?xml version="1.0" encoding="utf-8"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                    <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="target-path.xml" Id="rId2"/>
                </Relationships>
            """),
            "word/target-path.xml": " "
        })
        part_paths = self._find_part_paths(fileobj)
        assert_equal("word/target-path.xml", part_paths.comments)
    
    @istest
    def when_relationship_for_comments_cannot_be_found_then_fallback_is_used(self):
        fileobj = _create_zip({
            "_rels/.rels": textwrap.dedent("""\
                <?xml version="1.0" encoding="utf-8"?>
                <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                    <Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/word/document.xml" Id="rId1"/>
                </Relationships>
            """),
            "word/document.xml": " ",
        })
        part_paths = self._find_part_paths(fileobj)
        assert_equal("word/comments.xml", part_paths.comments)
        
    
    def _find_part_paths(self, fileobj):
        return docx._find_part_paths(zips.open_zip(fileobj, "r"))


def _create_zip(files):
    fileobj = io.BytesIO()
    
    zip_file = zipfile.ZipFile(fileobj, "w")
    try:
        for name, contents in files.items():
            zip_file.writestr(name, contents)
    finally:
        zip_file.close()
    
    fileobj.seek(0)
    return fileobj
