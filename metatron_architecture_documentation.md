# `build_metatron_architecture.py` — Technical Documentation

**Procedural Blender-to-Unity / VRChat Architectural Frame Generator**

---

## 1. Overview

`build_metatron_architecture.py` is a Blender Python (`bpy`) script designed for VRChat world builders and technical artists. It procedurally generates a world-scale **Metatron's Cube** ($K_{13}$ complete graph) architectural frame consisting of **13 Node Hubs** and **78 Connecting Bridge Struts**.

The historical and creative context for the Metatron and Azazel designs is summarized in [character_context_mapping.md](./character_context_mapping.md). The complete graph is this generator's visual interpretation, not a claim that a historical text defines Metatron with this geometry.

For the coordinate equations, graph counts, and transform derivations, see [metatron_mathematical_design.md](./metatron_mathematical_design.md).

For the repository-wide generator and documentation flow, see [codebase_logic_design.md](./codebase_logic_design.md).

Rather than baking the complete frame into one mesh, this script builds an **instanced modular hierarchy** that keeps its components separately addressable for colliders, culling, and runtime toggles:
* **2 Shared Master Meshes:** `Mesh_Node_Hub` (unit icosphere) and `Mesh_Unit_Strut` (centered $1\text{ m}$ unit prism).
* **GPU Instancing Ready:** All 13 hubs reference the same hub mesh data block, and all 78 struts reference the same unit strut mesh data block. Unity may batch these into two instanced batches when the materials, shaders, visibility, and importer settings support it; two draw calls are not guaranteed in every scene or render pipeline.
* **Zero-Cost Primitive Colliders:** Because `Mesh_Unit_Strut` is normalized to a $1\text{ m}$ depth along its local $+Z$ axis and scaled via object transforms (`(STRUT_RADIUS, STRUT_RADIUS, chord_length)`), a standard Unity `BoxCollider` (`Size: 2, 2, 1`) matches the exact length, thickness, and orientation of every walkway without a single `MeshCollider`.
* **Deterministic UdonSharp Naming:** Every node and strut follows a zero-padded naming convention (`Node_00_Origin`, `Strut_00_to_07`) sorted into logical architectural sub-groups.

---

## 2. Requirements & Compatibility

* **Blender:** `3.6 LTS`, `4.0+` (uses standard `bpy`, `bmesh`, and `mathutils` modules).
* **Unity:** `2022.3 LTS` (VRChat Creator Companion standard).
* **Target Platforms:** PCVR and Meta Quest (Standalone Android) — base geometry is approximately $2,600$ triangles after triangulating the unit icosphere hubs and hexagonal strut prisms.

---

## 3. Configuration Parameters

At the top of `build_metatron_architecture.py`, modify the global constants to customize the scale and proportions of your world frame before running the script:

| Parameter | Default | Type | Description |
| :--- | :--- | :--- | :--- |
| `RING_RADIUS` | `18.0` | `float` | Radius $R$ (in meters) of the inner hexagonal ring (`Nodes 01–06`). The outer ring (`Nodes 07–12`) automatically scales to $2R$ (`36.0m`). |
| `VERTICAL_ELEVATION` | `0.0` | `float` | Vertical $Z$-axis offset (in Blender space) between concentric rings. At `0.0`, the lattice is flat planar; positive values create a 3D stepped amphitheater/tower. |
| `HUB_RADIUS` | `3.5` | `float` | Uniform scale radius (in meters) applied to each of the 13 Node Hub chambers. |
| `STRUT_RADIUS` | `0.45` | `float` | Cross-sectional thickness radius (in meters) applied to the $X$ and $Y$ axes of each connecting bridge strut. |
| `STRUT_SIDES` | `6` | `int` | Radial segments for the strut prism (`6` = hexagonal sci-fi girder, `4` = square beam, `8` = octagonal conduit). |
| `CLEAR_EXISTING` | `True` | `bool` | Automatically purges any previous `Metatron_Architecture` collection and orphan meshes before rebuilding. |
| `AUTO_EXPORT_FBX` | `False` | `bool` | When `True` (and the `.blend` file is saved on disk), automatically exports `FBX_FILENAME` into the same directory using Unity-ready axis settings. |
| `FBX_FILENAME` | `"Metatron_World_Frame.fbx"` | `str` | Target filename used when `AUTO_EXPORT_FBX` is enabled. |

---

## 4. Mathematical Coordinate System & Node Indexing

The script places 13 nodes using polar coordinates converted to Cartesian space. In Blender ($Z$-up), planar coordinates are generated on the $X\text{–}Y$ plane (which exports cleanly to Unity's $X\text{–}Z$ horizontal plane via `-Z Forward, Y Up`).

$$P_k = \begin{cases} (0, 0, 0) & \text{if } k = 0 \\ \left(R \cos\theta_k,\; R \sin\theta_k,\; Z_{\text{offset}}\right) & \text{if } 1 \le k \le 6 \\ \left(2R \cos\theta_k,\; 2R \sin\theta_k,\; 2Z_{\text{offset}}\right) & \text{if } 7 \le k \le 12 \end{cases}$$

where $\theta_k = (k - 1) \times 60^\circ$ for the inner ring and $(k - 7) \times 60^\circ$ for the outer ring.

### Node Lookup Table

| Index | Object Name | Ring Layer | Angle ($\theta$) | Radial Distance | Default Position $(R = 18\text{ m}, Z = 0)$ |
| :---: | :--- | :--- | :---: | :---: | :--- |
| `0` | `Node_00_Origin` | Origin | $0^\circ$ | $0$ | `(0.00, 0.00, 0.00)` |
| `1` | `Node_01_Inner_000deg` | Inner | $0^\circ$ | $R$ | `(18.00, 0.00, 0.00)` |
| `2` | `Node_02_Inner_060deg` | Inner | $60^\circ$ | $R$ | `(9.00, 15.59, 0.00)` |
| `3` | `Node_03_Inner_120deg` | Inner | $120^\circ$ | $R$ | `(-9.00, 15.59, 0.00)` |
| `4` | `Node_04_Inner_180deg` | Inner | $180^\circ$ | $R$ | `(-18.00, 0.00, 0.00)` |
| `5` | `Node_05_Inner_240deg` | Inner | $240^\circ$ | $R$ | `(-9.00, -15.59, 0.00)` |
| `6` | `Node_06_Inner_300deg` | Inner | $300^\circ$ | $R$ | `(9.00, -15.59, 0.00)` |
| `7` | `Node_07_Outer_000deg` | Outer | $0^\circ$ | $2R$ | `(36.00, 0.00, 0.00)` |
| `8` | `Node_08_Outer_060deg` | Outer | $60^\circ$ | $2R$ | `(18.00, 31.18, 0.00)` |
| `9` | `Node_09_Outer_120deg` | Outer | $120^\circ$ | $2R$ | `(-18.00, 31.18, 0.00)` |
| `10` | `Node_10_Outer_180deg` | Outer | $180^\circ$ | $2R$ | `(-36.00, 0.00, 0.00)` |
| `11` | `Node_11_Outer_240deg` | Outer | $240^\circ$ | $2R$ | `(-18.00, -31.18, 0.00)` |
| `12` | `Node_12_Outer_300deg` | Outer | $300^\circ$ | $2R$ | `(18.00, -31.18, 0.00)` |

---

## 5. Scene Hierarchy & Architectural Grouping

Running the script creates a dedicated collection named `Metatron_Architecture` with the following parent-child transform hierarchy:

```text
Metatron_Architecture (Collection)
└── Metatron_Architecture_Root (Empty - Origin 0,0,0)
    ├── Nodes_13_Hubs (Empty)
    │   ├── Node_00_Origin (Mesh: Mesh_Node_Hub)
    │   ├── Node_01_Inner_000deg (Mesh: Mesh_Node_Hub)
    │   ├── ...
    │   └── Node_12_Outer_300deg (Mesh: Mesh_Node_Hub)
    └── Struts_78_Vectors (Empty)
        ├── 01_Radial_Spokes (12 struts: Node 00 to all Inner & Outer nodes)
        │   ├── Strut_00_to_01
        │   └── ...
        ├── 02_Inner_Hexagon_And_Star (15 struts: all connections between Nodes 01..06)
        │   ├── Strut_01_to_02 (Hexagon perimeter edge)
        │   ├── Strut_01_to_03 (Inner Star Tetrahedron / Merkaba edge)
        │   └── ...
        ├── 03_Outer_Hexagon_And_Star (15 struts: all connections between Nodes 07..12)
        │   ├── Strut_07_to_08 (Outer Hexagon perimeter edge)
        │   ├── Strut_07_to_09 (Outer Star Tetrahedron / Merkaba edge)
        │   └── ...
        └── 04_Cross_Lattice_Chords (36 struts: all connections between Inner 01..06 and Outer 07..12)
            ├── Strut_01_to_07
            └── ...
```

### Why Struts Are Categorized Into 4 Sub-Groups
Having all 78 struts enabled simultaneously creates a dense lattice. Sorting them into four logical parent Empties allows you to toggle entire architectural rings in Unity with a single checkbox or `GameObject.SetActive(bool)` call in UdonSharp:
1. **`01_Radial_Spokes` (12 struts):** Primary axial bridges radiating from the central spawn hub.
2. **`02_Inner_Hexagon_And_Star` (15 struts):** Contains the inner regular hexagon perimeter, the inner 2D Star of David (3D Stellated Octahedron / Merkaba projection), and diameters.
3. **`03_Outer_Hexagon_And_Star` (15 struts):** Outer boundary perimeter and outer Merkaba star chords.
4. **`04_Cross_Lattice_Chords` (36 struts):** Secondary harmonic chords that form the embedded Cube, Octahedron, Icosahedron, and Dodecahedron silhouettes.

---

## 6. Execution Instructions

### Method A: Inside Blender GUI
1. Open Blender and switch to the **Scripting** workspace tab.
2. Click **New** (or **Open**) and load `build_metatron_architecture.py`.
3. Adjust any desired parameters at the top of the script.
4. Click **Run Script** ($\blacktriangleright$ button or `Alt + P`).
5. Inspect the generated hierarchy in the **Outliner** under `Metatron_Architecture`.

### Method B: Headless Command Line (CLI Automation)
You can generate the `.fbx` file directly from a terminal or CI/CD build script without opening the Blender UI:

```bash
blender -b -P build_metatron_architecture.py --python-expr \
"import bpy; c=bpy.data.collections['Metatron_Architecture']; bpy.ops.object.select_all(action='DESELECT'); [o.select_set(True) for o in c.objects]; bpy.context.view_layer.objects.active=c.objects['Metatron_Architecture_Root']; bpy.ops.export_scene.fbx(filepath='./Metatron_World_Frame.fbx', use_selection=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', object_types={'EMPTY', 'MESH'}, mesh_smooth_type='FACE')"
```

---

## 7. Unity & VRChat Integration Guide

### Step 1: FBX Import Settings
Select `Metatron_World_Frame.fbx` in your Unity Project window and configure the **Inspector**:
* **Model Tab:**
  * `Scale Factor`: `1`
  * `Convert Units`: Checked
  * `Bake Axis Conversion`: Unchecked (already handled by `-Z Forward / Y Up`)
  * `Generate Colliders`: **Unchecked** (never use auto-generated MeshColliders for 78 struts!)
  * `Generate Lightmap UVs`: Checked (if baking static lighting with Bakery or Progressive Lightmapper)
* **Materials Tab:**
  * Extract or remap `Mat_Metatron_Hub` and `Mat_Metatron_Strut`.
  * **Crucial:** Check **Enable GPU Instancing** at the bottom of both material inspectors.

### Step 2: Zero-Overhead Primitive Colliders
Because every object uses normalized unit geometry scaled via its Transform:
1. **For the 13 Node Hubs (`Node_00` to `Node_12`):**
   * Select all 13 hub GameObjects in the scene hierarchy.
   * Click **Add Component > Sphere Collider**.
   * Set `Center` to `(0, 0, 0)` and `Radius` to `1.0`. Because each Hub's Transform scale is `(HUB_RADIUS, HUB_RADIUS, HUB_RADIUS)`, Unity automatically scales the `SphereCollider` to the exact world radius (`3.5m`).
2. **For the 78 Bridge Struts (`Strut_00_to_01` to `Strut_11_to_12`):**
   * Select all 78 strut GameObjects.
   * Click **Add Component > Box Collider**.
   * Set `Center` to `(0, 0, 0)` and `Size` to `(2.0, 2.0, 1.0)`.
   * Why `(2, 2, 1)`? The unit strut mesh has a radius of `1.0` (diameter = `2.0`) on $X$ and $Y$, and a total depth of `1.0` (`-0.5` to `+0.5`) along local $Z$. Each strut's Transform scale `(STRUT_RADIUS, STRUT_RADIUS, length)` automatically stretches the `BoxCollider` to fit the exact chord length and orientation.

### Step 3: Isolating Specific Platonic Solids in UdonSharp
Because every strut is named `Strut_II_to_JJ` (where `II < JJ`), you can isolate specific Platonic solids or geometric subsets by enabling only their corresponding index pairs:

| Geometric Subset | Active Node Indices | Active Strut Pairs (`II_to_JJ`) |
| :--- | :--- | :--- |
| **Inner Hexagon Ring** | `1, 2, 3, 4, 5, 6` | `01_to_02`, `02_to_03`, `03_to_04`, `04_to_05`, `05_to_06`, `01_to_06` |
| **Inner Merkaba (Star Tetrahedron)** | `1, 2, 3, 4, 5, 6` | Upward Triangle: `01_to_03`, `03_to_05`, `01_to_05`<br>Downward Triangle: `02_to_04`, `04_to_06`, `02_to_06`<br>Internal Axes: `00_to_01` .. `00_to_06` |
| **Outer Merkaba (Star Tetrahedron)** | `7, 8, 9, 10, 11, 12` | Upward Triangle: `07_to_09`, `09_to_11`, `07_to_11`<br>Downward Triangle: `08_to_10`, `10_to_12`, `08_to_12` |
| **Isometric Cube (Hexahedron)** | `0, 7, 8, 9, 10, 11, 12` | Outer Hexagon (`07_to_08`, `08_to_09`, `09_to_10`, `10_to_11`, `11_to_12`, `07_to_12`) + 3 Alternating Radial Spokes (`00_to_07`, `00_to_09`, `00_to_11`) |
| **Isometric Octahedron** | `0, 7, 8, 9, 10, 11, 12` | Outer Hexagon perimeter + Outer Triangle (`07_to_09`, `09_to_11`, `07_to_11`) + Opposite Triangle (`08_to_10`, `10_to_12`, `08_to_12`) |

---

## 8. Internal Function Reference

* **`cleanup_previous()`**
  Unlinks and deletes the `Metatron_Architecture` collection and removes `Mesh_Node_Hub` and `Mesh_Unit_Strut` data blocks from `bpy.data.meshes` to prevent `.001` duplicate suffixes on re-runs.
* **`get_or_create_material(name, base_color, metallic, roughness, emission_strength)`**
  Idempotently creates a node-based Principled BSDF material so repeated executions do not bloat the `.blend` file with duplicate material slots.
* **`create_unit_hub_mesh(name)`**
  Constructs a 2-subdivision icosphere ($R = 1.0\text{ m}$, $80$ triangles) via `bmesh.ops.create_icosphere` and runs Smart UV Project (`66°` angle limit) for immediate lightmap and texture compatibility. The generated hub is spherical; it does not include a walkable floor.
* **`create_unit_strut_mesh(name, sides)`**
  Constructs a flat-shaded regular polygonal prism ($R = 1.0\text{ m}$, depth $= 1.0\text{ m}$) along the local $Z$-axis via `bmesh.ops.create_cone` and applies cubic UV projection.
* **`generate_metatron_coordinates(radius, z_offset)`**
  Calculates the 13 node dictionaries containing index, deterministic name, ring classification, and `mathutils.Vector` position.
* **`build_metatron_world_frame()`**
  Main orchestrator function. Sets scene units to Metric `1.0`, builds the Empty hierarchy, instances the 13 hubs and $\binom{13}{2} = 78$ struts using `direction.to_track_quat('Z', 'Y')`, converts rotations to clean `XYZ` Euler angles, and optionally triggers the FBX exporter.