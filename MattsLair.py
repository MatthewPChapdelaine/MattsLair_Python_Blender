import bpy
import bmesh
import math
import os
from mathutils import Vector

# -------------------------------------------------------------------------
# 1. SCENE CLEANUP & METRIC SCALE SETUP (1 Blender Unit = 1 Unity Meter)
# -------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

collection = bpy.data.collections.new("Matts_Lair_Club")
scene.collection.children.link(collection)

def link_obj(obj):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

# -------------------------------------------------------------------------
# 2. PBR MATERIALS (Blender 3.x, 4.x & 4.2+ Cross-Version Compatible)
# -------------------------------------------------------------------------
def create_pbr_material(name, base_color, metallic=0.0, roughness=0.5, emission_color=None, emission_strength=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if emission_color and emission_strength > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission_color
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission_color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0 and hasattr(mat, "blend_method"):
        try:
            mat.blend_method = 'BLEND'
        except AttributeError:
            pass
    return mat

mat_green_metal = create_pbr_material("Mat_Green_Metal", (0.04, 0.25, 0.06, 1.0), metallic=0.85, roughness=0.25)
mat_dark_floor  = create_pbr_material("Mat_Dark_Floor",  (0.05, 0.05, 0.07, 1.0), metallic=0.2,  roughness=0.4)
mat_purple_glow = create_pbr_material("Mat_Purple_Portal", (0.12, 0.02, 0.28, 1.0), metallic=0.1, roughness=0.15,
                                      emission_color=(0.35, 0.05, 0.85, 1.0), emission_strength=2.5)
mat_neon_green  = create_pbr_material("Mat_Neon_Green",  (0.1, 1.0, 0.1, 1.0),   metallic=0.0,  roughness=0.2,
                                      emission_color=(0.15, 1.0, 0.15, 1.0), emission_strength=4.0)
mat_glass       = create_pbr_material("Mat_Skylight_Glass", (0.05, 0.1, 0.15, 1.0), metallic=0.1, roughness=0.05, alpha=0.3)

# -------------------------------------------------------------------------
# 3. MESH BUILDER HELPERS (Winding Normalization, Cap Triangulation, Box UV0)
# -------------------------------------------------------------------------
def generate_box_uv0(bm):
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        if abs(n.z) > 0.8:
            for loop in face.loops:
                co = loop.vert.co
                loop[uv_layer].uv = (co.x * 0.25, co.y * 0.25)
        else:
            tangent = Vector((-n.y, n.x, 0.0))
            if tangent.length > 1e-5:
                tangent.normalize()
            else:
                tangent = Vector((1.0, 0.0, 0.0))
            bitangent = n.cross(tangent).normalized()
            for loop in face.loops:
                co = loop.vert.co
                loop[uv_layer].uv = (co.dot(tangent) * 0.25, co.dot(bitangent) * 0.25)

def create_prism_from_2d(name, pts_2d, z_bottom, height, material):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    link_obj(obj)
    obj.data.materials.append(material)

    # Force CCW ordering so side faces wind outward before recalc
    area = 0.0
    n = len(pts_2d)
    for i in range(n):
        x1, y1 = pts_2d[i]
        x2, y2 = pts_2d[(i + 1) % n]
        area += (x1 * y2 - x2 * y1)
    ordered_pts = list(pts_2d) if area >= 0 else list(reversed(pts_2d))

    bm = bmesh.new()
    bottom_verts = [bm.verts.new((x, y, z_bottom)) for x, y in ordered_pts]
    top_verts    = [bm.verts.new((x, y, z_bottom + height)) for x, y in ordered_pts]

    bottom_face = bm.faces.new(bottom_verts[::-1])
    top_face    = bm.faces.new(top_verts)

    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bottom_verts[i], bottom_verts[j], top_verts[j], top_verts[i]])

    # Triangulate the concave caps so the FBX exporter can't pick bad diagonals
    bmesh.ops.triangulate(bm, faces=[bottom_face, top_face])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    generate_box_uv0(bm)
    bm.to_mesh(mesh)
    bm.free()
    return obj

def _wall_segment(name, p1, p2, z_bottom, wall_height, thickness, material):
    seg = Vector((p2[0] - p1[0], p2[1] - p1[1], 0.0))
    length = seg.length
    if length < 0.01:
        return None
    mid = Vector((p1[0], p1[1], 0.0)) + seg * 0.5
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mid.x, mid.y, z_bottom + wall_height * 0.5))
    wall = bpy.context.active_object
    wall.name = name
    wall.scale = (length + thickness, thickness, wall_height)
    wall.rotation_euler = (0.0, 0.0, math.atan2(seg.y, seg.x))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    wall.data.materials.append(material)
    link_obj(wall)
    return wall

def create_wall_perimeter(name, pts_2d, z_bottom, wall_height, thickness, material, open_edges=None):
    if open_edges is None:
        open_edges = set()
    n = len(pts_2d)
    for i in range(n):
        if i in open_edges:
            continue
        _wall_segment(f"{name}_Seg_{i}", pts_2d[i], pts_2d[(i + 1) % n],
                      z_bottom, wall_height, thickness, material)

def create_rail(name, p1, p2, z, height, thickness, material):
    return _wall_segment(name, p1, p2, z, height, thickness, material)

def create_stairs(name, start_pos, yaw_deg, width, total_height, run_length, steps, material):
    step_h = total_height / steps
    step_d = run_length / steps
    yaw = math.radians(yaw_deg)
    forward = Vector((math.cos(yaw), math.sin(yaw), 0.0))

    for s in range(steps):
        h = step_h * (s + 1)
        pos = Vector((start_pos[0], start_pos[1], 0.0)) + forward * (step_d * (s + 0.5))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pos.x, pos.y, start_pos[2] + h * 0.5))
        step = bpy.context.active_object
        step.name = f"{name}_Step_{s}"
        step.scale = (step_d, width, h)
        step.rotation_euler = (0.0, 0.0, yaw)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        step.data.materials.append(material)
        link_obj(step)

# -------------------------------------------------------------------------
# 4. ARCHITECTURAL ZONES
# -------------------------------------------------------------------------

# A. PURPLE PORTAL TRIANGLE (Dance Floor, DJ Stage at tip)
portal_pts = [
    (-2.0, -2.0),
    (18.0, -3.5),
    (2.0, -11.5),
    (-2.5, -6.5)
]
create_prism_from_2d("Zone_DanceFloor_Portal", portal_pts, -0.3, 0.3, mat_purple_glow)
create_wall_perimeter("Zone_DanceFloor_Walls", portal_pts, 0.0, 6.5, 0.4, mat_green_metal, open_edges={3})

# DJ booth - pulled inside the polygon so it clears the 0.2m wall inner face
dj_pts = [(12.5, -3.9), (16.5, -3.7), (13.0, -5.7)]
create_prism_from_2d("DJ_Stage_Platform", dj_pts, 0.0, 0.8, mat_green_metal)
create_prism_from_2d("DJ_Console_Desk", [(13.5, -4.3), (15.3, -4.1), (13.8, -5.3)], 0.8, 1.1, mat_neon_green)

# B. "LAIR" VIP ZONE (Elevated)
lair_pts = [
    (-16.0, -7.5),
    (-2.5, -6.5),
    (-2.0, -2.0),
    (-11.0, -1.5)
]
create_prism_from_2d("Zone_VIP_Lair_Floor", lair_pts, -0.3, 0.9, mat_dark_floor)
create_wall_perimeter("Zone_VIP_Outer_Walls", lair_pts, 0.0, 6.5, 0.4, mat_green_metal, open_edges={1, 2})

# Dance Floor -> VIP riser (4 steps, 0.6m rise)
create_stairs("Stairs_Dance_To_VIP", (-1.4, -4.2, 0.0), 180.0, 3.2, 0.6, 1.8, 4, mat_green_metal)

# Lobby -> VIP riser (3 steps, 0.6m rise) - fixes the 60cm ledge
create_stairs("Stairs_Lobby_To_VIP", (-6.0, -1.4, 0.0), 270.0, 2.4, 0.6, 1.0, 3, mat_green_metal)

# Wrap-around bar in the 'L' corner
bar_pts = [(-13.5, -6.2), (-6.5, -5.8), (-6.5, -4.8), (-12.5, -5.2)]
create_prism_from_2d("VIP_Bar_Counter", bar_pts, 0.6, 1.15, mat_green_metal)
create_prism_from_2d("VIP_Bar_Neon_Trim", bar_pts, 1.75, 0.08, mat_neon_green)

# C. "MATT'S" SPAWN LOBBY
spawn_pts = [
    (-14.0, 6.5),
    (-4.0, 6.5),
    (-4.0, -1.5),
    (-14.0, -1.5)
]
create_prism_from_2d("Zone_Spawn_Lobby_Floor", spawn_pts, -0.3, 0.3, mat_dark_floor)
create_wall_perimeter("Zone_Spawn_Walls", spawn_pts, 0.0, 6.5, 0.4, mat_green_metal, open_edges={2})

# Mezzanine catwalk - extended west to the lobby wall so it can actually be reached
mezz_pts = [
    (-14.0, 6.0),
    (11.0, 6.0),
    (11.0, 1.8),
    (-14.0, 1.8)
]
create_prism_from_2d("Zone_Mezzanine_Deck", mezz_pts, 2.9, 0.3, mat_green_metal)
# Back wall on the north edge only (east edge gets a rail instead)
create_wall_perimeter("Zone_Mezzanine_BackWall", mezz_pts, 3.2, 3.3, 0.4, mat_green_metal, open_edges={1, 2, 3})

# Railing split around the stair opening (stairs occupy x -10.3 .. -7.7)
create_rail("Rail_Mezz_South_W", (-14.0, 1.8), (-10.3, 1.8), 3.2, 1.1, 0.12, mat_neon_green)
create_rail("Rail_Mezz_South_E", (-7.7, 1.8), (11.0, 1.8), 3.2, 1.1, 0.12, mat_neon_green)
create_rail("Rail_Mezz_East", (11.0, 1.8), (11.0, 6.0), 3.2, 1.1, 0.12, mat_neon_green)

# Grand staircase: climbs north from the lobby and lands exactly on the deck edge at y=1.8
create_stairs("Stairs_Lobby_To_Mezzanine", (-9.0, -1.4, 0.0), 0.0, 2.6, 3.2, 3.2, 16, mat_green_metal)

# D. SKYLIGHT ROOF
roof_pts = [(-16.5, 7.0), (18.5, 7.0), (18.5, -12.0), (-16.5, -12.0)]
create_prism_from_2d("Club_Skylight_Ceiling", roof_pts, 6.5, 0.2, mat_glass)

# E. SCALE REFERENCE (moved clear of the staircase, tucked under the deck)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-12.0, 3.5, 0.875))
avatar_ref = bpy.context.active_object
avatar_ref.name = "VRC_Avatar_Scale_Ref_175cm"
avatar_ref.scale = (0.5, 0.35, 1.75)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
avatar_ref.data.materials.append(mat_neon_green)
link_obj(avatar_ref)

# -------------------------------------------------------------------------
# 5. LIGHTMAP UV + NORMALS (HEADLESS-SAFE)
# -------------------------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')

for obj in collection.objects:
    if obj.type == 'MESH' and obj.name != "VRC_Avatar_Scale_Ref_175cm":
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        while len(obj.data.uv_layers) < 2:
            obj.data.uv_layers.new()
        obj.data.uv_layers[0].name = "UVMap"
        obj.data.uv_layers[1].name = "LightmapUV"

        obj.data.uv_layers.active_index = 1
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.03)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.uv_layers.active_index = 0

bpy.ops.object.select_all(action='DESELECT')
for obj in collection.objects:
    if obj.type == 'MESH' and obj.name != "VRC_Avatar_Scale_Ref_175cm":
        obj.select_set(True)

# -------------------------------------------------------------------------
# 6. EXPORT
# -------------------------------------------------------------------------
def export_vrc_fbx(export_path=None):
    if export_path is None:
        export_path = os.path.join(os.path.expanduser("~"), "Matts_Lair_Club.fbx")
    bpy.ops.export_scene.fbx(
        filepath=export_path,
        use_selection=True,
        object_types={'MESH'},
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        bake_space_transform=True
    )
    print(f"[OK] Matts Lair Club built and exported to: {export_path}")
    return export_path

if __name__ == "__main__":
    export_vrc_fbx()