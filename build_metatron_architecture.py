import bpy
import bmesh
import math
import os
from mathutils import Vector

# ==============================================================================
# CONFIGURATION PARAMETERS (World-Scale VRChat Dimensions in Meters)
# ==============================================================================
RING_RADIUS = 18.0          # Inner ring radius (Outer ring = 2 * RING_RADIUS = 36m)
VERTICAL_ELEVATION = 0.0    # Optional Z offset between rings (0.0 = flat planar)
HUB_RADIUS = 3.5            # Radius of the 13 node hub chambers
STRUT_RADIUS = 0.45         # Radius/thickness of the 78 connecting bridge struts
STRUT_SIDES = 6             # 6 = Hexagonal sci-fi girders (low-poly), 4 = Square beams
CLEAR_EXISTING = True       # Remove previous 'Metatron_Architecture' collection on run
AUTO_EXPORT_FBX = False     # Set True to auto-export FBX to the blend file directory
FBX_FILENAME = "Metatron_World_Frame.fbx"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def cleanup_previous():
    """Removes existing Metatron collection and orphan meshes from previous runs."""
    col_name = "Metatron_Architecture"
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

    for mesh_name in ["Mesh_Node_Hub", "Mesh_Unit_Strut"]:
        if mesh_name in bpy.data.meshes:
            mesh = bpy.data.meshes[mesh_name]
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)


def validate_configuration():
    """Reject invalid dimensions before modifying the current Blender scene."""
    for name, value in (
        ("RING_RADIUS", RING_RADIUS),
        ("HUB_RADIUS", HUB_RADIUS),
        ("STRUT_RADIUS", STRUT_RADIUS),
        ("VERTICAL_ELEVATION", VERTICAL_ELEVATION),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number.")

    for name, value in (
        ("RING_RADIUS", RING_RADIUS),
        ("HUB_RADIUS", HUB_RADIUS),
        ("STRUT_RADIUS", STRUT_RADIUS),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if isinstance(STRUT_SIDES, bool) or not isinstance(STRUT_SIDES, int) or STRUT_SIDES < 3:
        raise ValueError("STRUT_SIDES must be an integer of at least 3.")
    if not isinstance(FBX_FILENAME, str) or not FBX_FILENAME.strip():
        raise ValueError("FBX_FILENAME must be a non-empty filename.")


def get_or_create_material(name, base_color, metallic=0.8, roughness=0.25, emission_strength=0.0):
    """Creates a clean Principled BSDF material ready for Unity Standard/Lit conversion."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if "Emission Color" in bsdf.inputs and emission_strength > 0:
            bsdf.inputs["Emission Color"].default_value = base_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        elif "Emission" in bsdf.inputs and emission_strength > 0:
            bsdf.inputs["Emission"].default_value = base_color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def create_unit_hub_mesh(name="Mesh_Node_Hub"):
    """
    Creates a 1m-radius low-poly icosphere hub with clean UVs and a centered pivot.
    """
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    # Subdivided icosphere (subdivisions=2 gives 80 tris - ideal for Quest/PC VR)
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    bm.to_mesh(mesh)
    bm.free()

    _project_mesh_uv(mesh, "Temp_Hub", smart_project=True)

    return mesh


def _project_mesh_uv(mesh, temp_name, smart_project):
    """Run a UV operator on an isolated temporary object and restore selection."""
    previous_active = bpy.context.view_layer.objects.active
    previous_selected = list(bpy.context.selected_objects)
    previous_mode = previous_active.mode if previous_active else 'OBJECT'
    if previous_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    temp_obj = bpy.data.objects.new(temp_name, mesh)
    bpy.context.scene.collection.objects.link(temp_obj)
    try:
        bpy.ops.object.select_all(action='DESELECT')
        temp_obj.select_set(True)
        bpy.context.view_layer.objects.active = temp_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        if smart_project:
            bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
        else:
            bpy.ops.uv.cube_project(cube_size=1.0)
        bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(temp_obj, do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in previous_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if previous_active and previous_active.name in bpy.context.view_layer.objects:
            bpy.context.view_layer.objects.active = previous_active
        if previous_mode != 'OBJECT' and previous_active:
            bpy.ops.object.mode_set(mode=previous_mode)


def create_unit_strut_mesh(name="Mesh_Unit_Strut", sides=6):
    """
    Creates a unit-sized (1m length, 1m radius) prism oriented along the +Z axis
    with its origin centered at (0,0,0) and spanning Z from -0.5 to +0.5.
    Why centered? In Unity, a single BoxCollider at (0,0,0) with size (2, 2, 1)
    will automatically match the exact scaled length and rotation of every strut!
    """
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sides,
        radius1=1.0,
        radius2=1.0,
        depth=1.0
    )
    bm.to_mesh(mesh)
    bm.free()

    # Enable sharp edges for clean sci-fi architectural shading
    for poly in mesh.polygons:
        poly.use_smooth = False

    _project_mesh_uv(mesh, "Temp_Strut", smart_project=False)

    return mesh


def generate_metatron_coordinates(radius, z_offset=0.0):
    """
    Returns the 13 canonical 3D coordinates of the Fruit of Life / Metatron's Cube.
    Index 0: Origin
    Indices 1..6: Inner Hexagonal Ring (Radius = R)
    Indices 7..12: Outer Hexagonal Ring (Radius = 2R)
    """
    nodes = []
    # 0: Center Hub
    nodes.append({
        "index": 0,
        "name": "Node_00_Origin",
        "ring": "Origin",
        "pos": Vector((0.0, 0.0, 0.0))
    })

    # 1..6: Inner Ring
    for i in range(6):
        angle_deg = i * 60
        angle_rad = math.radians(angle_deg)
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        nodes.append({
            "index": i + 1,
            "name": f"Node_{i+1:02d}_Inner_{angle_deg:03d}deg",
            "ring": "Inner",
            "pos": Vector((x, y, z_offset))
        })

    # 7..12: Outer Ring
    for i in range(6):
        angle_deg = i * 60
        angle_rad = math.radians(angle_deg)
        x = (2.0 * radius) * math.cos(angle_rad)
        y = (2.0 * radius) * math.sin(angle_rad)
        nodes.append({
            "index": i + 7,
            "name": f"Node_{i+7:02d}_Outer_{angle_deg:03d}deg",
            "ring": "Outer",
            "pos": Vector((x, y, z_offset * 2.0))
        })

    return nodes


# ==============================================================================
# MAIN BUILD ROUTINE
# ==============================================================================
def build_metatron_world_frame():
    validate_configuration()
    if AUTO_EXPORT_FBX and not bpy.data.filepath:
        raise RuntimeError(
            "AUTO_EXPORT_FBX is enabled, but the Blender file has not been saved."
        )
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if CLEAR_EXISTING:
        cleanup_previous()

    # Ensure metric 1.0 unit scale for 1:1 Unity FBX parity
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0

    # Create Collection
    main_col = bpy.data.collections.new("Metatron_Architecture")
    bpy.context.scene.collection.children.link(main_col)

    # Create Hierarchy Empties
    root_empty = bpy.data.objects.new("Metatron_Architecture_Root", None)
    root_empty.empty_display_type = 'ARROWS'
    root_empty.empty_display_size = 5.0
    main_col.objects.link(root_empty)

    hubs_group = bpy.data.objects.new("Nodes_13_Hubs", None)
    hubs_group.parent = root_empty
    main_col.objects.link(hubs_group)

    struts_group = bpy.data.objects.new("Struts_78_Vectors", None)
    struts_group.parent = root_empty
    main_col.objects.link(struts_group)

    # Sub-groups for easy toggling of architectural density in Unity
    subgroups = {}
    for sg_name in ["01_Radial_Spokes", "02_Inner_Hexagon_And_Star", "03_Outer_Hexagon_And_Star", "04_Cross_Lattice_Chords"]:
        sg = bpy.data.objects.new(sg_name, None)
        sg.parent = struts_group
        main_col.objects.link(sg)
        subgroups[sg_name] = sg

    # Build Shared Instanced Meshes & Materials
    hub_mesh = create_unit_hub_mesh("Mesh_Node_Hub")
    strut_mesh = create_unit_strut_mesh("Mesh_Unit_Strut", sides=STRUT_SIDES)

    mat_hub = get_or_create_material("Mat_Metatron_Hub", (0.12, 0.14, 0.18, 1.0), metallic=0.85, roughness=0.2)
    mat_strut = get_or_create_material("Mat_Metatron_Strut", (0.85, 0.68, 0.25, 1.0), metallic=0.9, roughness=0.3)

    hub_mesh.materials.append(mat_hub)
    strut_mesh.materials.append(mat_strut)

    # Generate the 13 Node Coordinates
    nodes = generate_metatron_coordinates(RING_RADIUS, VERTICAL_ELEVATION)

    # 1. Instantiate the 13 Node Hubs
    for n in nodes:
        hub_obj = bpy.data.objects.new(n["name"], hub_mesh)
        hub_obj.location = n["pos"]
        hub_obj.scale = (HUB_RADIUS, HUB_RADIUS, HUB_RADIUS)
        hub_obj.parent = hubs_group
        main_col.objects.link(hub_obj)

    # 2. Instantiate the 78 Connecting Struts (K_13 Complete Graph)
    strut_count = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_a = nodes[i]
            node_b = nodes[j]
            pos_a = node_a["pos"]
            pos_b = node_b["pos"]

            delta = pos_b - pos_a
            length = delta.length
            midpoint = (pos_a + pos_b) * 0.5

            # Align local +Z axis along the vector from Node A to Node B
            direction = delta.normalized()
            rot_quat = direction.to_track_quat('Z', 'Y')

            strut_name = f"Strut_{i:02d}_to_{j:02d}"
            strut_obj = bpy.data.objects.new(strut_name, strut_mesh)
            strut_obj.location = midpoint
            strut_obj.rotation_euler = rot_quat.to_euler('XYZ')
            strut_obj.scale = (STRUT_RADIUS, STRUT_RADIUS, length)

            # Categorize into architectural sub-layers so you can toggle rings/stars in Unity
            if i == 0:
                strut_obj.parent = subgroups["01_Radial_Spokes"]
            elif i <= 6 and j <= 6:
                strut_obj.parent = subgroups["02_Inner_Hexagon_And_Star"]
            elif i >= 7 and j >= 7:
                strut_obj.parent = subgroups["03_Outer_Hexagon_And_Star"]
            else:
                strut_obj.parent = subgroups["04_Cross_Lattice_Chords"]

            main_col.objects.link(strut_obj)
            strut_count += 1

    print(f"[Metatron Builder] Created {len(nodes)} Hub Nodes and {strut_count} Strut Vectors.")

    # Optional automatic FBX Export configured for Unity
    if AUTO_EXPORT_FBX:
        export_path = os.path.join(os.path.dirname(bpy.data.filepath), FBX_FILENAME)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in main_col.objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = root_empty
        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z',
            axis_up='Y',
            object_types={'EMPTY', 'MESH'},
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            bake_space_transform=False
        )
        print(f"[Metatron Builder] Exported Unity FBX to: {export_path}")


if __name__ == "__main__":
    build_metatron_world_frame()