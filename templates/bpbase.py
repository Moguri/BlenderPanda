from .rendermanager import create_render_manager
from . import pman
import panda3d.core as p3d


class BPBase:
    def __init__(self, base, config):
        self.rendermanager = create_render_manager(base, config)


def init(base):
    config = pman.get_config()
    if base.appRunner is None and config.getboolean('run', 'auto_build'):
        pman.build(config)

    # Add export directory to model path
    exportdir = pman.get_abs_path(config, config.get('build', 'export_dir'))
    p3d.get_model_path().prepend_directory(exportdir)

    base._bpbase = BPBase(base, config)
