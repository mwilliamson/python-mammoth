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


if sys.version_info[0] == 2:
    map = map
    filter = filter
else:
    import builtins
    def map(*args, **kwargs):
        return list(builtins.map(*args, **kwargs))
    def filter(*args, **kwargs):
        return list(builtins.filter(*args, **kwargs))
