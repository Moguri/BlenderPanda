from .rendermanager import create_render_manager


class BPBase:
    def __init__(self, base):
        self.rendermanager = create_render_manager(base)


def init(base):
    base._bpbase = BPBase(base)
