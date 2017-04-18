import os
import sys

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d
import blenderpanda


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)


app = GameApp()
app.run()
