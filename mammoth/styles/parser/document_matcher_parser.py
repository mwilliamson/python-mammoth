from ... import documents, document_matchers
from .errors import LineParseError
from .tokeniser import TokenType
from .token_parser import try_parse_class_name, parse_string


def parse_document_matcher(tokens):
    if tokens.try_skip(TokenType.IDENTIFIER, "p"):
        style_id = try_parse_class_name(tokens)
        style_name = _parse_style_name(tokens)
        numbering = _parse_numbering(tokens)
        
        return document_matchers.paragraph(
            style_id=style_id,
            style_name=style_name,
            numbering=numbering,
        )
        
    elif tokens.try_skip(TokenType.IDENTIFIER, "r"):
        style_id = try_parse_class_name(tokens)
        style_name = _parse_style_name(tokens)
        
        return document_matchers.run(
            style_id=style_id,
            style_name=style_name,
        )
    
    elif tokens.try_skip(TokenType.IDENTIFIER, "b"):
        return document_matchers.bold
    
    elif tokens.try_skip(TokenType.IDENTIFIER, "i"):
        return document_matchers.italic
    
    elif tokens.try_skip(TokenType.IDENTIFIER, "u"):
        return document_matchers.underline
    
    elif tokens.try_skip(TokenType.IDENTIFIER, "strike"):
        return document_matchers.strikethrough
    
    elif tokens.try_skip(TokenType.IDENTIFIER, "comment-reference"):
        return document_matchers.comment_reference

    else:
        raise LineParseError("Unrecognised document element: {0}".format(tokens.next_value(TokenType.IDENTIFIER)))

def _parse_style_name(tokens):
    if tokens.try_skip(TokenType.SYMBOL, "["):
        tokens.skip(TokenType.IDENTIFIER, "style-name")
        tokens.skip(TokenType.SYMBOL, "=")
        name = parse_string(tokens)
        tokens.skip(TokenType.SYMBOL, "]")
        return name
    else:
        return None


def _parse_numbering(tokens):
    if tokens.try_skip(TokenType.SYMBOL, ":"):
        is_ordered = _parse_list_type(tokens)
        tokens.skip(TokenType.SYMBOL, "(")
        level = int(tokens.next_value(TokenType.INTEGER)) - 1
        tokens.skip(TokenType.SYMBOL, ")")
        return documents.numbering_level(level, is_ordered=is_ordered)


def _parse_list_type(tokens):
    list_type = tokens.next_value(TokenType.IDENTIFIER)
    if list_type == "ordered-list":
        return True
    elif list_type == "unordered-list":
        return False
    else:
        pass
        # TODO: raise
