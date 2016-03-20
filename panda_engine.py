import os
import sys

USE_EXTERNAL = False


if "bpy" in locals():
    import imp
    imp.reload(engine)
    if not USE_EXTERNAL:
        imp.reload(processor)
else:
    import bpy
    from .brte.brte import engine
    from .brte.brte.processors import ExternalProcessor
    if not USE_EXTERNAL:
        from . import processor



class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    _processor = None

    def __init__(self):
        if USE_EXTERNAL:
            if sys.platform == 'win32':
                pycmd = 'ppython'
            else:
                pycmd = 'python3'
            path = os.path.join(os.path.dirname(__file__), 'processor_app.py')
            args = [pycmd, path]

            super().__init__(processor=ExternalProcessor(args))
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
