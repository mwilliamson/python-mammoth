import sys


def collect(values):
    result = []
    _collect(values, result)
    return result


def _collect(values, result):
    for value in values:
        if isinstance(value, list):
            _collect(value, result)
        elif value is not None:
            result.append(value)
