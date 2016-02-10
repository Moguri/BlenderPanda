from importlib.machinery import SourceFileLoader

from . import pman


class BasicRenderManager:
    def __init__(self, base):
        import panda3d.core as p3d

        self.base = base
        self.base.render.set_shader_auto()


def create_render_manager(base, config=None):
    if config is None:
        try:
            config = pman.get_config()
        except pman.NoConfigError:
            print("RenderManager: Could not find pman config, falling back to basic plugin")
            config = None

    renderplugin = config['general']['render_plugin'] if config else ''

    if not renderplugin:
        return BasicRenderManager(base)

    path = pman.get_abs_path(config, renderplugin)
    mod = SourceFileLoader("render_plugin", path).load_module()

    return mod.get_plugin()(base)

