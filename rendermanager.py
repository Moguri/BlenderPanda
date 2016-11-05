try:
    from importlib.machinery import SourceFileLoader
    HAS_SFL = True
except ImportError:
    import imp
    HAS_SFL = False

try:
    import pman
except ImportError:
    try:
        from . import pman
    except ImportError:
        import blenderpanda.pman as pman


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

    renderplugin = config.get('general', 'render_plugin') if config else ''

    if not renderplugin:
        return BasicRenderManager(base)

    path = pman.get_abs_path(config, renderplugin)

    if HAS_SFL:
        mod = SourceFileLoader("render_plugin", path).load_module()
    else:
        mod = imp.load_source("render_plugin", path)

    return mod.get_plugin()(base)

