import bpy
import bmesh
import math
import os
from mathutils import Vector

# ==============================================================================
# CONFIGURATION
# ==============================================================================
RING_RADIUS = 20.0
BRIDGE_ELEVATION = 3.0
CORE_RADIUS = 3.6
CORE_HEIGHT = 12.0
WATCHTOWER_RADIUS = 1.8
WATCHTOWER_HEIGHT = 7.0
CAUSEWAY_WIDTH = 1.4
SPIRE_SIDES = 8
CAUSEWAY_SIDES = 4
CLEAR_EXISTING = True
AUTO_EXPORT_FBX = False
FBX_FILENAME = "Azazel_Ashen_Citadel.fbx"

WATCHTOWER_NAMES = (
    "Watcher_018deg",
    "Watcher_090deg",
    "Watcher_162deg",
    "Watcher_234deg",
    "Watcher_306deg",
)


def validate_configuration():
    """Validate dimensions before modifying the current Blender scene."""
    for name, value in (
        ("RING_RADIUS", RING_RADIUS),
        ("BRIDGE_ELEVATION", BRIDGE_ELEVATION),
        ("CORE_RADIUS", CORE_RADIUS),
        ("CORE_HEIGHT", CORE_HEIGHT),
        ("WATCHTOWER_RADIUS", WATCHTOWER_RADIUS),
        ("WATCHTOWER_HEIGHT", WATCHTOWER_HEIGHT),
        ("CAUSEWAY_WIDTH", CAUSEWAY_WIDTH),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number.")

    for name, value in (
        ("RING_RADIUS", RING_RADIUS),
        ("CORE_RADIUS", CORE_RADIUS),
        ("CORE_HEIGHT", CORE_HEIGHT),
        ("WATCHTOWER_RADIUS", WATCHTOWER_RADIUS),
        ("WATCHTOWER_HEIGHT", WATCHTOWER_HEIGHT),
        ("CAUSEWAY_WIDTH", CAUSEWAY_WIDTH),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")
    if BRIDGE_ELEVATION < 0:
        raise ValueError("BRIDGE_ELEVATION cannot be negative.")

    for name, value in (("SPIRE_SIDES", SPIRE_SIDES), ("CAUSEWAY_SIDES", CAUSEWAY_SIDES)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 3:
            raise ValueError(f"{name} must be an integer of at least 3.")
    if not isinstance(FBX_FILENAME, str) or not FBX_FILENAME.strip():
        raise ValueError("FBX_FILENAME must be a non-empty filename.")


def cleanup_previous():
    """Remove this generator's previous collection and its unused meshes."""
    collection_name = "Azazel_Architecture"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)

    for mesh_name in ("Mesh_Azazel_Spire", "Mesh_Azazel_Causeway"):
        mesh = bpy.data.meshes.get(mesh_name)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def get_or_create_material(name, base_color, metallic, roughness, emission_strength=0.0):
    """Create or reuse a Principled material compatible with Blender 3.6 and 4.x."""
    material = bpy.data.materials.get(name)
    if material:
        return material

    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = base_color
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Roughness"].default_value = roughness
        if emission_strength > 0:
            emission_color = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
            if emission_color:
                emission_color.default_value = base_color
            emission = shader.inputs.get("Emission Strength")
            if emission:
                emission.default_value = emission_strength
    return material


def _project_mesh_uv(mesh, temp_name, smart_project):
    """UV unwrap a temporary, isolated object and restore the previous selection."""
    previous_active = bpy.context.view_layer.objects.active
    previous_selected = list(bpy.context.selected_objects)
    previous_mode = previous_active.mode if previous_active else "OBJECT"
    if previous_mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    temp_obj = bpy.data.objects.new(temp_name, mesh)
    bpy.context.scene.collection.objects.link(temp_obj)
    try:
        bpy.ops.object.select_all(action="DESELECT")
        temp_obj.select_set(True)
        bpy.context.view_layer.objects.active = temp_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        if smart_project:
            bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
        else:
            bpy.ops.uv.cube_project(cube_size=1.0)
        bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.data.objects.remove(temp_obj, do_unlink=True)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in previous_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if previous_active and previous_active.name in bpy.context.view_layer.objects:
            bpy.context.view_layer.objects.active = previous_active
        if previous_mode != "OBJECT" and previous_active:
            bpy.ops.object.mode_set(mode=previous_mode)


def create_spire_mesh(name="Mesh_Azazel_Spire", sides=8):
    """Build a tapered, unit-height spire with its base at local Z=0."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sides,
        radius1=1.0,
        radius2=0.58,
        depth=1.0,
    )
    for vert in bm.verts:
        vert.co.z += 0.5
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    _project_mesh_uv(mesh, "Temp_Azazel_Spire", smart_project=True)
    return mesh


def create_causeway_mesh(name="Mesh_Azazel_Causeway", sides=4):
    """Build a centered, one-meter-long polygonal causeway along local Z."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sides,
        radius1=1.0,
        radius2=1.0,
        depth=1.0,
    )
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    _project_mesh_uv(mesh, "Temp_Azazel_Causeway", smart_project=False)
    return mesh


def generate_azazel_towers(radius, bridge_elevation):
    """Return one central citadel and five evenly spaced perimeter towers."""
    towers = [{
        "index": 0,
        "name": "Tower_00_Ashen_Citadel",
        "position": Vector((0.0, 0.0, 0.0)),
        "bridge_position": Vector((0.0, 0.0, bridge_elevation)),
        "role": "Core",
    }]
    for index in range(5):
        angle_degrees = 18 + index * 72
        angle = math.radians(angle_degrees)
        position = Vector((
            radius * math.cos(angle),
            radius * math.sin(angle),
            0.0,
        ))
        towers.append({
            "index": index + 1,
            "name": f"Tower_{index + 1:02d}_{WATCHTOWER_NAMES[index]}",
            "position": position,
            "bridge_position": Vector((position.x, position.y, bridge_elevation)),
            "role": "Watcher",
        })
    return towers


def _create_parent(name, parent, collection):
    obj = bpy.data.objects.new(name, None)
    obj.parent = parent
    collection.objects.link(obj)
    return obj


def build_azazel_architecture():
    validate_configuration()
    if AUTO_EXPORT_FBX and not bpy.data.filepath:
        raise RuntimeError("AUTO_EXPORT_FBX is enabled, but the Blender file has not been saved.")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    if CLEAR_EXISTING:
        cleanup_previous()

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    main_collection = bpy.data.collections.new("Azazel_Architecture")
    scene.collection.children.link(main_collection)

    root = bpy.data.objects.new("Azazel_Architecture_Root", None)
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 5.0
    main_collection.objects.link(root)

    towers_group = _create_parent("Towers_06_Spires", root, main_collection)
    causeways_group = _create_parent("Causeways_09_Bridges", root, main_collection)
    radial_group = _create_parent("01_Radial_Ashen_Causeways", causeways_group, main_collection)
    broken_ring_group = _create_parent("02_Broken_Ring_Causeways", causeways_group, main_collection)

    spire_mesh = create_spire_mesh(sides=SPIRE_SIDES)
    causeway_mesh = create_causeway_mesh(sides=CAUSEWAY_SIDES)
    spire_material = get_or_create_material(
        "Mat_Azazel_Obsidian",
        (0.055, 0.035, 0.045, 1.0),
        metallic=0.72,
        roughness=0.32,
    )
    causeway_material = get_or_create_material(
        "Mat_Azazel_Ember",
        (0.34, 0.075, 0.035, 1.0),
        metallic=0.55,
        roughness=0.28,
        emission_strength=0.25,
    )
    spire_mesh.materials.append(spire_material)
    causeway_mesh.materials.append(causeway_material)

    towers = generate_azazel_towers(RING_RADIUS, BRIDGE_ELEVATION)
    tower_objects = []
    for tower in towers:
        obj = bpy.data.objects.new(tower["name"], spire_mesh)
        obj.location = tower["position"]
        if tower["role"] == "Core":
            obj.scale = (CORE_RADIUS, CORE_RADIUS, CORE_HEIGHT)
        else:
            obj.scale = (WATCHTOWER_RADIUS, WATCHTOWER_RADIUS, WATCHTOWER_HEIGHT)
        obj.parent = towers_group
        main_collection.objects.link(obj)
        tower_objects.append(obj)

    connections = [(0, index) for index in range(1, 6)]
    connections.extend((index, index + 1) for index in range(1, 5))
    for start_index, end_index in connections:
        start = towers[start_index]["bridge_position"]
        end = towers[end_index]["bridge_position"]
        delta = end - start
        obj = bpy.data.objects.new(
            f"Causeway_{start_index:02d}_to_{end_index:02d}",
            causeway_mesh,
        )
        obj.location = (start + end) * 0.5
        obj.rotation_euler = delta.normalized().to_track_quat("Z", "Y").to_euler("XYZ")
        obj.scale = (CAUSEWAY_WIDTH * 0.5, CAUSEWAY_WIDTH * 0.5, delta.length)
        obj.parent = radial_group if start_index == 0 else broken_ring_group
        main_collection.objects.link(obj)

    print(
        f"[Azazel Builder] Created {len(tower_objects)} spires "
        f"and {len(connections)} causeways; the outer ring remains open."
    )

    if AUTO_EXPORT_FBX:
        export_path = os.path.join(os.path.dirname(bpy.data.filepath), FBX_FILENAME)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in main_collection.objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = root
        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Z",
            axis_up="Y",
            object_types={"EMPTY", "MESH"},
            use_mesh_modifiers=True,
            mesh_smooth_type="FACE",
            bake_space_transform=False,
        )
        print(f"[Azazel Builder] Exported Unity FBX to: {export_path}")


if __name__ == "__main__":
    build_azazel_architecture()
