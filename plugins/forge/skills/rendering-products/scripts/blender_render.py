"""Optional Blender marketing render -- runs INSIDE Blender's own bundled Python via
``bpy``, invoked as:

    <real Blender executable> -b --factory-startup -P blender_render.py -- \\
        --stl <path.stl> --out <path.png> [--width 1600 --height 1200]

**Important:** invoke the real executable path
(``/Applications/Blender.app/Contents/MacOS/Blender``), not the
``~/.forge/bin/blender`` symlink -- verified empirically: Blender resolves
its bundled ``scripts/`` and ``datafiles/`` (fonts etc.) relative to how it
was invoked, and running it through the forge-bin symlink produced
``couldn't find 'scripts/modules'`` and a hard crash before any Python ran.
Running the same script via the real path under
``/Applications/Blender.app/Contents/MacOS/Blender`` works. ``verify.py``
resolves the symlink before invoking Blender for exactly this reason.

This is optional (ADR-001 §8: Blender is opt-in). It is not covered by a
mandatory check the way the PyVista engineering pack is -- see SKILL.md.
"""
from __future__ import annotations

import sys


def _parse_args(argv: list[str]) -> dict:
    # Blender puts a "--" before script args; everything after it is ours.
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    out = {"width": 1600, "height": 1200}
    i = 0
    while i < len(argv):
        key = argv[i].lstrip("-")
        if key in ("stl", "out"):
            out[key] = argv[i + 1]
            i += 2
        elif key in ("width", "height"):
            out[key] = int(argv[i + 1])
            i += 2
        else:
            i += 1
    return out


def main() -> int:
    import bpy

    args = _parse_args(sys.argv)
    if "stl" not in args or "out" not in args:
        print("ERROR: --stl and --out are required", file=sys.stderr)
        return 2

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.stl_import(filepath=args["stl"])
    obj = bpy.context.selected_objects[0]

    mat = bpy.data.materials.new("forge_marketing")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.77, 0.82, 1.0)
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.15
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.35
    obj.data.materials.append(mat)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = args["width"]
    scene.render.resolution_y = args["height"]
    scene.render.film_transparent = True

    dims = obj.dimensions
    span = max(dims.x, dims.y, dims.z, 1.0)

    cam_data = bpy.data.cameras.new("cam")
    cam_obj = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (span * 1.8, -span * 1.8, span * 1.4)
    cam_obj.rotation_euler = (1.05, 0.0, 0.8)
    scene.camera = cam_obj

    # Sun lamps are directional -- only rotation_euler aims them, location is ignored.
    key = bpy.data.lights.new("key", type="SUN")
    key.energy = 3.0
    key_obj = bpy.data.objects.new("key", key)
    scene.collection.objects.link(key_obj)
    key_obj.rotation_euler = (0.9, 0.3, 0.9)  # angled to catch the top and two side faces

    fill = bpy.data.lights.new("fill", type="SUN")
    fill.energy = 1.2
    fill_obj = bpy.data.objects.new("fill", fill)
    scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (1.3, 0.0, -2.3)  # opposite side, softer, fills the shadowed faces

    scene.render.filepath = args["out"]
    bpy.ops.render.render(write_still=True)
    print(f"OK {args['out']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
