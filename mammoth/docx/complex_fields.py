class unknown(object):
    pass


class Hyperlink(object):
    def __init__(self, kwargs):
        self.kwargs = kwargs


def hyperlink(kwargs):
    return Hyperlink(kwargs=kwargs)
