from ... import html_paths
from .tokeniser import TokenType
from .token_parser import parse_identifier, parse_string, try_parse_class_name


def parse_html_path(tokens):
    if tokens.try_skip(TokenType.SYMBOL, "!"):
        return html_paths.ignore
    else:
        return html_paths.path(_parse_html_path_elements(tokens))


def _parse_html_path_elements(tokens):
    elements = []
    
    if tokens.peek_token_type() == TokenType.IDENTIFIER:
        elements.append(_parse_element(tokens))
        
        while tokens.try_skip_many(((TokenType.WHITESPACE, None), (TokenType.SYMBOL, ">"))):
            tokens.skip(TokenType.WHITESPACE)
            elements.append(_parse_element(tokens))
        
    return elements


def _parse_element(tokens):
    tag_names = _parse_tag_names(tokens)
    class_names = _parse_class_names(tokens)
    is_fresh = _parse_is_fresh(tokens)
    separator = _parse_separator(tokens)
    
    return html_paths.element(
        tag_names,
        class_names=class_names,
        fresh=is_fresh,
        separator=separator,
    )


def _parse_tag_names(tokens):
    tag_names = [parse_identifier(tokens)]
    
    while tokens.try_skip(TokenType.SYMBOL, "|"):
        tag_names.append(parse_identifier(tokens))
    
    return tag_names


def _parse_class_names(tokens):
    class_names = []
    
    while True:
        class_name = try_parse_class_name(tokens)
        if class_name is None:
            break
        else:
            class_names.append(class_name)
    
    return class_names


def _parse_is_fresh(tokens):
    return tokens.try_skip_many((
        (TokenType.SYMBOL, ":"),
        (TokenType.IDENTIFIER, "fresh"),
    ))


def _parse_separator(tokens):
    is_separator = tokens.try_skip_many((
        (TokenType.SYMBOL, ":"),
        (TokenType.IDENTIFIER, "separator"),
    ))
    if is_separator:
        tokens.skip(TokenType.SYMBOL, "(")
        value = parse_string(tokens)
        tokens.skip(TokenType.SYMBOL, ")")
        return value
    else:
        return None
