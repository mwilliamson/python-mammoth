class unknown(object):
    pass


class Hyperlink(object):
    def __init__(self, href):
        self.href = href


def hyperlink(href):
    return Hyperlink(href)
