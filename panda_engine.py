import os
import sys


if "bpy" in locals():
    import imp
    imp.reload(engine)
    imp.reload(processor)
else:
    import bpy
    from .brte.brte import engine
    from .brte.brte.processors import DoubleBuffer
    from . import processor



class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    _processor = None

    def __init__(self):
        if PandaEngine._processor is None:
            self.display = DoubleBuffer(3, self.draw_callback)
            PandaEngine._processor = processor.PandaProcessor(self.display)
        PandaEngine._processor.reset(os.path.dirname(bpy.data.filepath))

        self.processor = PandaEngine._processor
        super().__init__(processor=PandaEngine._processor)

    def view_draw(self, context):
        """ Called when viewport settings change """
        self.processor.render_frame(context)

    def main_update(self, dt):
        super().main_update(dt)
        self.draw_callback()
