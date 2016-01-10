class BasicRenderManager:
    def __init__(self, base):
        import panda3d.core as p3d

        self.base = base
        self.base.render.set_shader_auto()

_managers = {
}

def register_manager(name, cls):
    global _managers
    _managers[name] = cls

def unregister_manager(name):
    global _managers
    del _managers[name]

def create_render_manager(name, base):
    return _managers[name](base)

register_manager('basic', BasicRenderManager)
