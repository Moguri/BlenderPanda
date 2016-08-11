import os
import sys


import bpy
from .brte.brte import engine
from .brte.brte.processors import ExternalProcessor

import pman



class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    def __init__(self):
        try:
            config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)
        except pman.NoConfigError as e:
            config = None
        pycmd = pman.get_python_program(config)
        path = os.path.join(os.path.dirname(__file__), 'processor_app.py')
        args = [pycmd, path, os.path.dirname(bpy.data.filepath)]

        super().__init__(
            processor=ExternalProcessor(args),
            use_bgr_texture=True
        )

    @classmethod
    def launch_game(cls):
        bpy.ops.panda_engine.run_project()

