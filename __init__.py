bl_info = {
    "name": "Panda3D Integration",
    "author": "Mitchell Stokes",
    "blender": (2, 74, 0),
    "location": "Info header, render engine menu",
    "description": "Run Panda3D from inside Blender",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Render"}


if "bpy" in locals():
    import imp
    unregister()
    imp.reload(pman)
    imp.reload(panda_engine)
    imp.reload(ui)
    imp.reload(operators)
    imp.reload(properties)
    imp.reload(rendermanager)
else:
    import bpy
    import sys
    import os
    # Add this folder to the path to find PyOpenGL
    sys.path.append(os.path.dirname(__file__))
    from . import pman
    from . import panda_engine
    from . import ui
    from . import operators
    from . import properties
    from . import rendermanager

@bpy.app.handlers.persistent
def load_handler(_):
    operators.update_blender_path()

def register():
    bpy.utils.register_module(__name__)
    ui.register()
    operators.register()
    properties.register()
    bpy.app.handlers.load_post.append(load_handler)


def unregister():
    bpy.utils.unregister_module(__name__)
    ui.unregister()
    operators.unregister()
    properties.unregister()
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
