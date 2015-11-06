import os
import sys

path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path)
sys.path.append(os.path.join(path, 'brte'))

if "bpy" in locals():
    import imp
    imp.reload(engine)
    imp.reload(processor)
else:
    import bpy
    from brte import engine
    from brte.processors import DoubleBuffer
    from . import processor

class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    def __init__(self):
        self.display = DoubleBuffer(3, self.draw_callback)
        p = processor.PandaProcessor(self.display)

        super().__init__(processor=p)

    def view_draw(self, context):
        """ Called when viewport settings change """
        self.processor.render(context)

    def main_update(self, dt):
        super().main_update(dt)
        self.draw_callback()
