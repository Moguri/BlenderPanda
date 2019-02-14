import struct
import sys


from OpenGL import GL


import bpy


class PandaEngine(bpy.types.RenderEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

    def __init__(self):
        self.tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGB8, 1, 1, 0,
            GL.GL_RGB, GL.GL_UNSIGNED_BYTE, struct.pack('=BBB', 0, 0, 0)
        )

    def _draw_texture(self):
        GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        # image_format = GL.GL_BGR
        # GL.glTexImage2D(
        #     GL.GL_TEXTURE_2D, 0, GL.GL_RGB8, image_ref[0], image_ref[1], 0,
        #     GL.GL_BGR, GL.GL_UNSIGNED_BYTE, image_ref[2]
        # )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_STENCIL_TEST)
        GL.glEnable(GL.GL_TEXTURE_2D)

        GL.glClearColor(0, 0, 1, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()

        GL.glBegin(GL.GL_QUADS)
        GL.glColor3f(1.0, 1.0, 1.0)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex3i(-1, -1, 0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex3i(1, -1, 0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex3i(1, 1, 0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex3i(-1, 1, 0)
        GL.glEnd()

        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

        GL.glPopAttrib()

    def view_update(self, _context):
        """ Called when the scene is changed """
        self._draw_texture()


    def view_draw(self, _context):
        """ Called when viewport settings change """
        self._draw_texture()


    @classmethod
    def launch_game(cls):
        bpy.ops.panda_engine.run_project()

    @classmethod
    def register(cls):
        render_engine_class = cls
        class LaunchGame(bpy.types.Operator):
            '''Launch the game in a separate window'''
            bl_idname = '{}.launch_game'.format(cls.bl_idname.lower())
            bl_label = 'Launch Game'

            @classmethod
            def poll(cls, context):
                return context.scene.render.engine == render_engine_class.bl_idname

            def execute(self, _context):
                try:
                    cls.launch_game()
                except Exception: #pylint:disable=broad-except
                    self.report({'ERROR'}, str(sys.exc_info()[1]))
                return {'FINISHED'}

        bpy.utils.register_class(LaunchGame)
        if not bpy.app.background:
            keymap = bpy.context.window_manager.keyconfigs.default.keymaps['Screen']
            keymap.keymap_items.new(LaunchGame.bl_idname, 'P', 'PRESS')
