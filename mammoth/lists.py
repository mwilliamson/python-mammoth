import sys


__all__ = ["filter"]

if sys.version_info[0] == 2:
    filter = filter
else:
    import builtins
    def filter(*args, **kwargs):
        return list(builtins.filter(*args, **kwargs))
