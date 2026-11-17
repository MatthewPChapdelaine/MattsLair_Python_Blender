# `build_azazel_architecture.py` — Technical Documentation

**Procedural Blender-to-Unity / VRChat Ashen Citadel Generator**

---

## 1. Design Intent

`build_azazel_architecture.py` creates a modular, vertical structure called the **Ashen Citadel**: one central tapered spire, five perimeter watchtowers, five radial causeways, and four links of a deliberately broken outer ring.

The design is an artistic foil to the companion Metatron frame:

| Metatron frame | Azazel frame |
| :--- | :--- |
| Planar, regular, and complete | Vertical, sparse, and intentionally open |
| 13 hubs joined as the complete graph $K_{13}$ | 6 towers joined by 9 selected causeways |
| Repeating geometric order | A broken perimeter and a clear point of entry |
| Pale metallic / neutral architectural language | Obsidian, ash, and restrained ember accents |

These are visual interpretations, not definitive religious descriptions. The Azazel design draws on motifs sometimes associated with wilderness, exile, and forbidden knowledge, while avoiding a literal or canonical religious depiction.

For basic definitions and the reasoning behind both architecture designs, see [character_context_mapping.md](./character_context_mapping.md).

For tower coordinates, graph topology, causeway lengths, and mesh counts, see [azazel_mathematical_design.md](./azazel_mathematical_design.md).

For the repository-wide generator and documentation flow, see [codebase_logic_design.md](./codebase_logic_design.md).

---

## 2. Requirements

* **Blender:** `3.6 LTS` or `4.0+`.
* **Unity:** `2022.3 LTS` for the documented VRChat workflow.
* The Blender FBX exporter must be available to export FBX.

The default model uses two shared meshes. After triangulation, its base geometry is approximately **276 triangles**: six 8-sided spires and nine 4-sided causeways. It is intentionally simple; lighting, materials, and scene composition provide most of its visual character.

---

## 3. Configuration

Edit these constants near the top of `build_azazel_architecture.py`:

| Parameter | Default | Description |
| :--- | :---: | :--- |
| `RING_RADIUS` | `20.0` | Radius of the five-watchtower layout, in meters. |
| `BRIDGE_ELEVATION` | `3.0` | Height of the causeway centerline above the ground. |
| `CORE_RADIUS` | `3.6` | Base radius of the central spire. |
| `CORE_HEIGHT` | `12.0` | Central spire height. |
| `WATCHTOWER_RADIUS` | `1.8` | Base radius of each perimeter tower. |
| `WATCHTOWER_HEIGHT` | `7.0` | Height of each perimeter tower. |
| `CAUSEWAY_WIDTH` | `1.4` | Causeway width in meters. |
| `SPIRE_SIDES` | `8` | Radial segments in the shared tapered spire mesh. |
| `CAUSEWAY_SIDES` | `4` | Cross-section sides of the shared causeway mesh. |
| `CLEAR_EXISTING` | `True` | Removes the prior `Azazel_Architecture` collection before rebuilding. |
| `AUTO_EXPORT_FBX` | `False` | Exports beside the saved `.blend` file when enabled. |
| `FBX_FILENAME` | `"Azazel_Ashen_Citadel.fbx"` | Automatic export filename. |

The builder rejects non-finite or non-positive dimensions before it changes the scene. `BRIDGE_ELEVATION` may be zero but cannot be negative. Automatic export requires a saved `.blend` file.

---

## 4. Layout and Causeways

The central citadel is at the origin. Five watchtowers sit on a radius-`RING_RADIUS` pentagonal layout at `18°`, `90°`, `162°`, `234°`, and `306°`. Towers rise from the ground; causeways connect them at `BRIDGE_ELEVATION`.

The 9 causeways are:

* **5 radial causeways:** the central citadel to each watchtower.
* **4 perimeter causeways:** Watchtower 01–02, 02–03, 03–04, and 04–05.
* **1 intentionally absent link:** Watchtower 05 to Watchtower 01.

That missing segment leaves a visible opening in the ring. It is intentional and is not an incomplete-generation error.

---

## 5. Scene Hierarchy

Running the script creates an `Azazel_Architecture` collection:

```text
Azazel_Architecture (Collection)
└── Azazel_Architecture_Root (Empty)
    ├── Towers_06_Spires (Empty)
    │   ├── Tower_00_Ashen_Citadel (Mesh_Azazel_Spire)
    │   └── Tower_01..05_Watcher_* (Mesh_Azazel_Spire)
    └── Causeways_09_Bridges (Empty)
        ├── 01_Radial_Ashen_Causeways (Empty, 5 causeways)
        └── 02_Broken_Ring_Causeways (Empty, 4 causeways)
```

All six towers instance `Mesh_Azazel_Spire`; all nine causeways instance `Mesh_Azazel_Causeway`. They use `Mat_Azazel_Obsidian` and `Mat_Azazel_Ember`, respectively.

---

## 6. Running and Exporting

### Blender GUI

1. Save a `.blend` file if you want to use automatic FBX export.
2. Open the **Scripting** workspace and load `build_azazel_architecture.py`.
3. Adjust the configuration constants if needed.
4. Run the script and inspect `Azazel_Architecture` in the Outliner.
5. To export automatically, set `AUTO_EXPORT_FBX = True` and rerun.

The generator adds its own collection and does not reset the rest of the scene. With `CLEAR_EXISTING = True`, reruns replace only its own collection.

### Headless FBX export

From the repository directory:

```bash
blender -b -P build_azazel_architecture.py --python-expr \
"import bpy; c=bpy.data.collections['Azazel_Architecture']; bpy.ops.object.select_all(action='DESELECT'); [o.select_set(True) for o in c.objects]; bpy.context.view_layer.objects.active=c.objects['Azazel_Architecture_Root']; bpy.ops.export_scene.fbx(filepath='./Azazel_Ashen_Citadel.fbx', use_selection=True, global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', object_types={'EMPTY', 'MESH'}, mesh_smooth_type='FACE')"
```

The selection in this command is limited to the architecture collection, so Blender's default cube and other unrelated scene objects are not included.

---

## 7. Unity and VRChat Setup

### Import

Import the FBX with scale factor `1` and axis conversion `-Z Forward, Y Up`. Leave automatic mesh-collider generation disabled. The two repeated meshes are candidates for GPU instancing when the Unity render pipeline, shaders, materials, visibility, and importer settings permit it; draw-call counts are not guaranteed.

### Primitive colliders

To keep collision geometry simple:

* **Six towers:** add a `BoxCollider` with local `Center (0, 0, 0.5)` and `Size (2, 2, 1)`. The mesh is tapered, so this collider covers its bounding envelope rather than matching every sloped face.
* **Nine causeways:** add a `BoxCollider` with local `Center (0, 0, 0)` and `Size (2, 2, 1)`. The object scale sets the causeway width and length.

The two causeway groups can be toggled independently for runtime variants. Keep the missing outer-ring link absent if preserving the intended open, fractured silhouette.

---

## 8. Functions

* `validate_configuration()` checks dimensions and exporter configuration.
* `cleanup_previous()` removes the generated collection and unused master meshes.
* `create_spire_mesh()` and `create_causeway_mesh()` create the shared unit meshes and UVs.
* `generate_azazel_towers()` calculates the central and perimeter tower positions.
* `build_azazel_architecture()` creates the hierarchy, instances the meshes, and optionally exports FBX.
