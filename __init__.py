bl_info = {
    "name": "Panda3D Integration",
    "author": "Mitchell Stokes",
    "blender": (2, 74, 0),
    "location": "Info header, render engine menu",
    "description": "Run Panda3D from inside Blender",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'TESTING',
    "category": "Render"}


if "bpy" in locals():
    import imp
    unregister()
    imp.reload(pman)
    imp.reload(panda_engine)
    imp.reload(ui)
    imp.reload(operators)
    imp.reload(properties)
else:
    import bpy
    from . import pman
    from . import panda_engine
    from . import ui
    from . import operators
    from . import properties

def register():
    bpy.utils.register_module(__name__)
    ui.register()
    operators.register()
    properties.register()


def unregister():
    bpy.utils.unregister_module(__name__)
    ui.unregister()
    operators.unregister()
    properties.unregister()
