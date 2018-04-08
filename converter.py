from __future__ import print_function

import math
import base64
import struct

from panda3d.core import * # pylint: disable=wildcard-import
try:
    from panda3d import bullet
    HAVE_BULLET = True
except ImportError:
    HAVE_BULLET = False


class Converter():
    def __init__(self):
        self.cameras = {}
        self.lights = {}
        self.textures = {}
        self.mat_states = {}
        self.mat_mesh_map = {}
        self.meshes = {}
        self.nodes = {}
        self.node_paths = {}
        self.scenes = {}
        self.characters = {}

        # Scene props
        self.active_scene = NodePath(ModelRoot('default'))
        self.background_color = (0, 0, 0)
        self.active_camera = None

    def update(self, gltf_data, writing_bam=False):
        #import pprint
        #pprint.pprint(gltf_data)

        # Convert data
        for camid, gltf_cam in gltf_data.get('cameras', {}).items():
            self.load_camera(camid, gltf_cam)

        if 'extensions' in gltf_data and 'KHR_materials_common' in gltf_data['extensions']:
            for lightid, gltf_light in gltf_data['extensions']['KHR_materials_common'].get('lights', {}).items():
                self.load_light(lightid, gltf_light)

        for texid, gltf_tex in gltf_data.get('textures', {}).items():
            self.load_texture(texid, gltf_tex, gltf_data)

        for matid, gltf_mat in gltf_data.get('materials', {}).items():
            self.load_material(matid, gltf_mat)

        for meshid, gltf_mesh in gltf_data.get('meshes', {}).items():
            self.load_mesh(meshid, gltf_mesh, gltf_data)

        for nodeid, gltf_node in gltf_data.get('nodes', {}).items():
            node = self.nodes.get(nodeid, PandaNode(gltf_node['name']))
            self.nodes[nodeid] = node

        # If we support writing bam 6.40, we can safely write out
        # instanced lights.  If not, we have to copy it.
        copy_lights = writing_bam and not hasattr(BamWriter, 'root_node')

        # Build scenegraphs
        def add_node(root, gltf_scene, nodeid):
            if nodeid not in gltf_data['nodes']:
                print("Could not find node with id: {}".format(nodeid))
                return

            gltf_node = gltf_data['nodes'][nodeid]
            if 'jointName' in gltf_node:
                # don't handle joints here
                return
            panda_node = self.nodes[nodeid]

            if 'extras' in gltf_scene and 'hidden_nodes' in gltf_scene['extras']:
                if nodeid in gltf_scene['extras']['hidden_nodes']:
                    panda_node = panda_node.make_copy()

            np = self.node_paths.get(nodeid, root.attach_new_node(panda_node))
            self.node_paths[nodeid] = np

            if 'meshes' in gltf_node:
                np_tmp = np

                if 'skeletons' in gltf_node:
                    char = self.characters[gltf_node['name']]
                    np_tmp = np.attach_new_node(char)

                for meshid in gltf_node['meshes']:
                    mesh = self.meshes[meshid]
                    np_tmp.attach_new_node(mesh)
            if 'camera' in gltf_node:
                camid = gltf_node['camera']
                cam = self.cameras[camid]
                np.attach_new_node(cam)
            if 'extensions' in gltf_node:
                if 'KHR_materials_common' in gltf_node['extensions']:
                    lightid = gltf_node['extensions']['KHR_materials_common']['light']
                    light = self.lights[lightid]
                    if copy_lights:
                        light = light.make_copy()
                    lnp = np.attach_new_node(light)
                    if isinstance(light, Light):
                        root.set_light(lnp)

                if HAVE_BULLET and 'BLENDER_physics' in gltf_node['extensions']:
                    phy = gltf_node['extensions']['BLENDER_physics']
                    shape = None
                    collision_shape = phy['collisionShapes'][0]
                    bounding_box = collision_shape['boundingBox']
                    radius = max(bounding_box[0], bounding_box[1]) / 2.0
                    height = bounding_box[2]
                    geomnode = None
                    static = 'static' in phy and phy['static']
                    if 'mesh' in collision_shape:
                        try:
                            geomnode = self.meshes[collision_shape['mesh']]
                        except KeyError:
                            print("Could not find physics mesh ({}) for object ({})".format(collision_shape['mesh'], nodeid))

                    shape_type = collision_shape['shapeType']
                    if shape_type == 'BOX':
                        shape = bullet.BulletBoxShape(LVector3(*bounding_box) / 2.0)
                    elif shape_type == 'SPHERE':
                        shape = bullet.BulletSphereShape(max(bounding_box) / 2.0)
                    elif shape_type == 'CAPSULE':
                        shape = bullet.BulletCapsuleShape(radius, height - 2.0 * radius, bullet.ZUp)
                    elif shape_type == 'CYLINDER':
                        shape = bullet.BulletCylinderShape(radius, height, bullet.ZUp)
                    elif shape_type == 'CONE':
                        shape = bullet.BulletConeShape(radius, height, bullet.ZUp)
                    elif shape_type == 'CONVEX_HULL':
                        if geomnode:
                            shape = bullet.BulletConvexHullShape()

                            for geom in geomnode.get_geoms():
                                shape.add_geom(geom)
                    elif shape_type == 'MESH':
                        if geomnode:
                            mesh = bullet.BulletTriangleMesh()
                            for geom in geomnode.get_geoms():
                                mesh.add_geom(geom)
                            shape = bullet.BulletTriangleMeshShape(mesh, dynamic=not static)
                    else:
                        print("Unknown collision shape ({}) for object ({})".format(shape_type, nodeid))

                    if shape is not None:
                        phynode = bullet.BulletRigidBodyNode(gltf_node['name'])
                        phynode.add_shape(shape)
                        np.attach_new_node(phynode)
                        if not static:
                            phynode.set_mass(phy['mass'])
                    else:
                        print("Could not create collision shape for object ({})".format(nodeid))
                elif not HAVE_BULLET:
                    print("Bullet is unavailable, not converting collision shape for object ({})".format(nodeid))
            if 'extras' in gltf_node:
                for key, value in gltf_node['extras'].items():
                    np.set_tag(key, str(value))


            for child_nodeid in gltf_node.get('children', []):
                add_node(np, gltf_scene, child_nodeid)

            # Handle visibility after children are loaded
            def visible_recursive(node, visible):
                if visible:
                    node.show()
                else:
                    node.hide()
                for child in node.get_children():
                    visible_recursive(child, visible)
            if 'extras' in gltf_scene and 'hidden_nodes' in gltf_scene['extras']:
                if nodeid in gltf_scene['extras']['hidden_nodes']:
                    #print('Hiding', np)
                    visible_recursive(np, False)
                else:
                    #print('Showing', np)
                    visible_recursive(np, True)

            # Check if we need to deal with negative scale values
            scale = panda_node.get_transform().get_scale()
            negscale = scale.x * scale.y * scale.z < 0
            if negscale:
                for geomnode in np.find_all_matches('**/+GeomNode'):
                    tmp = geomnode.get_parent().attach_new_node(PandaNode('ReverseCulling'))
                    tmp.set_attrib(CullFaceAttrib.make_reverse())
                    geomnode.reparent_to(tmp)

        for sceneid, gltf_scene in gltf_data.get('scenes', {}).items():
            scene_root = NodePath(ModelRoot(gltf_scene['name']))

            node_list = gltf_scene['nodes']
            if 'extras' in gltf_scene and 'hidden_nodes' in gltf_scene['extras']:
                node_list += gltf_scene['extras']['hidden_nodes']

            for nodeid in node_list:
                add_node(scene_root, gltf_scene, nodeid)

            self.scenes[sceneid] = scene_root

        # Update node transforms for glTF nodes that have a NodePath
        for nodeid, gltf_node in gltf_data.get('nodes', {}).items():
            if nodeid not in self.node_paths:
                continue
            np = self.node_paths[nodeid]
            np.set_pos(*gltf_node.get('translation', [0, 0, 0]))
            np.set_hpr(self.load_quaternion_as_hpr(gltf_node.get('rotation', [0, 0, 0, 1])))
            np.set_scale(*gltf_node.get('scale', [1, 1, 1]))


        # Set the active scene
        sceneid = gltf_data.get('scene', None)
        if sceneid in self.scenes:
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

    def load_quaternion_as_hpr(self, quaternion):
        quat = LQuaternion(quaternion[3], quaternion[0], quaternion[1], quaternion[2])
        return quat.get_hpr()

    def load_texture(self, texid, gltf_tex, gltf_data):
        if 'source' not in gltf_tex:
            print("Texture '{}' has no source, skipping".format(gltf_tex['name']))
            return

        source = gltf_data['images'][gltf_tex['source']]
        uri = Filename.fromOsSpecific(source['uri'])
        texture = TexturePool.load_texture(uri, 0, False, LoaderOptions())
        use_srgb = False
        if 'format' in gltf_tex and gltf_tex['format'] in (0x8C40, 0x8C42):
            use_srgb = True
        elif 'internalFormat' in gltf_tex and gltf_tex['internalFormat'] in (0x8C40, 0x8C42):
            use_srgb = True

        if use_srgb:
            if texture.get_num_components() == 3:
                texture.set_format(Texture.F_srgb)
            elif texture.get_num_components() == 4:
                texture.set_format(Texture.F_srgb_alpha)
        self.textures[texid] = texture

    def load_material(self, matid, gltf_mat):
        state = self.mat_states.get(matid, RenderState.make_empty())

        if matid not in self.mat_mesh_map:
            self.mat_mesh_map[matid] = []

        pmat = Material(gltf_mat['name'])
        textures = []

        if 'extensions' in gltf_mat and 'KHR_materials_common' in gltf_mat['extensions']:
            matext = gltf_mat['extensions']['KHR_materials_common']['values']
            pmat.set_shininess(matext['shininess'])

            if isinstance(matext['diffuse'], list):
                diffuse = LColor(*matext['diffuse'])
                pmat.set_diffuse(diffuse)
            else:
                textures.append(matext['diffuse'])

            if isinstance(matext['specular'], list):
                specular = LColor(*matext['specular'])
                pmat.set_specular(specular)
            else:
                textures.append(matext['specular'])

            if isinstance(matext['emission'], list):
                emission = LColor(*matext['emission'])
                pmat.set_emission(emission)
            else:
                textures.append(matext['emission'])

            ambient = LColor(*matext['ambient'])
            pmat.set_ambient(ambient)

        state = state.set_attrib(MaterialAttrib.make(pmat))

        for i, tex in enumerate(textures):
            texdata = self.textures.get(tex, None)
            if texdata is None:
                print("Could not find texture for key: {}".format(tex))
                continue

            tex_attrib = TextureAttrib.make()
            texstage = TextureStage(str(i))
            texstage.set_texcoord_name(InternalName.get_texcoord_name('0'))

            if texdata.get_num_components() == 4:
                state = state.set_attrib(TransparencyAttrib.make(TransparencyAttrib.M_alpha))

            tex_attrib = tex_attrib.add_on_stage(texstage, texdata)
            state = state.set_attrib(tex_attrib)

        # Remove stale meshes
        self.mat_mesh_map[matid] = [
            pair for pair in self.mat_mesh_map[matid] if pair[0] in self.meshes
        ]

        # Reload the material
        for meshid, geom_idx in self.mat_mesh_map[matid]:
            self.meshes[meshid].set_geom_state(geom_idx, state)

        self.mat_states[matid] = state

    def create_anim(self, character, skel_name, gltf_anim, gltf_data):
        root_bone = gltf_data['nodes'][skel_name]
        if 'extras' in gltf_data['scenes'][gltf_data['scene']]:
            fps = gltf_data['scenes'][gltf_data['scene']].get('frames_per_second', 30)
        else:
            fps = 30

        # Blender exports the same number of elements in each time parameter, so find
        # one and assume that the number of elements is the number of frames
        num_frames = [
            gltf_data['accessors'][accid]['count']
            for param, accid in gltf_anim['parameters'].items()
            if 'time_parameter' in param
        ][0]

        # Create a simpler samplers dict so we don't have to keep looking
        # up parameters
        samplers = {
            samplerid: gltf_anim['parameters'][sampler['output']]
            for samplerid, sampler in gltf_anim['samplers'].items()
        }

        bundle_name = '_'.join(gltf_anim['name'].split('_')[1:])
        bundle = AnimBundle(bundle_name, fps, num_frames)
        skeleton = AnimGroup(bundle, '<skeleton>')

        def create_anim_channel(parent, boneid):
            bone = gltf_data['nodes'][boneid]
            channels = [chan for chan in gltf_anim['channels'] if chan['target']['id'] == boneid]

            group = AnimChannelMatrixXfmTable(parent, bone['name'])

            def extract_chan_data(path):
                vals = []
                accessors = [
                    gltf_data['accessors'][samplers[chan['sampler']]]
                    for chan in channels
                    if chan['target']['path'] == path
                ]

                if not accessors:
                    return vals

                acc = accessors[0]

                buff_view = gltf_data['bufferViews'][acc['bufferView']]
                buff = gltf_data['buffers'][buff_view['buffer']]
                buff_data = base64.b64decode(buff['uri'].split(',')[1])
                start = buff_view['byteOffset']
                end = buff_view['byteOffset'] + buff_view['byteLength']

                if path == 'rotation':
                    data = [struct.unpack_from('<ffff', buff_data, idx) for idx in range(start, end, 4 * 4)]
                    vals += [
                        [i[0] for i in data],
                        [i[1] for i in data],
                        [i[2] for i in data],
                        [i[3] for i in data]
                    ]
                else:
                    data = [struct.unpack_from('<fff', buff_data, idx) for idx in range(start, end, 3 * 4)]
                    vals += [
                        [i[0] for i in data],
                        [i[1] for i in data],
                        [i[2] for i in data]
                    ]

                return vals

            loc_vals = extract_chan_data('translation')
            rot_vals = extract_chan_data('rotation')
            scale_vals = extract_chan_data('scale')

            if loc_vals:
                group.set_table(b'x', CPTAFloat(PTAFloat(loc_vals[0])))
                group.set_table(b'y', CPTAFloat(PTAFloat(loc_vals[1])))
                group.set_table(b'z', CPTAFloat(PTAFloat(loc_vals[2])))

            if rot_vals:
                tableh = PTAFloat.empty_array(num_frames)
                tablep = PTAFloat.empty_array(num_frames)
                tabler = PTAFloat.empty_array(num_frames)
                for i in range(num_frames):
                    quat = LQuaternion(rot_vals[3][i], rot_vals[0][i], rot_vals[1][i], rot_vals[2][i])
                    hpr = quat.get_hpr()
                    tableh.set_element(i, hpr.get_x())
                    tablep.set_element(i, hpr.get_y())
                    tabler.set_element(i, hpr.get_z())
                group.set_table(b'h', CPTAFloat(tableh))
                group.set_table(b'p', CPTAFloat(tablep))
                group.set_table(b'r', CPTAFloat(tabler))

            if scale_vals:
                group.set_table(b'i', CPTAFloat(PTAFloat(scale_vals[0])))
                group.set_table(b'j', CPTAFloat(PTAFloat(scale_vals[1])))
                group.set_table(b'k', CPTAFloat(PTAFloat(scale_vals[2])))


            for childid in bone.get('children', []):
                create_anim_channel(group, childid)

        create_anim_channel(skeleton, skel_name)
        character.add_child(AnimBundleNode(root_bone['name'], bundle))

    def create_character(self, gltf_node, gltf_skin, gltf_mesh, gltf_data):
        #print("Creating skinned mesh for", gltf_mesh['name'])
        skel_name = gltf_node['skeletons'][0]
        root = gltf_data['nodes'][skel_name]

        character = Character(gltf_mesh['name'])
        bundle = character.get_bundle(0)
        skeleton = PartGroup(bundle, "<skeleton>")
        jvtmap = {}

        bind_mats = []
        ibmacc = gltf_data['accessors'][gltf_skin['inverseBindMatrices']]
        ibmbv = gltf_data['bufferViews'][ibmacc['bufferView']]
        ibmbuff = gltf_data['buffers'][ibmbv['buffer']]
        ibmdata = base64.b64decode(ibmbuff['uri'].split(',')[1])

        for i in range(ibmacc['count']):
            mat = struct.unpack_from('<{}'.format('f'*16), ibmdata, i * 16 * 4)
            #print('loaded', mat)
            mat = self.load_matrix(mat)
            mat.invert_in_place()
            bind_mats.append(mat)

        def create_joint(parent, node, transform):
            #print("Creating joint for:", node['name'])
            inv_transform = LMatrix4(transform)
            inv_transform.invert_in_place()
            joint_index = None
            joint_mat = LMatrix4.ident_mat()
            if node['jointName'] in gltf_skin['jointNames']:
                joint_index = gltf_skin['jointNames'].index(node['jointName'])
                joint_mat = bind_mats[joint_index]

            # glTF uses an absolute bind pose, Panda wants it local
            bind_pose = joint_mat * inv_transform
            joint = CharacterJoint(character, bundle, parent, node['name'], bind_pose)

            # Non-deforming bones are not in the skin's jointNames, don't add them to the jvtmap
            if joint_index is not None:
                jvtmap[joint_index] = JointVertexTransform(joint)


            for child in node.get('children', []):
                #print("Create joint for child", child)
                bone_node = gltf_data['nodes'][child]
                create_joint(joint, bone_node, bind_pose * transform)

        create_joint(skeleton, root, LMatrix4.ident_mat())
        #print("Adding skinned mesh to", gltf_node['name'])
        self.characters[gltf_node['name']] = character

        # convert animations
        #print("Looking for actions for", skel_name)
        anims = [
            anim
            for anim in gltf_data.get('animations', {}).values()
            if skel_name in {chan['target']['id'] for chan in anim['channels']}
        ]

        if anims:
            #print("Found anims for", gltf_node['name'])
            for gltf_anim in anims:
                #print("\t", gltf_anim['name'])
                self.create_anim(character, skel_name, gltf_anim, gltf_data)

        return jvtmap


    def load_mesh(self, meshid, gltf_mesh, gltf_data):
        node = self.meshes.get(meshid, GeomNode(gltf_mesh['name']))

        # Clear any existing mesh data
        node.remove_all_geoms()

        # Check for skinning data
        mesh_attribs = gltf_mesh['primitives'][0]['attributes']
        is_skinned = 'WEIGHT' in mesh_attribs

        # Describe the vertex data
        vert_array = GeomVertexArrayFormat()
        vert_array.add_column(InternalName.get_vertex(), 3, GeomEnums.NT_float32, GeomEnums.C_point)
        vert_array.add_column(InternalName.get_normal(), 3, GeomEnums.NT_float32, GeomEnums.C_normal)

        if is_skinned:
            # Find all nodes that use this mesh and try to find a skin
            gltf_nodes = [
                gltf_node
                for gltf_node in gltf_data['nodes'].values()
                if 'meshes' in gltf_node and meshid in gltf_node['meshes']
            ]
            gltf_node = [gltf_node for gltf_node in gltf_nodes if 'skin' in gltf_node][0]
            gltf_skin = gltf_data['skins'][gltf_node['skin']]

            jvtmap = self.create_character(gltf_node, gltf_skin, gltf_mesh, gltf_data)
            tb_va = GeomVertexArrayFormat()
            tb_va.add_column(InternalName.get_transform_blend(), 1, GeomEnums.NTUint16, GeomEnums.CIndex)
            tbtable = TransformBlendTable()

        uv_layers = [
            i.replace('TEXCOORD_', '')
            for i in gltf_mesh['primitives'][0]['attributes']
            if i.startswith('TEXCOORD_')
        ]
        for uv_layer in uv_layers:
            vert_array.add_column(InternalName.get_texcoord_name(uv_layer), 2, GeomEnums.NTFloat32, GeomEnums.CTexcoord)

        col_layers = [
            i.replace('COLOR_', '')
            for i in gltf_mesh['primitives'][0]['attributes']
            if i.startswith('COLOR_')
        ]
        for col_layer in col_layers:
            vert_array.add_column(InternalName.get_color().append(col_layer), 3, GeomEnums.NTFloat32, GeomEnums.CColor)

        #reg_format = GeomVertexFormat.register_format(GeomVertexFormat(vert_array))
        vformat = GeomVertexFormat()
        vformat.add_array(vert_array)
        if is_skinned:
            vformat.add_array(tb_va)
            aspec = GeomVertexAnimationSpec()
            aspec.set_panda()
            vformat.set_animation(aspec)
        reg_format = GeomVertexFormat.register_format(vformat)
        vdata = GeomVertexData(gltf_mesh['name'], reg_format, GeomEnums.UH_stream)
        if is_skinned:
            vdata.set_transform_blend_table(tbtable)

        # Write the vertex data
        pacc_name = mesh_attribs['POSITION']
        pacc = gltf_data['accessors'][pacc_name]

        handle = vdata.modify_array(0).modify_handle()
        handle.unclean_set_num_rows(pacc['count'])

        buff_view = gltf_data['bufferViews'][pacc['bufferView']]
        buff = gltf_data['buffers'][buff_view['buffer']]
        buff_data = base64.b64decode(buff['uri'].split(',')[1])
        start = buff_view['byteOffset']
        end = buff_view['byteOffset'] + buff_view['byteLength']
        handle.copy_data_from(buff_data[start:end])
        handle = None
        #idx = start
        #while idx < end:
        #    s = struct.unpack_from('<ffffff', buff_data, idx)
        #    idx += 24
        #    print(s)

        # Write the transform blend table
        if is_skinned:
            tdata = GeomVertexWriter(vdata, InternalName.get_transform_blend())

            sacc = gltf_data['accessors'][mesh_attribs['WEIGHT']]
            sbv = gltf_data['bufferViews'][sacc['bufferView']]
            sbuff = gltf_data['buffers'][sbv['buffer']]
            sbuff_data = base64.b64decode(sbuff['uri'].split(',')[1])

            for i in range(0, sbv['byteLength'], 32):
                joints = struct.unpack_from('<BBBB', sbuff_data, i)
                weights = struct.unpack_from('<ffff', sbuff_data, i+16)
                #print(i, joints, weights)
                tblend = TransformBlend()
                for j in range(4):
                    joint = joints[j]
                    weight = weights[j]
                    try:
                        jvt = jvtmap[joint]
                    except KeyError:
                        print("Could not find joint in jvtmap:\n\tjoint={}\n\tjvtmap={}".format(joint, jvtmap))
                        continue
                    tblend.add_transform(jvt, weight)
                tdata.add_data1i(tbtable.add_blend(tblend))

            tbtable.set_rows(SparseArray.lower_on(vdata.get_num_rows()))

        geom_idx = 0
        for gltf_primitive in gltf_mesh['primitives']:
            # Grab the index data
            prim = GeomTriangles(GeomEnums.UH_stream)

            iacc_name = gltf_primitive['indices']
            iacc = gltf_data['accessors'][iacc_name]

            num_verts = iacc['count']
            if iacc['componentType'] == 5123:
                prim.set_index_type(GeomEnums.NTUint16)
            else:
                prim.set_index_type(GeomEnums.NTUint32)
            handle = prim.modify_vertices(num_verts).modify_handle()
            handle.unclean_set_num_rows(num_verts)

            buff_view = gltf_data['bufferViews'][iacc['bufferView']]
            buff = gltf_data['buffers'][buff_view['buffer']]
            buff_data = base64.b64decode(buff['uri'].split(',')[1])
            start = buff_view['byteOffset']
            end = buff_view['byteOffset'] + buff_view['byteLength']
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
            matid = gltf_primitive.get('material', None)
            if matid is None:
                print("Warning: mesh {} has a primitive with no material, using an empty RenderState".format(meshid))
                mat = RenderState.make_empty()
            elif matid not in self.mat_states:
                print("Warning: material with name {} has no associated mat state, using an empty RenderState".format(matid))
                mat = RenderState.make_empty()
            else:
                mat = self.mat_states[gltf_primitive['material']]
                self.mat_mesh_map[gltf_primitive['material']].append((meshid, geom_idx))

            # Now put it together
            geom = Geom(vdata)
            geom.add_primitive(prim)
            node.add_geom(geom, mat)

            geom_idx += 1

        self.meshes[meshid] = node

    def load_camera(self, camid, gltf_camera):
        node = self.cameras.get(camid, Camera(gltf_camera['name']))

        if gltf_camera['type'] == 'perspective':
            gltf_lens = gltf_camera['perspective']
            lens = PerspectiveLens()
            lens.set_fov(math.degrees(gltf_lens['yfov'] * gltf_lens['aspectRatio']), math.degrees(gltf_lens['yfov']))
            lens.set_near_far(gltf_lens['znear'], gltf_lens['zfar'])
            lens.set_view_vector((0, 0, -1), (0, 1, 0))
            node.set_lens(lens)

        self.cameras[camid] = node

    def load_light(self, lightid, gltf_light):
        node = self.lights.get(lightid, None)
        lightname = gltf_light['name']

        ltype = gltf_light['type']
        # Construct a new light if needed
        # TODO handle switching light types
        if node is None:
            if ltype == 'point':
                node = PointLight(lightname)
            elif ltype == 'directional':
                node = DirectionalLight(lightname)
                node.set_direction((0, 0, -1))
            elif ltype == 'spot':
                node = Spotlight(lightname)
            else:
                print("Unsupported light type for light with name {}: {}".format(lightname, gltf_light['type']))
                node = PandaNode(lightname)

        # Update the light
        if ltype == 'unsupported':
            lightprops = {}
        else:
            lightprops = gltf_light[ltype]

        if ltype in ('point', 'directional', 'spot'):
            node.set_color(LColor(*lightprops['color'], w=1))

        if ltype in ('point', 'spot'):
            att = LPoint3(
                lightprops['constantAttenuation'],
                lightprops['linearAttenuation'],
                lightprops['quadraticAttenuation']
            )
            node.set_attenuation(att)

        self.lights[lightid] = node


def main():
    import sys
    import json

    # TODO better arg parsing and help/usage display
    if len(sys.argv) < 2:
        print("Missing glTF srouce file argument")
    elif len(sys.argv) < 3:
        print("Missing bam destination file argument")

    with open(sys.argv[1]) as f:
        gltf_data = json.load(f)

    dstfname = Filename.fromOsSpecific(sys.argv[2])
    get_model_path().prepend_directory(dstfname.getDirname())

    converter = Converter()
    converter.update(gltf_data, writing_bam=True)

    #converter.active_scene.ls()

    converter.active_scene.write_bam_file(dstfname)


if __name__ == '__main__':
    main()
