# Matts Lair Python Blender

This project contains a Blender Python script that builds a stylized social club / nightlife venue called "Matt's Lair" and exports it as an FBX for downstream use in Unity and VRChat development.

The script is designed to be run directly inside Blender's scripting editor. It creates a complete environment from code, including floors, walls, stairs, mezzanine deck, neon accents, skylight roof, and a scale reference object.

## Project purpose

The goal of this script is to automate environment generation for a 3D club interior with:

- A dance floor / portal zone
- A VIP / "Lair" lounge area
- A spawn lobby
- A mezzanine / catwalk
- A glass skylight roof
- PBR materials and consistent UVs for export

The output is intended to be imported into game engines or further edited in 3D software.

## Files

- `MattsLair.py` — Blender script that generates the full 3D scene
- `README.md` — project documentation

## What the script does

When executed in Blender, the script performs the following actions:

1. Resets the Blender scene to factory defaults
2. Configures the scene to use metric units
3. Creates a dedicated collection named `Matts_Lair_Club`
4. Builds PBR materials for floors, metal, portal glow, neon trim, and glass
5. Creates architectural geometry with custom mesh helpers
6. Generates walls, stairs, platforms, rails, and floor polygons
7. Applies UVs and normal fixes for export readiness
8. Exports the selected mesh scene to an FBX file in the user's home directory

## Script structure

The script is divided into logical sections:

### 1. Scene setup

- Resets Blender to a clean state
- Sets the scene unit system to metric
- Sets a 1:1 metric scale
- Creates a new collection for the club environment

### 2. PBR materials

The script creates reusable materials:

- `Mat_Green_Metal` — green metal surface
- `Mat_Dark_Floor` — dark club floor material
- `Mat_Purple_Portal` — purple glow portal material with emission
- `Mat_Neon_Green` — bright neon green material with emission
- `Mat_Skylight_Glass` — translucent glass material

These materials are created with Blender node-based Principled BSDF settings and support both Blender 3.x and 4.x.

### 3. Mesh generation helpers

The script includes helper functions for:

- `generate_box_uv0()` — creates UVs suitable for box-like planar faces
- `create_prism_from_2d()` — converts a 2D polygon into a 3D prism with top/bottom faces and wall caps
- `_wall_segment()` — creates a wall segment between two points
- `create_wall_perimeter()` — creates connected wall segments around a polygon
- `create_rail()` — creates a light rail or barrier object
- `create_stairs()` — creates a 3D stair run with multiple steps

### 4. Architectural zones

The environment is composed of several distinct areas:

#### A. Purple portal triangle / dance floor

- Portal floor polygon
- Outer wall ring with an open edge for access
- DJ stage platform and console desk

#### B. VIP lounge / lair zone

- Elevated lounge floor
- Outer wall perimeter
- Bar counter and neon trim
- Stairs connecting the dance floor and lobby to the VIP area

#### C. Spawn lobby

- Lobby floor
- Surrounding walls
- Mezzanine catwalk around the lobby area
- Grand staircase to the mezzanine deck

#### D. Skylight roof

- Glass roofing slab covering the full club footprint

#### E. Scale reference

- A neon green avatar scale reference object
- Includes a 175 cm human-scale reference to help with proportion evaluation

### 5. UV and normal processing

Before export, the script:

- Ensures each mesh has at least two UV layers
- Names them `UVMap` and `LightmapUV`
- Enables smart UV projection for clean unwraps
- Makes normals consistent to prevent shading problems before export

### 6. Export

The script defines `export_vrc_fbx(export_path=None)`, which exports the selected meshes to an FBX using settings suitable for game export.

Default export location:

- `~/Matts_Lair_Club.fbx`

This means the file is written to the current user's home directory unless you pass in a custom path.

## How to run the script in Blender

1. Open Blender
2. Go to the `Scripting` workspace
3. Click `New` to create a new text block
4. Paste the contents of `MattsLair.py` into the editor
5. Press `Run Script`
6. Wait for the environment to generate
7. The script will export the scene to `~/Matts_Lair_Club.fbx`

## Export behavior

The script exports with these settings:

- `use_selection=True`
- `object_types={'MESH'}`
- `global_scale=1.0`
- `apply_unit_scale=True`
- `apply_scale_options='FBX_SCALE_ALL'`
- `axis_forward='-Z'`
- `axis_up='Y'`
- `use_mesh_modifiers=True`
- `mesh_smooth_type='FACE'`
- `bake_space_transform=True`

This helps preserve the intended world scale and orientation for Unity/VRChat workflows.

## Notes and assumptions

- The script assumes you are running Blender with Python scripting enabled.
- It uses Blender's built-in API and should work in Blender 3.x/4.x style environments.
- The script automatically creates the club collection and does not require a template file.
- It is intended as a procedural scene generator rather than a hand-authored mesh asset.
- The generated FBX is suitable for engine import and further optimization if needed.

## Suggested workflow

- Run the script in Blender
- Inspect the generated structural layout
- Adjust any polygon points or material values directly in the script if needed
- Re-export the FBX after edits
- Import the FBX into Unity or VRChat project tooling

## Licensing / use

This script is a procedural environment generator for personal / project-specific 3D development. Adapt and modify it as needed for your own Blender scenes and game projects.

## Quick summary

This project creates a complete club interior scene from code, including architecture, lighting-friendly UVs, material setup, and FBX export for game development. It is a compact procedural Blender environment generator intended to accelerate environment creation for a VRChat / Unity workflow.
