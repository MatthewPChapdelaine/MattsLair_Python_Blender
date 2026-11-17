# Codebase Logic Design

## 1. Purpose

This document organizes the repository by intent, execution order, and data flow. It is the navigation map for the project; use each generator's technical and mathematical documents for implementation details.

The repository has three independent Blender entry points:

1. `MattsLair.py` builds and exports the club environment.
2. `build_metatron_architecture.py` builds an instanced, complete-graph frame.
3. `build_azazel_architecture.py` builds an instanced, open-ring citadel.

The three scripts do not import or call one another. Each is independently executable and creates its own scene content and export workflow. The two architecture collections can coexist in one scene if both builders are run there; `MattsLair.py` resets the scene when it runs.

## 2. Logical Map

```text
Project intent and navigation
├── README.md
├── MattsLairDesign.md
└── character_context_mapping.md
    ├── Metatron interpretation ── metatron_mathematical_design.md
    │                            └── build_metatron_architecture.py
    └── Azazel interpretation ──── azazel_mathematical_design.md
                                 └── build_azazel_architecture.py

Club design
└── MattsLairDesign.md ── MattsLair.py ── Matts_Lair_Club.fbx

Architecture design
├── Metatron guide + math ── build_metatron_architecture.py
│                           └── Metatron_World_Frame.fbx
└── Azazel guide + math ──── build_azazel_architecture.py
                            └── Azazel_Ashen_Citadel.fbx

FBX assets ── Unity import ── materials, colliders, VRChat setup
```

The arrows show conceptual inputs and generated outputs, not Python imports. The documentation explains intent and use; the Python scripts are the executable implementations.

## 3. File Responsibilities and Reading Order

| Order | File | Responsibility |
| ---: | :--- | :--- |
| 0 | `codebase_logic_design.md` | This repository-wide map of execution order and data flow. |
| 1 | [README.md](./README.md) | Project entry point, generator choice, tutorials, and setup overview. |
| 2 | [MattsLairDesign.md](./MattsLairDesign.md) | Club narrative, zones, visual system, and experience goals. |
| 3 | [character_context_mapping.md](./character_context_mapping.md) | Basic Metatron/Azazel context and how those interpretations inform the architecture designs. |
| 4 | [metatron_mathematical_design.md](./metatron_mathematical_design.md) | Metatron coordinates, complete-graph edges, strut transforms, and counts. |
| 5 | [azazel_mathematical_design.md](./azazel_mathematical_design.md) | Azazel tower coordinates, sparse graph, causeway transforms, and counts. |
| 6 | [MattsLair.py](./MattsLair.py) | Executable club-scene generator and FBX export function. |
| 7 | [build_metatron_architecture.py](./build_metatron_architecture.py) | Executable Metatron collection generator. |
| 8 | [build_azazel_architecture.py](./build_azazel_architecture.py) | Executable Azazel collection generator. |
| 9 | [metatron_architecture_documentation.md](./metatron_architecture_documentation.md) | Metatron configuration, hierarchy, run instructions, and Unity guidance. |
| 10 | [azazel_architecture_documentation.md](./azazel_architecture_documentation.md) | Azazel configuration, hierarchy, run instructions, and Unity guidance. |

The numbered mathematical and technical guides are complementary: mathematical documents explain why the coordinates and counts have their values; technical documents explain how to run and import the result.

## 4. Choose the Generator

| Need | Entry point | Scene behavior | Primary output |
| :--- | :--- | :--- | :--- |
| Complete social club / broadcast lair | `MattsLair.py` | Resets Blender to an empty factory scene, then constructs the club. | `~/Matts_Lair_Club.fbx` by default. |
| Symmetric 13-node Metatron frame | `build_metatron_architecture.py` | Adds/replaces only the `Metatron_Architecture` collection. | FBX only when automatic export is enabled or manually invoked. |
| Vertical Azazel Ashen Citadel | `build_azazel_architecture.py` | Adds/replaces only the `Azazel_Architecture` collection. | FBX only when automatic export is enabled or manually invoked. |

**Important scene-safety distinction:** `MattsLair.py` calls `bpy.ops.wm.read_factory_settings(use_empty=True)` at the start. Run it in a separate Blender file if other scene content must be preserved. The two architecture scripts are additive; with `CLEAR_EXISTING = True`, each removes only its own prior collection and unused master meshes. They can coexist if run into the same scene, but neither builder invokes another, and neither automatically combines or exports the other generator's content.

## 5. Club Generator: `MattsLair.py`

`MattsLair.py` is an ordered scene-building script, not a reusable import-safe module. Scene reset, materials, geometry calls, UV preparation, and export setup execute at the top level when the script is run. `export_vrc_fbx()` is defined near the end and called under the `__main__` guard.

### Execution sequence

1. **Reset and initialize:** Start with an empty factory scene; set metric units to one Blender unit per meter; create `Matts_Lair_Club`.
2. **Prepare object linking:** `link_obj()` moves created objects into the club collection and sets the active object.
3. **Create materials:** Define dark floor, green metal, purple portal, neon, cyan signal, crimson, and glass materials.
4. **Define reusable geometry helpers:** Build polygon prisms and UVs with BMesh; create wall segments, perimeters, rails, stairs, signal rings, text signs, and the wave console.
5. **Construct zones in script order:**
   - portal/dance floor, signal rings, and transmitter core;
   - DJ stage, console, and broadcast monitor;
   - VIP/Lair floor, walls, signs, stairs, and bar;
   - spawn lobby, wave console, and welcome sign;
   - mezzanine deck, wall, railings, and staircase;
   - skylight ceiling and avatar scale reference.
6. **Prepare export meshes:** For eligible mesh objects, ensure `UVMap` and `LightmapUV` layers, unwrap the lightmap layer, recalculate normals, and restore the primary UV layer. The scale-reference mesh is excluded from this pass and from the final mesh selection.
7. **Export:** `export_vrc_fbx()` exports the selected meshes with Unity axis and scale settings. Its default destination is the user's home directory.

This script contains no separate `build_scene()` orchestrator: most build calls are top-level. Running it from Blender's Text Editor or as a script executes those calls. Importing the file in another Python module also executes the scene reset and build, so it should not be treated as a passive utility library.

## 6. Modular Architecture Generators

The Metatron and Azazel scripts use a common high-level pipeline but remain self-contained files. They share Blender concepts, not a Python helper package.

### Shared generation pipeline

1. Validate configured dimensions and mesh side counts.
2. If auto-export is requested, require a saved `.blend` file before changing the scene.
3. Switch to Object Mode for scene operations.
4. Optionally clean up the generator's previous collection.
5. Set metric units and create the named collection and Empty hierarchy.
6. Create one or two master mesh datablocks and their materials; UV unwrap the master meshes through an isolated temporary object.
7. Calculate architectural anchor points.
8. Instantiate repeated mesh objects by sharing those master datablocks.
9. Create connections by calculating endpoint delta, length, midpoint, and orientation; scale the unit mesh to the connection length.
10. Optionally select only the generated collection and export FBX.

### Metatron branch

`generate_metatron_coordinates()` creates one origin plus two six-point rings, at radii $R$ and $2R$. `build_metatron_world_frame()` creates 13 hub instances and one strut for every pair of nodes, producing $K_{13}$ with 78 struts. Four parent groups partition spokes, inner-ring edges, outer-ring edges, and cross-ring chords.

The output hierarchy is `Metatron_Architecture` → root → node/strut groups → four strut subgroups. The same hub mesh is used by all nodes; the same unit prism mesh is used by all struts.

### Azazel branch

`generate_azazel_towers()` creates the central citadel and five perimeter towers. `build_azazel_architecture()` creates six spire instances and nine causeways: five spokes plus four consecutive perimeter links. The fifth-to-first perimeter link is intentionally omitted, leaving the ring open.

The output hierarchy is `Azazel_Architecture` → root → towers and causeways → radial and broken-ring groups. All towers share one tapered spire mesh; all causeways share one prism mesh.

## 7. Data Flow to Unity

The architecture generators use Blender objects and Empty parenting for logical organization. They do not create Unity prefabs, runtime scripts, or colliders. Their FBX outputs are imported into Unity, where the corresponding architecture guide describes material handling, primitive colliders, and runtime group toggles.

```text
Configuration constants
        ↓
Coordinates / polygons
        ↓
Master mesh + material creation
        ↓
Instanced Blender objects and parent hierarchy
        ↓
UV preparation and FBX export
        ↓
Unity import and scene setup
```

The club generator differs in its mesh workflow: it creates a broad set of environment objects, prepares lightmap UVs and normals across those meshes, then exports the selected mesh objects. Its export and scene-reset semantics are specific to the club workflow.

## 8. Mathematical and Naming Contracts

* **Meters:** All generators set metric scene units with scale length `1.0`.
* **Stable object names:** Zero-padded node, strut, tower, and causeway names support Outliner navigation and downstream Unity lookup.
* **Shared mesh instances:** The architecture scripts share mesh datablocks instead of independently constructing every repeated form.
* **Connection transforms:** Each connection is centered at its endpoint midpoint, oriented along its endpoint vector, and stretched along local $+Z$.
* **Metatron count:** 13 nodes and $\binom{13}{2}=78$ struts; the group counts sum to 78.
* **Azazel count:** 6 towers and 9 causeways; the missing outer link is part of the design.
* **Interpretation boundary:** The character/context and mathematical documents describe artistic mappings. They do not claim the geometry is prescribed by historical or religious sources.

For derivations and numerical checks, consult [metatron_mathematical_design.md](./metatron_mathematical_design.md) and [azazel_mathematical_design.md](./azazel_mathematical_design.md).

## 9. Validation Boundaries

Python syntax and static checks can run outside Blender, but the generators depend on `bpy`, `bmesh`, `mathutils`, Blender operators, and Blender's FBX exporter. Actual scene construction, UV operator behavior, and FBX output must be validated in a compatible Blender installation and then checked in Unity. The repository currently has no standalone automated Blender test suite.
