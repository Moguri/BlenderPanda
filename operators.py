import bpy
from bpy_extras.io_utils import ExportHelper

from brte import engine
from brte.converters import BTFConverter

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


def menu_func_export(self, context):
    self.layout.operator(ExportBam.bl_idname, text="Panda3D (.bam)")


def register():
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
