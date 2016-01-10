import os
import shutil

import bpy
from bpy_extras.io_utils import ExportHelper

from brte import engine
from brte.converters import BTFConverter

from . import pman
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
        import panda3d.core as p3d

        blender_converter = BTFConverter()
        panda_converter = converter.Converter()

        # Setup model path to find textures
        p3d.get_model_path().clear()
        p3d.get_model_path().prepend_directory(os.path.dirname(bpy.data.filepath))

        def convert_cb(data):
            panda_converter.update(data)
            #panda_converter.active_scene.ls()

            # Copy images
            for img in data.get('images', {}).values():
                src = os.path.join(os.path.dirname(bpy.data.filepath), img['uri'])
                dst = os.path.dirname(self.filepath)
                print('Copying image from "{}" to "{}"'.format(src, dst))
                shutil.copy(src, dst)

        blender_converter.convert(*self._collect_deltas(), callback=convert_cb)

        panda_converter.active_scene.write_bam_file(self.filepath)

        # Clean up the model path
        p3d.get_model_path().clear()
        return {'FINISHED'}


class CreateProject(bpy.types.Operator):
    """Setup a new project directory"""
    bl_idname = 'panda_engine.create_project'
    bl_label = 'Create New Project'

    directory = bpy.props.StringProperty(
        name='Project Directory',
        subtype='DIR_PATH',
    )

    switch_dir = bpy.props.BoolProperty(
        name='Switch to directory',
        default=True,
    )

    def execute(self, context):
        pman.create_project(self.directory)

        if self.switch_dir:
            os.chdir(self.directory)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'switch_dir')


class SwitchProject(bpy.types.Operator):
    """Switch to an existing project directory"""
    bl_idname = 'panda_engine.switch_project'
    bl_label = 'Switch Project'

    directory = bpy.props.StringProperty(
        name='Project Directory',
        subtype='DIR_PATH',
    )

    def execute(self, context):
        os.chdir(self.directory)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BuildProject(bpy.types.Operator):
    """Build the current project"""
    bl_idname = 'panda_engine.build_project'
    bl_label = 'Build Project'

    def execute(self, context):
        try:
            config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)
            pman.build(config)
            return {'FINISHED'}
        except pman.PManException as e:
            self.report({'ERROR'}, e.value)
            return {'CANCELLED'}


class RunProject(bpy.types.Operator):
    """Run the current project"""
    bl_idname = 'panda_engine.run_project'
    bl_label = 'Run Project'

    def execute(self, context):
        try:
            config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)
            pman.run(config)
            return {'FINISHED'}
        except pman.PManException as e:
            self.report({'ERROR'}, e.value)
            return {'CANCELLED'}


def menu_func_export(self, context):
    self.layout.operator(ExportBam.bl_idname, text="Panda3D (.bam)")


def register():
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
