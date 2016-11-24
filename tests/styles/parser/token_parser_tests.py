from nose.tools import istest, assert_equal

from mammoth.styles.parser.tokeniser import Token, TokenType
from mammoth.styles.parser.token_parser import decode_escape_sequences, parse_identifier, parse_string
from mammoth.styles.parser.token_iterator import TokenIterator


@istest
def escape_sequences_in_identifiers_are_decoded():
    assert_equal(
        ":",
        parse_identifier(TokenIterator([
            Token(0, TokenType.IDENTIFIER, r"\:"),
        ])),
    )


@istest
def escape_sequences_in_strings_are_decoded():
    assert_equal(
        "\n",
        parse_string(TokenIterator([
            Token(0, TokenType.STRING, r"'\n'"),
        ])),
    )


@istest
def line_feeds_are_decoded():
    assert_equal("\n", decode_escape_sequences(r"\n"))


@istest
def carriage_returns_are_decoded():
    assert_equal("\r", decode_escape_sequences(r"\r"))


@istest
def tabs_are_decoded():
    assert_equal("\t", decode_escape_sequences(r"\t"))


@istest
def backslashes_are_decoded():
    assert_equal("\\", decode_escape_sequences(r"\\"))


@istest
def colons_are_decoded():
    assert_equal(":", decode_escape_sequences(r"\:"))
