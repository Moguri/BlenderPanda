import sys


import bpy


class PandaEngine(bpy.types.RenderEngine):
    bl_idname = 'PANDA'
    bl_label = 'Panda 3D'

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
