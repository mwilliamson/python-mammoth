import collections


Message = collections.namedtuple("Message", [
    #:: str
    "type",
    #:: str
    "message",
])


#:generic T
class Result(object):
    #:: Self, T, list[Message] -> none
    def __init__(self, value, messages):
        self.value = value
        self.messages = messages
    
    #:: R => Self, (T -> R) -> Result[R]
    def map(self, func):
        return Result(func(self.value), self.messages)
    
    #:: R => Self, (T -> Result[R]) -> Result[R]
    def bind(self, func):
        result = func(self.value)
        return Result(result.value, self.messages + result.messages)


#:: str -> Message
def warning(message):
    return Message("warning", message)


#:: T => T -> Result[T]
def success(value):
    return Result(value, [])


#:: T => list[Result[T]] -> Result[list[T]]
def combine(results):
    #:: list[T]
    values = []
    #:: list[Message]
    messages = []
    for result in results:
        values.append(result.value)
        for message in result.messages:
            messages.append(message)
        
    return Result(values, messages)
