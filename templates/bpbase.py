from .rendermanager import create_render_manager
from . import pman


class BPBase:
    def __init__(self, base):
        self.rendermanager = create_render_manager(base)


def init(base):
    config = pman.get_config()
    if config.getboolean('run', 'auto_build'):
        pman.build(config)
    base._bpbase = BPBase(base)
