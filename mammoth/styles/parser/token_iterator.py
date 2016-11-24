# TODO: check indices

class TokenIterator(object):
    def __init__(self, tokens):
        self._tokens = tokens
        self._index = 0
    
    def peek_token_type(self):
        return self._tokens[self._index].type
    
    def next_value(self, token_type):
        return self._next(token_type).value
    
    def _next(self, token_type):
        token = self._tokens[self._index]
        if token.type == token_type:
            self._index += 1
            return token
        else:
            raise self._unexpected_token_type(token_type, token)
    
    def skip(self, token_type, token_value=None):
        token = self._tokens[self._index]
        if token.type == token_type and (token_value is None or token.value == token_value):
            self._index += 1
            return True
        else:
            raise self._unexpected_token_type(token_type, token)
    
    def try_skip(self, token_type, token_value=None):
        token = self._tokens[self._index]
        if token.type == token_type and (token_value is None or token.value == token_value):
            self._index += 1
            return True
        else:
            return False
    
    def try_skip_many(self, tokens):
        start = self._index
        for token_type, token_value in tokens:
            token = self._tokens[self._index]
            if not (token.type == token_type and (token_value is None or token.value == token_value)):
                self._index = start
                return False
            else:
                self._index += 1
        
        return True
                
