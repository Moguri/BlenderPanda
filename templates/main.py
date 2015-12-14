import os
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d

p3d.load_prc_file_data(
    '',
    'model-path {}'.format(os.path.join(os.path.dirname(__file__), 'assets'))
)

class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.accept('escape', sys.exit)


app = GameApp()
app.run()
