import os
from enum import Enum

import bpy
from . import pman

class ConfTypes(Enum):
    string = 1
    path = 2
    boolean = 3

def get_conf_prop(section, field, conf_type):
    def f(_self):
        config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)

        if conf_type == ConfTypes.string:
            value = config[section][field]
        elif conf_type == ConfTypes.path:
            # Convert from pman path to Blender path
            value = pman.get_abs_path(config, config[section][field])
            value = bpy.path.relpath(value)
        elif conf_type == ConfTypes.boolean:
            value = config[section][field]
        else:
            raise TypeError("Unexpected conf_type {}".format(conf_type))

        #print("GET CONF", section, field, value)
        return value
    return f


def set_conf_prop(section, field, conf_type=ConfTypes.string):
    def f(_self, value):
        config = pman.get_config(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else None)
        if conf_type == ConfTypes.path:
            # Convert from Blender path to pman path
            value = bpy.path.abspath(value)
            config[section][field] = pman.get_rel_path(config, value)
        else:
            config[section][field] = value
        #print("SET CONF", section, field, value)
        pman.write_config(config)
    return f


class PandaProjectSettings(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.panda_project = bpy.props.PointerProperty(
            name="Panda3D Project Settings",
            description="Panda3D project settings",
            type=cls
        )

        cls.project_name = bpy.props.StringProperty(
            name="Project Name",
            description="The name of the current project",
            get=get_conf_prop('general', 'name', ConfTypes.string),
            set=set_conf_prop('general', 'name'),
        )

        cls.render_plugin = bpy.props.StringProperty(
            name="Render Plugin",
            description="Path to a Python file containing a plugin for rendering",
            subtype='FILE_PATH',
            get=get_conf_prop('general', 'render_plugin', ConfTypes.path),
            set=set_conf_prop('general', 'render_plugin', ConfTypes.path),
        )

        cls.asset_dir = bpy.props.StringProperty(
            name="Asset Directory",
            description="The directory containing assets to be built",
            subtype='DIR_PATH',
            get=get_conf_prop('build', 'asset_dir', ConfTypes.path),
            set=set_conf_prop('build', 'asset_dir', ConfTypes.path),
        )

        cls.export_dir = bpy.props.StringProperty(
            name="Export Directory",
            description="The directory to save the built assets",
            subtype='DIR_PATH',
            get=get_conf_prop('build', 'export_dir', ConfTypes.path),
            set=set_conf_prop('build', 'export_dir', ConfTypes.path),
        )

        cls.auto_save = bpy.props.BoolProperty(
            name="Auto Save",
            description="Automatically save current blend file when running the project",
            get=get_conf_prop('run', 'auto_save', ConfTypes.boolean),
            set=set_conf_prop('run', 'auto_save'),
        )

        cls.auto_build = bpy.props.BoolProperty(
            name="Auto Build",
            description="Automatically build the project when running",
            get=get_conf_prop('run', 'auto_build', ConfTypes.boolean),
            set=set_conf_prop('run', 'auto_build'),
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.panda_project

def register():
    pass

def unregister():
    pass
