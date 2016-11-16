from hamcrest import assert_that, contains, has_properties

from mammoth.styles.parser.tokeniser import tokenise


def test_unknown_tokens_are_tokenised():
    assert_tokens("~", is_token("unknown", "~"))


def test_empty_string_is_tokenised_to_end_of_file_token():
    assert_tokens("")


def test_whitespace_is_tokenised():
    assert_tokens(" \t\t  ", is_token("whitespace", " \t\t  "))


def test_identifiers_are_tokenised():
    assert_tokens("Overture", is_token("identifier", "Overture"))


def test_integers_are_tokenised():
    assert_tokens("123", is_token("integer", "123"))


def test_strings_are_tokenised():
    assert_tokens("'Tristan'", is_token("string", "'Tristan'"))


def test_unterminated_strings_are_tokenised():
    assert_tokens("'Tristan", is_token("unterminated string", "'Tristan"))


def test_arrows_are_tokenised():
    assert_tokens("=>=>", is_token("arrow", "=>"), is_token("arrow", "=>"))


def test_classes_are_tokenised():
    assert_tokens(".overture", is_token("class name", ".overture"))


def test_colons_are_tokenised():
    assert_tokens("::", is_token("colon", ":"), is_token("colon", ":"))


def test_greater_thans_are_tokenised():
    assert_tokens(">>", is_token("greater than", ">"), is_token("greater than", ">"))


def test_equals_are_tokenised():
    assert_tokens("==", is_token("equals", "="), is_token("equals", "="))


def test_open_parens_are_tokenised():
    assert_tokens("((", is_token("open paren", "("), is_token("open paren", "("))


def test_close_parens_are_tokenised():
    assert_tokens("))", is_token("close paren", ")"), is_token("close paren", ")"))


def test_open_square_brackets_are_tokenised():
    assert_tokens("[[", is_token("open square bracket", "["), is_token("open square bracket", "["))


def test_close_square_brackets_are_tokenised():
    assert_tokens("]]", is_token("close square bracket", "]"), is_token("close square bracket", "]"))


def test_choices_are_tokenised():
    assert_tokens("||", is_token("choice", "|"), is_token("choice", "|"))


def test_can_tokenise_multiple_tokens():
    assert_tokens("The Magic Position",
        is_token("identifier", "The"),
        is_token("whitespace", " "),
        is_token("identifier", "Magic"),
        is_token("whitespace", " "),
        is_token("identifier", "Position"),
    )


def assert_tokens(string, *expected):
    expected = list(expected)
    expected.append(is_token("end", ""))
    assert_that(
        tokenise(string),
        contains(*expected),
    )


def is_token(token_type, value):
    return has_properties(
        type=token_type,
        value=value,
    )
