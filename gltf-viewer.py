#!/usr/bin/env python2
from __future__ import print_function

import os
import sys

path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(path)

from BlenderRealtimeEngineAddon.socket_api import SocketClient

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *

from converter import Converter


loadPrcFileData('', 'window-type none')
loadPrcFileData('', 'gl-debug #t')



class Viewer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self) 

        self.view_lens = MatrixLens()
        self.view_lens.set_view_vector((0, 0, -1), (0, 1, 0))
        self.view_camera = NodePath(Camera('view'))
        self.view_camera.node().set_lens(self.view_lens)
        self.view_camera.node().set_active(True)
        self.view_camera.reparent_to(self.render)
        self.view_camera.node().set_scene(self.render)

        self.pipe = GraphicsPipeSelection.get_global_ptr().make_module_pipe('pandagl')

        self.bg = LVecBase4(0.0, 0.0, 0.0, 1.0)

        self.make_offscreen(550, 790)

        self.ready = False

        self.disableMouse()
        self.setFrameRateMeter(True)


        self.converter = Converter()
        self.converter.scene_root.reparent_to(self.render)

        self.render.setShaderAuto()

        self.socket_handler = SocketClient(self)
    
        def handle_socket(task):
            self.socket_handler.run()
            return task.cont
        self.taskMgr.add(handle_socket, 'Handle Socket')

    def make_offscreen(self, sx, sy):
        sx = Texture.up_to_power_2(sx)
        sy = Texture.up_to_power_2(sy)

        self.graphicsEngine.remove_all_windows()
        self.win = None
        self.texture = None
        self.view_region = None

        fbprops = FrameBufferProperties(FrameBufferProperties.get_default())
        fbprops.set_alpha_bits(0)
        wp = WindowProperties.size(sx, sy)
        flags = GraphicsPipe.BF_refuse_window
        self.win = self.graphicsEngine.make_output(self.pipe,
                                                   'window',
                                                   0,
                                                   fbprops,
                                                   wp,
                                                   flags)


        dr = self.win.make_mono_display_region()
        dr.set_camera(self.view_camera)
        dr.set_active(True)
        dr.set_clear_color_active(True)
        dr.set_clear_color(self.bg)
        dr.set_clear_depth(1.0)
        dr.set_clear_depth_active(True)
        self.view_region = dr
        self.graphicsEngine.open_windows()

        self.texture = Texture()
        self.win.addRenderTexture(self.texture, GraphicsOutput.RTM_copy_ram)

    def handle_projection(self, mat):
        mat = self.converter.load_matrix(mat)
        self.view_lens.set_user_mat(mat)
        self.view_lens.set_view_mat(Mat4.ident_mat())

    def handle_view(self, mat):
        pass
        #mat = self.converter.load_matrix(data['data'])
        # print('view update', mat)
        #self.view_lens.set_view_mat(mat)

    def handle_viewport(self, width, height):
        self.make_offscreen(width, height)

    def handle_gltf(self, data):
        self.converter.update(data)
        bg = self.converter.background_color
        self.bg = LVecBase4(LVecBase4(bg[0], bg[1], bg[2], 1))
        self.view_region.set_clear_color(self.bg)

    def get_render_image(self):
        self.graphicsEngine.render_frame()
        #self.texture.write('tex.png')
        return self.texture.getRamImage().get_data(), self.texture.get_x_size(), self.texture.get_y_size()


if __name__ == '__main__':
    app = Viewer()
    app.run()
