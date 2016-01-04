from __future__ import print_function

import math
import base64
import struct

from panda3d.core import *

class Converter():
    def __init__(self):
        self.cameras = {}
        self.lights = {}
        self.mat_states = {}
        self.mat_mesh_map = {}
        self.meshes = {}
        self.nodes = {}
        self.scenes = {}

        # Scene props
        self.active_scene = NodePath(ModelRoot('default'))
        self.background_color = (0, 0, 0)
        self.active_camera = None

    def update(self, gltf_data):
        # Convert data
        for camname, gltf_cam in gltf_data.get('cameras', {}).items():
            self.load_camera(camname, gltf_cam)

        if 'extras' in gltf_data:
            for lightname, gltf_light in gltf_data['extras'].get('lights', {}).items():
                self.load_light(lightname, gltf_light)

        for matname, gltf_mat in gltf_data.get('materials', {}).items():
            self.load_material(matname, gltf_mat)

        for meshname, gltf_mesh in gltf_data.get('meshes', {}).items():
            self.load_mesh(meshname, gltf_mesh, gltf_data)

        for nodename, gltf_node in gltf_data.get('nodes', {}).items():
            node = self.nodes.get(nodename, PandaNode(nodename))
            matrix = self.load_matrix(gltf_node['matrix'])
            node.set_transform(TransformState.make_mat(matrix))
            self.nodes[nodename] = node

        # Build scenegraphs
        def add_node(root, nodeid):
            gltf_node = gltf_data['nodes'][nodeid]
            panda_node = self.nodes[nodeid]
            np = root.attach_new_node(panda_node)

            if 'meshes' in gltf_node:
                for meshid in gltf_node['meshes']:
                    mesh = self.meshes[meshid]
                    np.attach_new_node(mesh)
            if 'camera' in gltf_node:
                camid = gltf_node['camera']
                cam = self.cameras[camid]
                np.attach_new_node(cam)
            if 'extras' in gltf_node:
                if 'light' in gltf_node['extras']:
                    lightid = gltf_node['extras']['light']
                    light = self.lights[lightid]
                    lnp = np.attach_new_node(light)
                    root.set_light(lnp)

            for child_nodeid in gltf_node['children']:
                add_node(np, child_nodeid)

        for scenename, gltf_scene in gltf_data.get('scenes', {}).items():
            scene_root = NodePath(ModelRoot(scenename))

            for nodeid in gltf_scene['nodes']:
                add_node(scene_root, nodeid)

            self.scenes[scenename] = scene_root

        # Set the active scene
        sceneid = gltf_data['scene']
        self.active_scene = self.scenes[sceneid]
        if 'scenes' in gltf_data:
            gltf_scene = gltf_data['scenes'][sceneid]
            if 'extras' in gltf_scene:
                if 'background_color' in gltf_scene['extras']:
                    self.background_color = gltf_scene['extras']['background_color']
                if 'active_camera' in gltf_scene['extras']:
                    self.active_camera = gltf_scene['extras']['active_camera']

    def load_matrix(self, mat):
        lmat = LMatrix4()

        for i in range(4):
            lmat.set_row(i, LVecBase4(*mat[i * 4: i * 4 + 4]))
        return lmat

    def load_material(self, matname, gltf_mat):
        state = self.mat_states.get(matname, RenderState.make_empty())

        if matname not in self.mat_mesh_map:
            self.mat_mesh_map[matname] = []

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
            texdata = TexturePool.load_texture(tex, 0, False, LoaderOptions())
            texstage = TextureStage(str(i))
            texture_layer = gltf_mat['values']['uv_layers'][i]
            if texture_layer:
                texstage.set_texcoord_name(InternalName.get_texcoord_name(texture_layer))
            else:
                texstage.set_texcoord_name(InternalName.get_texcoord())

            tex_attrib = tex_attrib.add_on_stage(texstage, texdata)
            state = state.set_attrib(tex_attrib)

        # Remove stale meshes
        self.mat_mesh_map[matname] = [
            pair for pair in self.mat_mesh_map[matname] if pair[0] in self.meshes
        ]

        # Reload the material
        for meshname, geom_idx in self.mat_mesh_map[matname]:
            self.meshes[meshname].set_geom_state(geom_idx, state)

        self.mat_states[matname] = state

    def load_mesh(self, meshname,  gltf_mesh, gltf_data):
        node = self.meshes.get(meshname, GeomNode(meshname))

        # Clear any existing mesh data
        node.remove_all_geoms()

        # Describe the vertex data
        va = GeomVertexArrayFormat()
        va.add_column(InternalName.get_vertex(), 3, GeomEnums.NTFloat32, GeomEnums.CPoint)
        va.add_column(InternalName.get_normal(), 3, GeomEnums.NTFloat32, GeomEnums.CPoint)

        uv_layers = [i.replace('TEXCOORD_', '') for i in gltf_mesh['primitives'][0]['attributes'] if i.startswith('TEXCOORD_')]
        for uv_layer in uv_layers:
            va.add_column(InternalName.get_texcoord_name(uv_layer), 2, GeomEnums.NTFloat32, GeomEnums.CTexcoord)

        reg_format = GeomVertexFormat.register_format(GeomVertexFormat(va))
        vdata = GeomVertexData(gltf_mesh['name'], reg_format, GeomEnums.UH_stream)

        # Write the vertex data
        pacc_name = gltf_mesh['primitives'][0]['attributes']['POSITION']
        pacc = gltf_data['accessors'][pacc_name]

        handle = vdata.modify_array(0).modify_handle()
        handle.unclean_set_num_rows(pacc['count'])

        bv = gltf_data['bufferViews'][pacc['bufferView']]
        buff = gltf_data['buffers'][bv['buffer']]
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

        geom_idx = 0
        for gltf_primitive in gltf_mesh['primitives']:
            # Grab the index data
            prim = GeomTriangles(GeomEnums.UH_stream)

            iacc_name = gltf_primitive['indices']
            iacc = gltf_data['accessors'][iacc_name]

            num_verts = iacc['count']
            handle = prim.modify_vertices(num_verts).modify_handle()
            handle.unclean_set_num_rows(num_verts)

            bv = gltf_data['bufferViews'][iacc['bufferView']]
            buff = gltf_data['buffers'][bv['buffer']] 
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
            mat = self.mat_states[gltf_primitive['material']]

            # Now put it together
            geom = Geom(vdata)
            geom.add_primitive(prim)
            node.add_geom(geom, mat)

            self.mat_mesh_map[gltf_primitive['material']].append((meshname, geom_idx))
            geom_idx += 1

        self.meshes[meshname] = node

    def load_camera(self, camname, gltf_camera):
        node = self.cameras.get(camname, Camera(camname))

        if gltf_camera['type'] == 'perspective':
            gltf_lens = gltf_camera['perspective']
            lens = PerspectiveLens()
            lens.set_fov(math.degrees(gltf_lens['yfov'] * gltf_lens['aspectRatio']), math.degrees(gltf_lens['yfov']))
            lens.set_near_far(gltf_lens['znear'], gltf_lens['zfar'])
            lens.set_view_vector((0, 0, -1), (0, 1, 0))
            node.set_lens(lens)

        self.cameras[camname] = node

    def load_light(self, lightname, gltf_light):
        node = self.lights.get(lightname, None)

        # Construct a new light if needed
        # TODO handle switching light types
        if node is None:
            if gltf_light['type'] == 'point':
                node = PointLight(lightname)
            else:
                print("Unsupported light type for light with name {}: {}".format(node_name, gltf_light['type']))
                node = PandaNode(lightname)

        # Update the light
        if gltf_light['type'] == 'point':
            col = LColor(*gltf_light['point']['color'], w=1)
            att = LPoint3(
                gltf_light['point']['constantAttenuation'],
                gltf_light['point']['linearAttenuation'],
                gltf_light['point']['quadraticAttenuation']
            )
            node.set_color(col)
            node.set_attenuation(att)

        self.lights[lightname] = node
