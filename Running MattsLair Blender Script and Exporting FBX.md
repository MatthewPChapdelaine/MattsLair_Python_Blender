---
title: Running MattsLair Blender Script and Exporting FBX
aliases:
  - Headless FBX Export
  - Blender FBX Deployment
tags:
  - blender
  - fbx
  - deployment
  - headless
  - vrchat
  - unity
  - gdevelop
---

# Running MattsLair Blender Script and Exporting FBX

> [!abstract] Purpose
> Build the club scene without a desktop session or GPU, export `Matts_Lair_Club.fbx`, and verify the result for Unity or VRChat.

**Related notes:** [[README]], [[MattsLairDesign]], [[codebase_logic_design]], [[MattsLair.py]], [[gdevelop5/README]]

> [!tip] Obsidian navigation
> Open [[MattsLair.canvas]] to move between project notes and generator files. Use backlinks on this note to find pages that reference the headless workflow.

**Overview**
You can run [this repository](https://github.com/MatthewPChapdelaine/MattsLair_Python_Blender) to generate the resulting FBX file. **A GPU is not required**. The script never renders frames or scenes via Cycles or EEVEE. Instead, it performs pure `bpy` mesh construction, material assignments, UV/normal cleanup, and one `export_scene.fbx` call.
The script concludes with the following block:

```py
if __name__ == "__main__":
    export_vrc_fbx()
```

Because of this, it self-executes cleanly under headless Blender commands (blender \-b \-P MattsLair.py) and writes directly to \~/Matts\_Lair\_Club.fbx without requiring GUI interaction.

## Export Checklist

- [ ] Blender 3.x or 4.x is available
- [ ] The repository contains `MattsLair.py`
- [ ] The generated scene uses a supported Blender version
- [ ] `Matts_Lair_Club.fbx` is present and non-empty
- [ ] The FBX is imported and checked in Unity or VRChat

## Option 1: Free Execution (GitHub Codespaces or Actions)

This approach requires no rental fees. GitHub Codespaces provides 60 free core-hours per month, and GitHub Actions is free for public repositories.

### Method A: GitHub Codespaces

```sh
sudo apt-get update && sudo apt-get install -y blender
mkdir -p ~/out
HOME=~/out blender -b -P MattsLair.py
# Output: ~/out/Matts_Lair_Club.fbx (Right-click in file tree to Download)
```

### Method B: GitHub Actions Workflow

Save the following content to .github/workflows/build.yml:

```yaml
name: build-fbx
on: [workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: sudo apt-get update && sudo apt-get install -y blender
      - run: HOME=$PWD blender -b -P MattsLair.py
      - uses: actions/upload-artifact@v4
        with:
          name: Matts_Lair_Club
          path: Matts_Lair_Club.fbx
```

The script uses `HOME` to choose its default export destination, so setting `HOME=$PWD` places `Matts_Lair_Club.fbx` in the repository workspace for the final upload step.

## Option 2: Cloud Instance Rental

If you prefer dedicated cloud compute resources:

* **Vast.ai**: Offers CPU-only instances for a few cents per hour (or GPU instances like RTX 3090/4090 for \~\$0.20–\$0.35/hr).
* **RunPod**: Provides CPU pods around \$0.10/hr (useful if you plan to render turntable previews later).
* **iRender / Spheron / Lambda**: High-end workstation providers; generally overkill for headless mesh exports.
* **Render Farm APIs (JANCTION, RenderStreet, SheepIt)**: Best if rendering previews alongside generation, as they directly accept Python script execution.

## Option 3: Docker Container Deployment (\$5/mo VPS or Local)

Create a Dockerfile:

```
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y blender libx11-6 libxi6 libxxf86vm1 \
    libxfixes3 libxrender1 libgl1 libsm6 libice6 git && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/MatthewPChapdelaine/MattsLair_Python_Blender /src
WORKDIR /src
CMD ["blender", "-b", "-P", "MattsLair.py"]
```

Build and run the container:

```sh
docker build -t mattslair .
docker run --rm -e HOME=/out -v "$PWD/out:/out" mattslair
```

`os.path.expanduser("~")` respects the `HOME` environment variable. Pointing `HOME` at a mounted volume ensures the exported FBX is stored directly on the host machine.

## Technical Considerations & Gotchas

* **Use OS Packages Over Tarballs**: Install Blender via apt-get to ensure all required X11 and OpenGL shared libraries are properly linked. Bare tarball extracts in minimal headless environments may fail on startup.
* **Blender Version Compatibility**: The script targets 3.x–4.x, but API changes between versions (e.g., uv.smart\_project angle parameters in radians, Principled BSDF socket name shifts in 4.0–4.2) may require pinning Blender to version 4.1 or 4.2 if material/UV errors occur.
* **Mesh Object Hierarchy**: The output FBX contains several hundred individual mesh objects (walls, rails, steps, signs). While suitable for VRChat scene organization, you may want to join or combine meshes in Unity for optimization.
* **FBX Addon Status**: If launching with \--factory-startup, io\_scene\_fbx remains enabled by default. Ensure bundled extensions are not disabled via custom preference files.
* **Text Sign Conversion**: Text elements (`THE LAIR`, `WELCOME TO THE LAIR`) are font curves. Because the exporter filters for mesh object types, unconverted font objects are omitted. If text signs are required in the FBX, convert them to mesh objects before export:

  ```python
  bpy.ops.object.select_all(action='DESELECT')
  for obj in bpy.context.scene.objects:
      if obj.type == 'FONT':
          obj.select_set(True)
  bpy.ops.object.convert(target='MESH')
  ```

## Verification

After export, verify the expected file exists and can be read:

```sh
test -s "$PWD/Matts_Lair_Club.fbx"
file "$PWD/Matts_Lair_Club.fbx"
ls -lh "$PWD/Matts_Lair_Club.fbx"
```

Then import the FBX into a clean Unity project or a VRChat SDK test scene and verify scale, mesh hierarchy, materials, UV layers, and collision behavior. The successful creation of a file does not by itself verify that every sign, material, or engine import setting is correct.

## GDevelop 5 Web and Desktop Workflow

GDevelop 5 3D objects support embedded-binary GLB models. FBX is useful for Unity and VRChat, but it is not the native web format for GDevelop. Export both formats when the club is intended for multiple engines.

> [!warning] Native format
> GDevelop expects a `.glb` model resource. It does not accept a `.gltf` file with external texture or binary dependencies reliably for packaged projects.

### Export GLB from Blender

After the existing FBX export, export the club scene to GLB:

```sh
blender -b -P MattsLair.py --python-expr \
"import bpy; bpy.ops.object.select_all(action='DESELECT'); [o.select_set(True) for o in bpy.data.collections['Matts_Lair_Club'].objects if o.type=='MESH' and o.name!='VRC_Avatar_Scale_Ref_175cm']; bpy.ops.export_scene.gltf(filepath='./Matts_Lair_Club.glb', export_format='GLB', use_selection=True, export_apply=True, export_yup=True)"
```

The script also provides:

```python
export_gdevelop_glb("/path/to/gdevelop5/assets/Matts_Lair_Club.glb")
```

Before importing, keep these constraints in mind:

- use meters consistently;
- export an embedded GLB with all textures included;
- remove or hide editor-only objects;
- use shared, simplified materials where possible;
- split an oversized club model into zones if browser loading or frame rate becomes a problem.

### Starter GDevelop project

Open [`gdevelop5/MattsLairGDevelop.json`](./gdevelop5/MattsLairGDevelop.json) in GDevelop 5:

1. Export `Matts_Lair_Club.glb` into `gdevelop5/assets/`.
2. Open the project resource manager and confirm the file is registered as a 3D model.
3. Select the `MattsLairClub` 3D model object.
4. Set its origin to the model origin or bottom center, depending on camera behavior.
5. Add a directional light and ambient light effect to the 3D layer.
6. Preview the project at several viewport sizes.

### Movement and camera events

Create these scene variables:

| Variable | Type | Example |
| :--- | :--- | :--- |
| `MoveSpeed` | number | `6` |
| `LookSensitivity` | number | `0.002` |

Typical event setup:

- At the beginning of the scene, position the club at `(0, 0, 0)` and place the camera near avatar eye height.
- When `W` or the up arrow is held, move forward.
- When `S` or the down arrow is held, move backward.
- When `A` or left arrow is held, strafe left.
- When `D` or right arrow is held, strafe right.
- When no movement key is held, stop the movement inputs and idle an optional animation.
- On mouse movement, rotate the camera horizontally and vertically within a safe pitch range.
- Use pointer lock for desktop play and restore normal pointer behavior on escape.

> [!tip] VRChat to GDevelop
> VRChat world scale and social SDK components do not transfer automatically. Convert the environment to GLB, replace VRChat pickups and triggers with GDevelop variables and events, and implement collision, portals, avatars, voice, and multiplayer again in GDevelop.