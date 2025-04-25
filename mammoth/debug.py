debug_mode = False


def set_debug_mode(mode=False):
    global debug_mode
    debug_mode = mode


def is_debug_mode():
    return debug_mode


def print_and_pause(msg=''):
    print(msg)
    input()
