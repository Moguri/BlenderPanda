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
    imp.reload(panda_engine)
else:
    import bpy
    from . import panda_engine

import bl_ui

def register():
    panels = [getattr(bpy.types, t) for t in dir(bpy.types) if 'PT' in t]
    for panel in panels:
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_GAME' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.add('PANDA')

    bpy.utils.register_module(__name__)


def unregister():
    panels = [getattr(bpy.types, t) for t in dir(bpy.types) if 'PT' in t]
    for panel in panels:
        if hasattr(panel, 'COMPAT_ENGINES') and 'RTE_FRAMEWORK' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('PANDA')

    bpy.utils.unregister_module(__name__)
