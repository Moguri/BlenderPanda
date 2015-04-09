import os
import sys

import bpy

from .BlenderRealtimeEngineAddon.engine import RealTimeEngine

path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path)


class PandaEngine(bpy.types.RenderEngine, RealTimeEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    def __init__(self):
        program = ('python2', os.path.join(path, 'gltf-viewer.py'))

        super().__init__(program)
