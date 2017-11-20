import os
from .rendermanager import create_render_manager
from . import pman
import panda3d.core as p3d


class BPBase:
    def __init__(self, base, config):
        self.rendermanager = create_render_manager(base, config)


def init(base):
    config = pman.get_config()
    if not pman.is_frozen() and base.appRunner is None and config.getboolean('run', 'auto_build'):
        pman.build(config)

    # Add export directory to model path
    exportdir = pman.get_abs_path(config, config['build']['export_dir'])
    maindir = os.path.dirname(pman.get_abs_path(config, config['run']['main_file']))
    if pman.is_frozen():
        exportdir = os.path.relpath(exportdir, maindir)
    exportdir = p3d.Filename.from_os_specific(exportdir)
    p3d.get_model_path().prepend_directory(exportdir)

    base._bpbase = BPBase(base, config)
