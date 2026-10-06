"""Render deterministic fixed-view evidence from the currently opened Blender file."""

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
    parser.add_argument("--scene-contract", required=True)
    parser.add_argument("--resolution", type=int, default=768)
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def point_camera(camera: bpy.types.Object, position: tuple[float, float, float], target: Vector) -> None:
    camera.location = position
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def camera_contract(contract: dict) -> tuple[Vector, dict[str, float], float]:
    dimensions = contract.get("dimensions", {})
    try:
        width = float(dimensions["width"])
        depth = float(dimensions["depth"])
        height = float(dimensions["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("scene contract requires positive width, depth, and height") from error
    if not all(math.isfinite(value) and value > 0 for value in (width, depth, height)):
        raise ValueError("scene contract dimensions must be finite positive numbers")
    origin_policy = contract.get("origin_policy")
    if origin_policy == "object-base-center":
        target = Vector((0.0, 0.0, height / 2.0))
    elif origin_policy == "world-origin":
        target = Vector((0.0, 0.0, 0.0))
    elif origin_policy == "declared-custom":
        framing_center = contract.get("framing_center")
        if not isinstance(framing_center, list) or len(framing_center) != 3:
            raise ValueError("declared-custom origin requires a three-number framing_center")
        try:
            target = Vector(tuple(float(value) for value in framing_center))
        except (TypeError, ValueError) as error:
            raise ValueError("framing_center must contain three finite numbers") from error
        if not all(math.isfinite(value) for value in target):
            raise ValueError("framing_center must contain three finite numbers")
    else:
        raise ValueError("unsupported origin_policy in scene contract")
    margin = 1.32
    scales = {
        "front": max(width, height) * margin,
        "back": max(width, height) * margin,
        "left": max(depth, height) * margin,
        "right": max(depth, height) * margin,
        "top": max(width, depth) * margin,
    }
    return target, scales, max(width, depth, height)


def build_contact_sheet(paths: list[Path], output: Path, thumb: int = 256) -> None:
    loaded = []
    try:
        for path in paths:
            image = bpy.data.images.load(str(path), check_existing=False)
            image.scale(thumb, thumb)
            loaded.append(image)
        width, height = thumb * 3, thumb * 2
        pixels = [0.0] * (width * height * 4)
        for index, image in enumerate(loaded):
            source = list(image.pixels[:])
            column, row = index % 3, 1 - index // 3
            for y in range(thumb):
                src_start = y * thumb * 4
                dst_start = ((row * thumb + y) * width + column * thumb) * 4
                pixels[dst_start : dst_start + thumb * 4] = source[src_start : src_start + thumb * 4]
        sheet = bpy.data.images.new("3D_Craft_Contact_Sheet", width=width, height=height, alpha=True)
        sheet.pixels[:] = pixels
        sheet.filepath_raw = str(output)
        sheet.file_format = "PNG"
        sheet.save()
        bpy.data.images.remove(sheet)
    finally:
        for image in loaded:
            bpy.data.images.remove(image)


def main() -> int:
    args = arguments()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    owned_outputs = [
        *(output_dir / f"{view}.png" for view in ("front", "back", "left", "right", "top", "perspective")),
        output_dir / "contact-sheet.png",
        output_dir / "lookdev-perspective.png",
        output_dir / "render-evidence.json",
    ]
    if any(path.exists() for path in owned_outputs):
        raise ValueError("render evidence already exists; create a new run for a new candidate")
    contract_path = Path(args.scene_contract).expanduser().resolve(strict=True)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "3d-craft.scene.v1":
        raise ValueError("--scene-contract must use schema 3d-craft.scene.v1")
    target, orthographic_scales, maximum_dimension = camera_contract(contract)
    blend_path = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    scene = bpy.context.scene
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.91, 0.90, 0.87)
    camera = bpy.data.objects.get("Camera_Evidence")
    if not camera:
        camera_data = bpy.data.cameras.new("Camera_Evidence")
        camera = bpy.data.objects.new("Camera_Evidence", camera_data)
        scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start = max(maximum_dimension / 1000.0, 0.0001)
    camera.data.clip_end = max(maximum_dimension * 50.0, 10.0)
    distance = maximum_dimension * 3.125
    positions = {
        "front": target + Vector((0.0, -distance, 0.0)),
        "back": target + Vector((0.0, distance, 0.0)),
        "left": target + Vector((-distance, 0.0, 0.0)),
        "right": target + Vector((distance, 0.0, 0.0)),
        "top": target + Vector((0.0, 0.0, distance)),
    }
    rendered: list[Path] = []
    metadata = []
    for name, position in positions.items():
        camera.data.ortho_scale = orthographic_scales[name]
        point_camera(camera, position, target)
        path = output_dir / f"{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(path)
        metadata.append({"view": name, "path": str(path), "sha256": sha256(path), "camera_location": [round(value, 6) for value in camera.location], "camera_rotation": [round(value, 6) for value in camera.rotation_euler], "camera_type": "ORTHO", "ortho_scale": camera.data.ortho_scale})
    camera.data.type = "PERSP"
    camera.data.lens = 70
    perspective_offset = Vector((1.5, -1.9375, 0.8125)) * maximum_dimension
    point_camera(camera, target + perspective_offset, target)
    perspective = output_dir / "perspective.png"
    scene.render.filepath = str(perspective)
    bpy.ops.render.render(write_still=True)
    rendered.append(perspective)
    metadata.append({"view": "perspective", "path": str(perspective), "sha256": sha256(perspective), "camera_location": [round(value, 6) for value in camera.location], "camera_rotation": [round(value, 6) for value in camera.rotation_euler], "camera_type": "PERSP", "lens": camera.data.lens})
    contact_sheet = output_dir / "contact-sheet.png"
    build_contact_sheet(rendered, contact_sheet)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_dir / "lookdev-perspective.png")
    bpy.ops.render.render(write_still=True)
    lookdev = output_dir / "lookdev-perspective.png"
    report = {
        "schema": "3d-craft.render-evidence.v1",
        "status": "PASS",
        "blender_version": bpy.app.version_string,
        "blend": {
            "path": str(blend_path) if blend_path else None,
            "sha256": sha256(blend_path) if blend_path and blend_path.is_file() else None,
        },
        "scene_contract": {"path": str(contract_path), "sha256": sha256(contract_path)},
        "framing": {
            "target": [round(value, 6) for value in target],
            "maximum_dimension": maximum_dimension,
            "margin": 1.32,
            "source": "scene-contract",
        },
        "renderers": {"structure": "BLENDER_WORKBENCH", "lookdev": "BLENDER_EEVEE"},
        "resolution": [args.resolution, args.resolution],
        "views": metadata,
        "contact_sheet": {"path": str(contact_sheet), "sha256": sha256(contact_sheet), "dimensions": [768, 512]},
        "lookdev": {"path": str(lookdev), "sha256": sha256(lookdev)},
    }
    report_path = output_dir / "render-evidence.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(report_path), "views": len(metadata)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
