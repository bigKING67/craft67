"""Create the original 3D-Craft coffee-grinder fixture in Blender 5.2.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)


def make_material(name: str, color: tuple[float, float, float, float], metallic: float, roughness: float, transmission: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if "Transmission Weight" in shader.inputs:
        shader.inputs["Transmission Weight"].default_value = transmission
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = 0.18 if metallic else 0.06
    shader.inputs["Alpha"].default_value = color[3]
    if color[3] < 1.0:
        material.surface_render_method = "DITHERED"
        material.use_transparency_overlap = False
    return material


def finish_object(obj: bpy.types.Object, name: str, material: bpy.types.Material, root: bpy.types.Object, bevel: float = 0.0025) -> bpy.types.Object:
    obj.name = f"GRINDER_{name}"
    obj.data.name = f"MESH_{name}"
    obj.data.materials.append(material)
    obj["3d_craft_component"] = name.lower()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if bevel > 0:
        modifier = obj.modifiers.new("Edge_Soften", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.parent = root
    obj.select_set(False)
    return obj


def add_box(name: str, location, dimensions, material, root, bevel=0.0025, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.dimensions = dimensions
    return finish_object(obj, name, material, root, bevel)


def add_cylinder(name: str, location, radius, depth, material, root, rotation=(0, 0, 0), vertices=48, bevel=0.0015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    return finish_object(bpy.context.object, name, material, root, bevel)


def add_cone(name: str, location, radius1, radius2, depth, material, root, vertices=64, bevel=0.0015):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location)
    return finish_object(bpy.context.object, name, material, root, bevel)


def create_scene() -> None:
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 24
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.035, 0.035, 0.032)

    root = bpy.data.objects.new("GRINDER_Root", None)
    root["3d_craft_profile"] = "product-asset"
    root["3d_craft_units"] = "meters"
    scene.collection.objects.link(root)

    metal = make_material("brushed_metal", (0.23, 0.25, 0.24, 1.0), 0.82, 0.24)
    polymer = make_material("matte_polymer", (0.055, 0.06, 0.058, 1.0), 0.04, 0.46)
    glass = make_material("tinted_transparent", (0.34, 0.48, 0.43, 0.48), 0.0, 0.18)
    rubber = make_material("rubber", (0.018, 0.02, 0.019, 1.0), 0.0, 0.72)
    light_material = make_material("status_emissive", (0.95, 0.22, 0.055, 1.0), 0.0, 0.28)
    light_shader = light_material.node_tree.nodes.get("Principled BSDF")
    light_shader.inputs["Emission Color"].default_value = (1.0, 0.055, 0.01, 1.0)
    light_shader.inputs["Emission Strength"].default_value = 2.6

    add_box("Base", (0, 0, 0.014), (0.18, 0.21, 0.028), rubber, root, 0.004)
    add_box("Body", (0, 0.028, 0.112), (0.16, 0.145, 0.17), polymer, root, 0.012)
    add_box("Body_Metal_Face", (0, -0.046, 0.132), (0.135, 0.006, 0.108), metal, root, 0.004)
    add_cylinder("Grinding_Chamber", (0, 0.028, 0.205), 0.061, 0.032, metal, root, vertices=64, bevel=0.002)
    add_cone("Transparent_Hopper", (0, 0.028, 0.262), 0.061, 0.052, 0.108, glass, root, bevel=0.0012)
    add_cylinder("Lid", (0, 0.028, 0.315), 0.057, 0.01, polymer, root, vertices=64, bevel=0.0015)
    add_cylinder("Adjustment_Knob", (0.087, 0.026, 0.169), 0.025, 0.016, metal, root, rotation=(0, math.pi / 2, 0), vertices=48, bevel=0.001)
    add_cylinder("Adjustment_Knob_Inset", (0.096, 0.026, 0.169), 0.014, 0.003, polymer, root, rotation=(0, math.pi / 2, 0), vertices=48, bevel=0.0005)
    add_box("Chute", (0, -0.079, 0.158), (0.068, 0.072, 0.038), metal, root, 0.006, rotation=(math.radians(-8), 0, 0))
    add_box("Chute_Mouth", (0, -0.113, 0.15), (0.057, 0.012, 0.028), polymer, root, 0.004)
    add_cylinder("Grounds_Cup", (0, -0.067, 0.071), 0.038, 0.086, glass, root, vertices=64, bevel=0.002)
    add_cylinder("Grounds_Cup_Rim", (0, -0.067, 0.1145), 0.041, 0.005, metal, root, vertices=64, bevel=0.001)
    add_cylinder("Status_Light", (0.035, -0.0505, 0.104), 0.006, 0.004, light_material, root, rotation=(math.pi / 2, 0, 0), vertices=32, bevel=0.0005)

    camera_data = bpy.data.cameras.new("Camera_Product")
    camera = bpy.data.objects.new("Camera_Product", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0.47, -0.62, 0.42)
    camera.rotation_euler = (Vector((0, 0, 0.16)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 70
    scene.camera = camera

    for name, location, energy, size in (
        ("Key", (0.45, -0.35, 0.62), 38, 0.45),
        ("Fill", (-0.42, -0.12, 0.38), 16, 0.35),
        ("Rim", (0.28, 0.42, 0.52), 24, 0.3),
    ):
        data = bpy.data.lights.new(f"Light_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        lamp = bpy.data.objects.new(f"Light_{name}", data)
        scene.collection.objects.link(lamp)
        lamp.location = location
        lamp.rotation_euler = (Vector((0, 0, 0.15)) - lamp.location).to_track_quat("-Z", "Y").to_euler()


def main() -> int:
    args = arguments()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    create_scene()
    blend_path = output_dir / "asset.blend"
    glb_path = output_dir / "asset.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=True,
    )
    report = {
        "schema": "3d-craft.fixture-build.v1",
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "blend": {"path": str(blend_path), "sha256": sha256(blend_path), "bytes": blend_path.stat().st_size},
        "glb": {"path": str(glb_path), "sha256": sha256(glb_path), "bytes": glb_path.stat().st_size},
    }
    report_path = output_dir / "build.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(report_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
