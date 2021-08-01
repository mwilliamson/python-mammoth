import re

from .tokeniser import TokenType


def try_parse_class_name(tokens):
    if tokens.try_skip(TokenType.SYMBOL, "."):
        return parse_identifier(tokens)


def parse_identifier(tokens):
    return decode_escape_sequences(tokens.next_value(TokenType.IDENTIFIER))


def parse_string(tokens):
    return decode_escape_sequences(tokens.next_value(TokenType.STRING)[1:-1])


_ESCAPE_SEQUENCE_REGEX = re.compile(r"\\(.)")


def decode_escape_sequences(value):
    return _ESCAPE_SEQUENCE_REGEX.sub(_decode_escape_sequence, value)
    
    
def _decode_escape_sequence(match):
    code = match.group(1)
    if code == "n":
        return "\n"

    if code == "r":
        return "\r"

    if code == "t":
        return "\t"

    return code
