import os
import sys

path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path)
sys.path.append(os.path.join(path, 'brte'))

if "bpy" in locals():
    import imp
    imp.reload(engine)
    imp.reload(processor)
    imp.reload(converter)
else:
    import bpy
    from bpy_extras.io_utils import ExportHelper
    from brte import engine
    from brte.processors import DoubleBuffer
    from brte.converters import BTFConverter
    from . import processor
    from . import converter


class ExportBam(bpy.types.Operator, ExportHelper):
    """Export to Panda3D's BAM file format"""
    bl_idname = 'panda_engine.export_bam'
    bl_label = 'Export BAM'

    # For ExportHelper
    filename_ext = '.bam'
    filter_glob = bpy.props.StringProperty(
        default='*.bam',
        options={'HIDDEN'},
    )

    def _collect_deltas(self):
        """Return the various deltas needed by BTFConverter.convert()"""
        add_delta = {}
        update_delta = {}
        remove_delta = {}
        view_delta = {}

        for collection in [getattr(bpy.data, i) for i in engine.DEFAULT_WATCHLIST]:
            collection_name = engine.get_collection_name(collection)
            collection_set = set(collection)
            add_delta[collection_name] = collection_set

        return (add_delta, update_delta, remove_delta, view_delta)

    def execute(self, context):
        blender_converter = BTFConverter()
        panda_converter = converter.Converter()

        def convert_cb(data):
            panda_converter.update(data)
            #panda_converter.active_scene.set_shader_auto()
            panda_converter.active_scene.ls()

        blender_converter.convert(*self._collect_deltas(), convert_cb)

        panda_converter.active_scene.write_bam_file(self.filepath)
        return {'FINISHED'}

class PandaEngine(bpy.types.RenderEngine, engine.RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    _processor = None

    def __init__(self):
        if PandaEngine._processor is None:
            self.display = DoubleBuffer(3, self.draw_callback)
            PandaEngine._processor = processor.PandaProcessor(self.display)
            PandaEngine._processor.reset()

        super().__init__(processor=PandaEngine._processor)

    def view_draw(self, context):
        """ Called when viewport settings change """
        self.processor.render(context)

    def main_update(self, dt):
        super().main_update(dt)
        self.draw_callback()
