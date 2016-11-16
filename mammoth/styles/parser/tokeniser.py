import collections
import re


Token = collections.namedtuple("Token", ["character_index", "type", "value"])


def regex_tokeniser(rules):
    rules = [(token_type, _to_regex(regex)) for token_type, regex in rules]
    rules.append(("unknown", re.compile(".")))
    
    def tokenise(value):
        tokens = []
        index = 0
        while index < len(value):
            for token_type, regex in rules:
                match = regex.match(value, index)
                if match is not None:
                    tokens.append(Token(index, token_type, match.group(0)))
                    index = match.end()
                    break
            else:
                # Should be impossible
                raise Exception("Remaining: " + value[index:])

        tokens.append(Token(index, "end", ""))

        return tokens

    return tokenise
    

def _to_regex(value):
    if hasattr(value, "match"):
        return value
    else:
        return re.compile(value)


_string_prefix = r"'(?:\\.|[^'])*"

tokenise = regex_tokeniser([
    ("identifier", r"[a-zA-Z][a-zA-Z0-9\-]*"),
    ("class name", r"\.(?:[a-zA-Z0-9\-]|\\.)+"),
    ("colon", r":"),
    ("greater than", r">"),
    ("whitespace", r"\s+"),
    ("arrow", r"=>"),
    ("equals", r"="),
    ("open paren", r"\("),
    ("close paren", r"\)"),
    ("open square bracket", r"\["),
    ("close square bracket", r"\]"),
    ("string", _string_prefix + "'"),
    ("unterminated string", _string_prefix),
    ("integer", r"([0-9]+)"),
    ("choice", r"\|"),
    ("bang", r"(!)"),
])
