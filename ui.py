import bpy
import os

class PandaButtonsPanel:
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    COMPAT_ENGINES = {'PANDA'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine in cls.COMPAT_ENGINES


class Panda_PT_context_material(PandaButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_context = "material"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.material or context.object) and PandaButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data
        is_sortable = len(ob.material_slots) > 1

        if ob:
            rows = 1
            if (is_sortable):
                rows = 4

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ZOOMIN', text="")
            col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")

            col.menu("MATERIAL_MT_specials", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(percentage=0.65)

        if ob:
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()

            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()

class PandaMaterial_PT_basic(PandaButtonsPanel, bpy.types.Panel):
    bl_label = "Basic Material"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and PandaButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout
        mat = context.material

        layout.label(text="Diffuse:")
        split = layout.split()
        col = split.column()
        col.prop(mat, "diffuse_color", text="")
        col = split.column()
        col.prop(mat, "diffuse_intensity", text="Intensity")

        layout.label(text="Specular:")
        split = layout.split()
        col = split.column()
        col.prop(mat, "specular_color", text="")
        col = split.column()
        col.prop(mat, "specular_intensity", text="Intensity")
        layout.prop(mat, "specular_hardness")


class PandaCamera_PT_lens(PandaButtonsPanel, bpy.types.Panel):
    bl_label = "Lens"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.camera and PandaButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        camera = context.camera

        layout.prop(camera, "type", text="")

        if camera.type == "PERSP":
            split = layout.split()
            col = split.column()
            col.prop(camera, "lens")
            col = split.column()
            col.prop(camera, "lens_unit", text="")
        elif camera.type == "ORTHO":
            layout.prop(camera, "ortho_scale")
        else:
            layout.label("Not supported")

def get_panels():
    panels = [
        "DATA_PT_camera_display",
        "DATA_PT_camera_safe_areas",
    ]

    return [getattr(bpy.types, p) for p in panels if hasattr(bpy.types, p)]


def register():
    for panel in get_panels():
        panel.COMPAT_ENGINES.add('PANDA')


def unregister():
    for panel in get_panels():
        if 'PANDA' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('PANDA')
