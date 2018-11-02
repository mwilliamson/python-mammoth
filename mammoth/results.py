import collections

from .lists import unique


class Result(object):
    def __init__(self, value, messages):
        self.value = value
        self.messages = unique(messages)
    
    def map(self, func):
        return Result(func(self.value), self.messages)
    
    def bind(self, func):
        result = func(self.value)
        return Result(result.value, self.messages + result.messages)


Message = collections.namedtuple("Message", ["type", "message"])


def warning(message):
    return Message("warning", message)


def success(value):
    return Result(value, [])


def combine(results):
    values = []
    messages = []
    for result in results:
        if isinstance(result, list):
            values.append([r.value for r in result])
            for r in result:
                messages.extend(r.messages)
        else:
            values.append(result.value)
            messages.extend(result.messages)
        
    return Result(values, messages)


def map(func, *args):
    return combine(args).map(lambda values: func(*values))
