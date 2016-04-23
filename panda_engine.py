import os
import sys

USE_EXTERNAL = True


import bpy
from .brte.brte import engine
from .brte.brte.processors import ExternalProcessor
if not USE_EXTERNAL:
    from . import processor

import pman



class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    _processor = None

    def __init__(self):
        if USE_EXTERNAL:
            try:
                config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)
            except pman.NoConfigError as e:
                config = None
            pycmd = pman.get_python_program(config)
            path = os.path.join(os.path.dirname(__file__), 'processor_app.py')
            args = [pycmd, path, os.path.dirname(bpy.data.filepath)]

            super().__init__(processor=ExternalProcessor(args), use_bgr_texture=False)
        else:
            if PandaEngine._processor is None:
                PandaEngine._processor = processor.PandaProcessor()
            PandaEngine._processor.reset(os.path.dirname(bpy.data.filepath))

            self.processor = PandaEngine._processor
            super().__init__(processor=PandaEngine._processor)

    def view_draw(self, context):
        """ Called when viewport settings change """
        if not USE_EXTERNAL:
            self.processor.render_frame(context)
        else:
            super().view_draw(context)

    def main_update(self, dt):
        super().main_update(dt)
        if not USE_EXTERNAL:
            self.draw_callback()
