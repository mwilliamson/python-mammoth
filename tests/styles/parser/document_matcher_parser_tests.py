from nose.tools import istest, assert_equal

from mammoth import documents, document_matchers
from mammoth.styles.parser.document_matcher_parser import parse_document_matcher
from mammoth.styles.parser.errors import LineParseError
from mammoth.styles.parser.tokeniser import tokenise
from mammoth.styles.parser.token_iterator import TokenIterator
from ...testing import assert_raises


@istest
def unrecognised_document_element_raises_error():
    error = assert_raises(LineParseError, lambda: read_document_matcher("x"))
    assert_equal("Unrecognised document element: x", str(error))


@istest
def reads_plain_paragraph():
    assert_equal(
        document_matchers.paragraph(),
        read_document_matcher("p")
    )


@istest
def reads_paragraph_with_style_id():
    assert_equal(
        document_matchers.paragraph(style_id="Heading1"),
        read_document_matcher("p.Heading1")
    )


@istest
def reads_paragraph_with_exact_style_name():
    assert_equal(
        document_matchers.paragraph(style_name=document_matchers.equal_to("Heading 1")),
        read_document_matcher("p[style-name='Heading 1']")
    )


@istest
def reads_paragraph_with_style_name_prefix():
    assert_equal(
        document_matchers.paragraph(style_name=document_matchers.starts_with("Heading")),
        read_document_matcher("p[style-name^='Heading']")
    )


@istest
def unrecognised_string_matcher_raises_error():
    error = assert_raises(LineParseError, lambda: read_document_matcher("p[style-name*='Heading']"))
    assert_equal("Unrecognised string matcher: *", str(error))


@istest
def reads_paragraph_ordered_list():
    assert_equal(
        document_matchers.paragraph(numbering=documents.numbering_level(1, is_ordered=True)),
        read_document_matcher("p:ordered-list(2)")
    )


@istest
def reads_paragraph_unordered_list():
    assert_equal(
        document_matchers.paragraph(numbering=documents.numbering_level(1, is_ordered=False)),
        read_document_matcher("p:unordered-list(2)")
    )


@istest
def unrecognised_list_type_raises_error():
    error = assert_raises(LineParseError, lambda: read_document_matcher("p:blah"))
    assert_equal("Unrecognised list type: blah", str(error))


@istest
def reads_plain_run():
    assert_equal(
        document_matchers.run(),
        read_document_matcher("r")
    )


@istest
def reads_run_with_style_id():
    assert_equal(
        document_matchers.run(style_id="Emphasis"),
        read_document_matcher("r.Emphasis")
    )


@istest
def reads_run_with_style_name():
    assert_equal(
        document_matchers.run(style_name=document_matchers.equal_to("Emphasis")),
        read_document_matcher("r[style-name='Emphasis']")
    )

@istest
def reads_bold():
    assert_equal(
        document_matchers.bold,
        read_document_matcher("b")
    )

@istest
def reads_italic():
    assert_equal(
        document_matchers.italic,
        read_document_matcher("i")
    )

@istest
def reads_underline():
    assert_equal(
        document_matchers.underline,
        read_document_matcher("u")
    )

@istest
def reads_strikethrough():
    assert_equal(
        document_matchers.strikethrough,
        read_document_matcher("strike")
    )

@istest
def reads_small_caps():
    assert_equal(
        document_matchers.small_caps,
        read_document_matcher("small-caps")
    )

@istest
def reads_comment_reference():
    assert_equal(
        document_matchers.comment_reference,
        read_document_matcher("comment-reference")
    )

@istest
def reads_line_breaks():
    assert_equal(
        document_matchers.line_break,
        read_document_matcher("br[type='line']"),
    )

@istest
def reads_page_breaks():
    assert_equal(
        document_matchers.page_break,
        read_document_matcher("br[type='page']"),
    )

@istest
def reads_column_breaks():
    assert_equal(
        document_matchers.column_break,
        read_document_matcher("br[type='column']"),
    )


@istest
def unrecognised_break_type_raises_error():
    error = assert_raises(LineParseError, lambda: read_document_matcher("br[type='unknownBreakType']"))
    assert_equal("Unrecognised break type: unknownBreakType", str(error))
    

def read_document_matcher(string):
    return parse_document_matcher(TokenIterator(tokenise(string)))
