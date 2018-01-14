import os


import bpy
from .brte.brte import engine
from .brte.brte.processors import ExternalProcessor
from .brte.brte.converters import BTFConverter
from . import pman
from . import operators


class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    def __init__(self):
        try:
            config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)
        except pman.NoConfigError as _err:
            config = None
        pycmd = pman.get_python_program(config)
        path = os.path.join(os.path.dirname(__file__), 'processor_app.py')
        args = [pycmd, path, os.path.dirname(bpy.data.filepath)]

        gltf_settings = operators._GLTF_SETTINGS.copy()
        gltf_settings['images_data_storage'] = 'REFERENCE'
        gltf_settings['meshes_apply_modifiers'] = False # Cannot be done in a thread

        super().__init__(
            converter=BTFConverter(gltf_settings),
            processor=ExternalProcessor(args),
            use_bgr_texture=True
        )

    @classmethod
    def launch_game(cls):
        bpy.ops.panda_engine.run_project()
