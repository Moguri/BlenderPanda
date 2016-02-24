import os
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d
from blenderpanda import rendermanager

p3d.load_prc_file_data(
    '',
    'model-path {}\n'.format(os.path.join(os.path.dirname(__file__), 'assets')) + \
    'framebuffer-srgb true\n'
)

class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.accept('escape', sys.exit)

        self.rendermanager = rendermanager.create_render_manager(self)


app = GameApp()
app.run()
