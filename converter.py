from __future__ import print_function

import math
import base64
import struct

from panda3d.core import *

class Converter():
    def __init__(self):
        self.mat_states = {'': RenderState.make_empty()}
        self.cameras = {}
        self.meshes = {}
        self.nodes = {}
        self.gltf_data = {}

        # Create scene root
        root = ModelRoot('root')
        self.scene_root = NodePath(root)

        # Scene props
        self.background_color = (0, 0, 0)
        self.active_camera = None

    def update(self, gltf_data):
        if not self.gltf_data:
            self.gltf_data = gltf_data
        else:
            for i in self.gltf_data.keys():
                if hasattr(self.gltf_data[i], 'update'):
                    self.gltf_data[i].update(gltf_data[i])
                else:
                    self.gltf_data[i] = gltf_data[i]
        gltf_data = self.gltf_data
        gltf_scene = gltf_data['scenes'][gltf_data['scene']]
        self.background_color = gltf_scene['extras']['background_color']
        self.active_camera = gltf_scene['extras']['active_camera']

        # For now blow away the scene and rebuild it
        for child in self.scene_root.get_children():
            child.remove_node()
        self.mat_states = {'': RenderState.make_empty()}
        self.cameras = {}

        root = self.scene_root.node()
        for gltf_node in [gltf_data['nodes'][i] for i in gltf_scene['nodes']]:
            if 'meshes' in gltf_node:
                node = GeomNode(gltf_node['name'])
                gltf_mesh = gltf_data['meshes'][gltf_node['meshes'][0]]
                self.load_mesh(node, gltf_mesh)
            elif 'camera' in gltf_node:
                node = Camera(gltf_node['name'])
                gltf_camera = gltf_data['cameras'][gltf_node['camera']]
                self.load_camera(node, gltf_camera, gltf_node['camera'])
            elif 'extras' in gltf_node and 'light' in gltf_node['extras']:
                gltf_light = gltf_data['extras']['lights'][gltf_node['extras']['light']]
                if gltf_light['type'] == 'point':
                    node = PointLight(gltf_node['name'])
                    self.load_light(node, gltf_light)
                else:
                    print("Unsupported light type for light with name {}: {}".format(gltf_node['name'], gltf_light['type']))
                    node = PandaNode(gltf_node['name'])
            else:
                print("Unsupported type for object with name {}: {}".format(gltf_node['name'], gltf_node))
                node = PandaNode(gltf_node['name'])

            root.add_child(node)

            matrix = self.load_matrix(gltf_node['matrix'])
            node.set_transform(TransformState.make_mat(matrix))

    def load_matrix(self, mat):
        lmat = LMatrix4()

        for i in range(4):
            lmat.set_row(i, LVecBase4(*mat[i * 4: i * 4 + 4]))
        return lmat

    def load_material(self, matname):
        matid = matname
        if matid in self.mat_states:
            return self.mat_states[matid]

        gltf_mat = self.gltf_data['materials'][matname]
        state = RenderState.make_empty()
        pmat = Material()
        pmat.set_shininess(gltf_mat['values']['shininess'])
       
        diffuse = LColor(*gltf_mat['values']['diffuse'])
        pmat.set_diffuse(diffuse)

        specular = LColor(*gltf_mat['values']['specular'])
        pmat.set_specular(specular)

        #ambient = LColor(*mat['diffuse_color'], w=1)
        #ambient *= mat['ambient']
        #ambient.w = mat['alpha']
        #pmat.set_ambient(ambient)
        #pmat.set_ambient(diffuse)

        #emit = LColor(*mat['diffuse_color'], w=1)
        #emit *= mat['emit']
        #emit.w = mat['alpha']
        #pmat.set_ambient(emit)

        state = state.set_attrib(MaterialAttrib.make(pmat))

        #if mat['use_transparency']:
        #    state = state.set_attrib(TransparencyAttrib.make(TransparencyAttrib.M_alpha))

        for i, tex in enumerate(gltf_mat['values']['textures']):
            tex_attrib = TextureAttrib.make()
            texdata = loader.loadTexture(tex)
            texstage = TextureStage(str(i))
            texture_layer = gltf_mat['values']['uv_layers'][i]
            print(tex, texdata, texture_layer)
            if texture_layer:
                texstage.set_texcoord_name(InternalName.get_texcoord_name(texture_layer))
            else:
                texstage.set_texcoord_name(InternalName.get_texcoord())

            texstage.set_mode(TextureStage.MReplace)

            tex_attrib = tex_attrib.add_on_stage(texstage, texdata)
            state = state.set_attrib(tex_attrib)

        self.mat_states[matid] = state
        return state

    def load_mesh(self, node, mesh):
        # Describe the vertex data
        va = GeomVertexArrayFormat()
        va.add_column(InternalName.get_vertex(), 3, GeomEnums.NTFloat32, GeomEnums.CPoint)
        va.add_column(InternalName.get_normal(), 3, GeomEnums.NTFloat32, GeomEnums.CPoint)

        uv_layers = [i.replace('TEXCOORD_', '') for i in mesh['primitives'][0]['attributes'] if i.startswith('TEXCOORD_')]
        for uv_layer in uv_layers:
            va.add_column(InternalName.get_texcoord_name(uv_layer), 2, GeomEnums.NTFloat32, GeomEnums.CTexcoord)

        reg_format = GeomVertexFormat.register_format(GeomVertexFormat(va))
        vdata = GeomVertexData(mesh['name'], reg_format, GeomEnums.UH_stream)

        # Write the vertex data
        pacc_name = mesh['primitives'][0]['attributes']['POSITION']
        pacc = self.gltf_data['accessors'][pacc_name]

        handle = vdata.modify_array(0).modify_handle()
        handle.unclean_set_num_rows(pacc['count'])

        bv = self.gltf_data['bufferViews'][pacc['bufferView']]
        buff = self.gltf_data['buffers'][bv['buffer']]
        buff_data = base64.b64decode(buff['uri'].split(',')[1])
        start = bv['byteOffset']
        end = bv['byteOffset'] + bv['byteLength']
        handle.copy_data_from(buff_data[start:end])
        handle = None
        #idx = start
        #while idx < end:
        #    s = struct.unpack_from('<ffffff', buff_data, idx)
        #    idx += 24
        #    print(s)

        for gltf_primitive in mesh['primitives']:
            # Grab the index data
            prim = GeomTriangles(GeomEnums.UH_stream)

            iacc_name = gltf_primitive['indices']
            iacc = self.gltf_data['accessors'][iacc_name]

            num_verts = iacc['count']
            handle = prim.modify_vertices(num_verts).modify_handle()
            handle.unclean_set_num_rows(num_verts)

            bv = self.gltf_data['bufferViews'][iacc['bufferView']]
            buff = self.gltf_data['buffers'][bv['buffer']] 
            buff_data = base64.b64decode(buff['uri'].split(',')[1])
            start = bv['byteOffset']
            end = bv['byteOffset'] + bv['byteLength']
            handle.copy_data_from(buff_data[start:end])
            #idx = start
            #indbuf = []
            #while idx < end:
            #    s = struct.unpack_from('<HHH', buff_data, idx)
            #    idx += 6
            #    print(s)
            #print(prim.get_max_vertex(), vdata.get_num_rows())
            handle = None

            #ss = StringStream()
            #vdata.write(ss)
            #print(ss.getData())
            #prim.write(ss, 2)
            #print(ss.getData())

            # Get a material
            mat = self.load_material(gltf_primitive['material'])

            # Now put it together
            geom = Geom(vdata)
            geom.add_primitive(prim)
            node.add_geom(geom, mat)

    def load_camera(self, node, camera, camera_name):
        if camera['type'] == 'perspective':
            gltf_lens = camera['perspective']
            lens = PerspectiveLens()
            lens.set_fov(math.degrees(gltf_lens['yfov'] * gltf_lens['aspectRatio']), math.degrees(gltf_lens['yfov']))
            lens.set_near_far(gltf_lens['znear'], gltf_lens['zfar'])
            lens.set_view_vector((0, 0, -1), (0, 1, 0))
            node.set_lens(lens)

        self.cameras[camera_name] = node

    def load_light(self, node, lamp):
        col = LColor(*lamp['point']['color'], w=1)
        node.set_color(col)

        self.scene_root.set_light(NodePath(node))
