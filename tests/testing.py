import os

from nose.tools import nottest


@nottest
def test_path(path):
    this_dir = os.path.dirname(__file__)
    return os.path.join(this_dir, "test-data", path)


def assert_raises(exception, func):
    try:
        func()
        assert False, "Expected " + exception.__name__
    except exception as error:
        return error
    
