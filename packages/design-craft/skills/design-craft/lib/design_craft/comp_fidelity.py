"""Bounded, dependency-free screenshot measurements for comp-fidelity review."""

from __future__ import annotations

import binascii
import hashlib
import json
import math
import os
import re
import stat
import struct
import tempfile
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SPEC_SCHEMA = "design-craft.comp-fidelity-spec.v1"
REPORT_SCHEMA = "design-craft.comp-fidelity-report.v1"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 4_000_000
MAX_DIMENSION = 16_384
MAX_SPEC_WIDTH = MAX_DIMENSION // 2
MAX_REGION_PIXELS = MAX_PIXELS
MAX_ARTIFACT_PIXELS = MAX_PIXELS * 6
MAX_SINGLE_ARTIFACT_PIXELS = MAX_PIXELS * 2
MAX_PNG_CHUNKS = 4096
DIMENSIONS = {"geometry", "type", "material", "ground", "controls", "content"}
SALIENCE = {"primary", "secondary", "supporting"}
METRIC_NAMES = {"mean_delta", "changed_pixel_ratio", "rmse"}
METRIC_FIELDS = {
    "mean_delta",
    "rmse",
    "max_delta_threshold",
    "changed_pixel_ratio",
    "reference_luminance",
    "rendered_luminance",
    "signed_luminance_shift",
    "reference_edge_energy",
    "rendered_edge_energy",
    "edge_energy_delta",
}


class CompFidelityError(RuntimeError):
    """Expected spec, image, output, or evidence validation failure."""


@dataclass(frozen=True)
class PngImage:
    width: int
    height: int
    rgba: bytes


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    data: bytes
    size: int
    sha256: str


def _identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _snapshot_file(path_value: Path, *, label: str, max_bytes: int = MAX_FILE_BYTES) -> FileSnapshot:
    """Read one immutable, bounded snapshot and bind its size and hash to those bytes."""

    path = path_value.expanduser().absolute()
    if path.is_symlink():
        raise CompFidelityError(f"{label} must be a non-symlink file")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CompFidelityError(f"{label} must be an existing non-symlink file: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise CompFidelityError(f"{label} must be a regular file")
        if before.st_size > max_bytes:
            raise CompFidelityError(f"{label} exceeds {max_bytes} bytes")
        data = bytearray()
        digest = hashlib.sha256()
        while len(data) <= max_bytes:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            digest.update(chunk)
        if len(data) > max_bytes:
            raise CompFidelityError(f"{label} exceeds {max_bytes} bytes")
        after = os.fstat(descriptor)
        if _identity(before) != _identity(after) or after.st_size != len(data):
            raise CompFidelityError(f"{label} changed while it was read")
    finally:
        os.close(descriptor)
    return FileSnapshot(path=path, data=bytes(data), size=len(data), sha256=digest.hexdigest())


def _paeth(a: int, b: int, c: int) -> int:
    estimate = a + b - c
    pa = abs(estimate - a)
    pb = abs(estimate - b)
    pc = abs(estimate - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _decode_png(data: bytes, *, label: str = "PNG", max_pixels: int = MAX_PIXELS) -> PngImage:
    if not data.startswith(PNG_SIGNATURE):
        raise CompFidelityError(f"{label} signature is invalid")
    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    palette = b""
    transparency = b""
    compressed = bytearray()
    saw_end = False
    saw_idat = False
    idat_closed = False
    saw_palette = False
    saw_transparency = False
    chunk_count = 0
    while offset < len(data):
        chunk_count += 1
        if chunk_count > MAX_PNG_CHUNKS:
            raise CompFidelityError(f"{label} has too many chunks")
        if offset + 12 > len(data):
            raise CompFidelityError(f"{label} chunk header is truncated")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        if not re.fullmatch(rb"[A-Za-z]{4}", chunk_type):
            raise CompFidelityError(f"{label} chunk type is invalid")
        end = offset + 12 + length
        if end > len(data):
            raise CompFidelityError(f"{label} chunk is truncated")
        chunk = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = binascii.crc32(chunk_type + chunk) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise CompFidelityError(f"{label} {chunk_type.decode('ascii', 'replace')} CRC mismatch")
        if chunk_type == b"IHDR":
            if chunk_count != 1 or length != 13 or width is not None:
                raise CompFidelityError(f"{label} IHDR must be the first and only header")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if not width or not height or width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise CompFidelityError(f"{label} dimensions are outside the supported bound")
            if width * height > max_pixels:
                raise CompFidelityError(f"{label} pixel count exceeds the supported bound")
            if bit_depth != 8 or color_type not in {0, 2, 3, 4, 6}:
                raise CompFidelityError(f"{label} must be 8-bit grayscale, RGB, palette, GA, or RGBA")
            if compression != 0 or filtering != 0 or interlace != 0:
                raise CompFidelityError(f"{label} compression, filtering, or interlace mode is unsupported")
        elif chunk_type == b"PLTE":
            if width is None or saw_palette or saw_idat or color_type in {0, 4}:
                raise CompFidelityError(f"{label} PLTE order or color type is invalid")
            if not 3 <= length <= 768 or length % 3:
                raise CompFidelityError(f"{label} PLTE length is invalid")
            palette = chunk
            saw_palette = True
        elif chunk_type == b"tRNS":
            if width is None or saw_transparency or saw_idat or color_type not in {0, 2, 3}:
                raise CompFidelityError(f"{label} tRNS order or color type is invalid")
            if color_type == 0 and length != 2 or color_type == 2 and length != 6:
                raise CompFidelityError(f"{label} tRNS length is invalid")
            if color_type == 3 and (not saw_palette or length > len(palette) // 3):
                raise CompFidelityError(f"{label} palette transparency is invalid")
            transparency = chunk
            saw_transparency = True
        elif chunk_type == b"IDAT":
            if width is None or idat_closed:
                raise CompFidelityError(f"{label} IDAT order is invalid")
            if color_type == 3 and not saw_palette:
                raise CompFidelityError(f"{label} indexed color requires PLTE before IDAT")
            saw_idat = True
            compressed.extend(chunk)
            if len(compressed) > MAX_FILE_BYTES:
                raise CompFidelityError(f"{label} compressed payload exceeds the supported bound")
        elif chunk_type == b"IEND":
            if width is None or not saw_idat or length != 0 or end != len(data):
                raise CompFidelityError(f"{label} IEND must be empty, final, and follow IDAT")
            saw_end = True
            offset = end
            break
        elif chunk_type[0] & 0x20 == 0:
            raise CompFidelityError(
                f"{label} contains unsupported critical chunk {chunk_type.decode('ascii')}"
            )
        elif saw_idat:
            idat_closed = True
        offset = end
    if width is None or height is None or not compressed or not saw_end:
        raise CompFidelityError(f"{label} is missing IHDR, IDAT, or IEND")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[int(color_type)]
    stride = int(width) * channels
    expected = (stride + 1) * int(height)
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(bytes(compressed), expected + 1)
    except zlib.error as exc:
        raise CompFidelityError(f"{label} decompression failed: {exc}") from exc
    if len(raw) != expected or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
        raise CompFidelityError(f"{label} decompressed payload has an unexpected size")

    rows: list[bytearray] = []
    cursor = 0
    previous = bytearray(stride)
    for _ in range(int(height)):
        filter_type = raw[cursor]
        encoded = raw[cursor + 1 : cursor + 1 + stride]
        cursor += stride + 1
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                predictor = _paeth(left, above, upper_left)
            else:
                raise CompFidelityError(f"{label} filter type {filter_type} is unsupported")
            row[index] = (value + predictor) & 0xFF
        rows.append(row)
        previous = row

    rgba = bytearray(int(width) * int(height) * 4)
    output = 0
    for row in rows:
        for x in range(int(width)):
            index = x * channels
            if color_type == 0:
                red = green = blue = row[index]
                alpha = 255
            elif color_type == 2:
                red, green, blue = row[index : index + 3]
                alpha = 255
            elif color_type == 3:
                palette_index = row[index]
                palette_offset = palette_index * 3
                if palette_offset + 3 > len(palette):
                    raise CompFidelityError(f"{label} palette index is invalid")
                red, green, blue = palette[palette_offset : palette_offset + 3]
                alpha = transparency[palette_index] if palette_index < len(transparency) else 255
            elif color_type == 4:
                red = green = blue = row[index]
                alpha = row[index + 1]
            else:
                red, green, blue, alpha = row[index : index + 4]
            rgba[output : output + 4] = bytes((red, green, blue, alpha))
            output += 4
    return PngImage(int(width), int(height), bytes(rgba))


def read_png(path_value: Path) -> PngImage:
    snapshot = _snapshot_file(path_value, label="PNG")
    return _decode_png(snapshot.data)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)


def write_png(path: Path, image: PngImage) -> None:
    path.write_bytes(_png_bytes(image))


def _png_bytes(image: PngImage) -> bytes:
    if image.width < 1 or image.height < 1 or len(image.rgba) != image.width * image.height * 4:
        raise CompFidelityError("RGBA image dimensions and byte count do not agree")
    rows = bytearray()
    stride = image.width * 4
    for y in range(image.height):
        rows.append(0)
        rows.extend(image.rgba[y * stride : (y + 1) * stride])
    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + _chunk(b"IEND", b"")
    )


def _json_object(path_value: Path, *, label: str) -> tuple[FileSnapshot, dict[str, Any]]:
    snapshot = _snapshot_file(path_value, label=label, max_bytes=1024 * 1024)
    try:
        payload = json.loads(snapshot.data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CompFidelityError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise CompFidelityError(f"{label} must contain a JSON object")
    return snapshot, payload


def _number(value: Any, *, label: str, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CompFidelityError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise CompFidelityError(f"{label} must be between {minimum} and {maximum}")
    return result


def _load_spec_snapshot(path_value: Path) -> tuple[FileSnapshot, dict[str, Any]]:
    snapshot, payload = _json_object(path_value, label="spec")
    allowed = {"schema", "case_id", "coordinate_space", "changed_pixel_delta", "regions", "advisory_thresholds"}
    missing = sorted((allowed - {"advisory_thresholds"}) - set(payload))
    extra = sorted(set(payload) - allowed)
    if missing or extra:
        raise CompFidelityError(f"spec fields mismatch: missing={missing}, unsupported={extra}")
    if payload.get("schema") != SPEC_SCHEMA:
        raise CompFidelityError(f"spec.schema must be {SPEC_SCHEMA}")
    case_id = payload.get("case_id")
    if not isinstance(case_id, str) or not SLUG.fullmatch(case_id):
        raise CompFidelityError("spec.case_id must be a lowercase slug")
    coordinate = payload.get("coordinate_space")
    if not isinstance(coordinate, dict) or set(coordinate) != {"width", "height"}:
        raise CompFidelityError("spec.coordinate_space must contain width and height")
    width, height = coordinate.get("width"), coordinate.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or not isinstance(height, int) or isinstance(height, bool):
        raise CompFidelityError("spec coordinate dimensions must be integers")
    if width < 1 or width > MAX_SPEC_WIDTH or height < 1 or height > MAX_DIMENSION or width * height > MAX_PIXELS:
        raise CompFidelityError("spec coordinate dimensions exceed the supported bound")
    payload["changed_pixel_delta"] = _number(payload.get("changed_pixel_delta"), label="spec.changed_pixel_delta")
    regions = payload.get("regions")
    if not isinstance(regions, list) or not 1 <= len(regions) <= 24:
        raise CompFidelityError("spec.regions must contain 1 to 24 regions")
    seen: set[str] = set()
    total_region_pixels = 0
    for index, region in enumerate(regions):
        label = f"spec.regions[{index}]"
        if not isinstance(region, dict) or set(region) != {"id", "box", "salience", "dimensions", "note"}:
            raise CompFidelityError(f"{label} has invalid fields")
        region_id = region.get("id")
        if not isinstance(region_id, str) or not SLUG.fullmatch(region_id) or region_id in seen:
            raise CompFidelityError(f"{label}.id must be a unique lowercase slug")
        seen.add(region_id)
        box = region.get("box")
        if not isinstance(box, list) or len(box) != 4 or any(isinstance(item, bool) or not isinstance(item, int) for item in box):
            raise CompFidelityError(f"{label}.box must be [x, y, width, height] integers")
        x, y, region_width, region_height = box
        if x < 0 or y < 0 or region_width < 1 or region_height < 1 or x + region_width > width or y + region_height > height:
            raise CompFidelityError(f"{label}.box leaves the coordinate space")
        total_region_pixels += region_width * region_height
        if region.get("salience") not in SALIENCE:
            raise CompFidelityError(f"{label}.salience is invalid")
        dimensions = region.get("dimensions")
        if not isinstance(dimensions, list) or not dimensions or len(dimensions) != len(set(dimensions)) or not set(dimensions) <= DIMENSIONS:
            raise CompFidelityError(f"{label}.dimensions is invalid")
        if not isinstance(region.get("note"), str) or not region["note"].strip():
            raise CompFidelityError(f"{label}.note must be non-empty")
    if total_region_pixels > MAX_REGION_PIXELS:
        raise CompFidelityError(
            f"spec region coverage exceeds the {MAX_REGION_PIXELS}-pixel processing bound"
        )
    thresholds = payload.get("advisory_thresholds")
    if thresholds is not None:
        if not isinstance(thresholds, dict) or not thresholds or not set(thresholds) <= METRIC_NAMES:
            raise CompFidelityError("spec.advisory_thresholds has invalid fields")
        payload["advisory_thresholds"] = {
            key: _number(value, label=f"spec.advisory_thresholds.{key}")
            for key, value in thresholds.items()
        }
    return snapshot, payload


def load_spec(path_value: Path) -> tuple[Path, dict[str, Any]]:
    snapshot, payload = _load_spec_snapshot(path_value)
    return snapshot.path, payload


def _luminance(red: int, green: int, blue: int) -> float:
    return (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255.0


def _metrics(reference: PngImage, rendered: PngImage, box: list[int], changed_delta: float) -> dict[str, float]:
    x, y, width, height = box
    channel_delta = 0
    squared = 0
    changed = 0
    ref_luminance = 0.0
    rendered_luminance = 0.0
    ref_edge_total = 0.0
    rendered_edge_total = 0.0
    edge_count = 0
    pixel_count = width * height
    for py in range(y, y + height):
        for px in range(x, x + width):
            offset = (py * reference.width + px) * 4
            ref_rgb = reference.rgba[offset : offset + 3]
            got_rgb = rendered.rgba[offset : offset + 3]
            deltas = [abs(int(a) - int(b)) for a, b in zip(ref_rgb, got_rgb)]
            channel_delta += sum(deltas)
            squared += sum(delta * delta for delta in deltas)
            changed += max(deltas) / 255.0 > changed_delta
            ref_value = _luminance(*ref_rgb)
            rendered_value = _luminance(*got_rgb)
            ref_luminance += ref_value
            rendered_luminance += rendered_value
            if px + 1 < x + width:
                right = offset + 4
                ref_edge_total += abs(ref_value - _luminance(*reference.rgba[right : right + 3]))
                rendered_edge_total += abs(rendered_value - _luminance(*rendered.rgba[right : right + 3]))
                edge_count += 1
            if py + 1 < y + height:
                below = offset + reference.width * 4
                ref_edge_total += abs(ref_value - _luminance(*reference.rgba[below : below + 3]))
                rendered_edge_total += abs(rendered_value - _luminance(*rendered.rgba[below : below + 3]))
                edge_count += 1

    ref_edge = ref_edge_total / edge_count if edge_count else 0.0
    rendered_edge = rendered_edge_total / edge_count if edge_count else 0.0
    return {
        "mean_delta": round(channel_delta / (pixel_count * 3 * 255), 8),
        "rmse": round(math.sqrt(squared / (pixel_count * 3)) / 255, 8),
        "max_delta_threshold": changed_delta,
        "changed_pixel_ratio": round(changed / pixel_count, 8),
        "reference_luminance": round(ref_luminance / pixel_count, 8),
        "rendered_luminance": round(rendered_luminance / pixel_count, 8),
        "signed_luminance_shift": round((rendered_luminance - ref_luminance) / pixel_count, 8),
        "reference_edge_energy": round(ref_edge, 8),
        "rendered_edge_energy": round(rendered_edge, 8),
        "edge_energy_delta": round(abs(rendered_edge - ref_edge), 8),
    }


def _crop(image: PngImage, box: list[int]) -> PngImage:
    x, y, width, height = box
    output = bytearray(width * height * 4)
    for row in range(height):
        start = ((y + row) * image.width + x) * 4
        output[row * width * 4 : (row + 1) * width * 4] = image.rgba[start : start + width * 4]
    return PngImage(width, height, bytes(output))


def _side_by_side(reference: PngImage, rendered: PngImage) -> PngImage:
    output = bytearray(reference.width * 2 * reference.height * 4)
    row_bytes = reference.width * 4
    output_row = row_bytes * 2
    for y in range(reference.height):
        output[y * output_row : y * output_row + row_bytes] = reference.rgba[y * row_bytes : (y + 1) * row_bytes]
        output[y * output_row + row_bytes : (y + 1) * output_row] = rendered.rgba[y * row_bytes : (y + 1) * row_bytes]
    return PngImage(reference.width * 2, reference.height, bytes(output))


def _heatmap(reference: PngImage, rendered: PngImage) -> PngImage:
    output = bytearray(len(reference.rgba))
    for offset in range(0, len(output), 4):
        delta = max(abs(reference.rgba[offset + channel] - rendered.rgba[offset + channel]) for channel in range(3))
        output[offset : offset + 4] = bytes((delta, min(255, delta * 2), 255 - delta, 255))
    return PngImage(reference.width, reference.height, bytes(output))


def _artifact(path: Path, root: Path, image: PngImage) -> dict[str, Any]:
    snapshot = _snapshot_file(path, label="generated artifact")
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": snapshot.size,
        "sha256": snapshot.sha256,
        "width": image.width,
        "height": image.height,
    }


def _input(snapshot: FileSnapshot, image: PngImage) -> dict[str, Any]:
    return {
        "name": snapshot.path.name,
        "bytes": snapshot.size,
        "sha256": snapshot.sha256,
        "width": image.width,
        "height": image.height,
    }


def _spec_input(snapshot: FileSnapshot) -> dict[str, Any]:
    return {
        "name": snapshot.path.name,
        "bytes": snapshot.size,
        "sha256": snapshot.sha256,
    }


def _advisory(overall: dict[str, float], spec: dict[str, Any]) -> dict[str, Any] | None:
    thresholds = spec.get("advisory_thresholds")
    if not thresholds:
        return None
    failed = sorted(key for key, maximum in thresholds.items() if overall[key] > maximum)
    return {
        "status": "outside" if failed else "within",
        "failed_metrics": failed,
        "thresholds": thresholds,
    }


def compare(
    *,
    reference_path: Path,
    rendered_path: Path,
    spec_path: Path,
    output_dir: Path,
    observed_at: str | None = None,
) -> dict[str, Any]:
    reference_snapshot = _snapshot_file(reference_path, label="reference PNG")
    rendered_snapshot = _snapshot_file(rendered_path, label="rendered PNG")
    spec_snapshot, spec = _load_spec_snapshot(spec_path)
    reference = _decode_png(reference_snapshot.data, label="reference PNG")
    rendered = _decode_png(rendered_snapshot.data, label="rendered PNG")
    expected_size = (spec["coordinate_space"]["width"], spec["coordinate_space"]["height"])
    if (reference.width, reference.height) != expected_size or (rendered.width, rendered.height) != expected_size:
        raise CompFidelityError("reference, rendered, and spec coordinate spaces must match exactly; resizing is not performed")
    output_dir = output_dir.expanduser().absolute()
    if output_dir.exists():
        raise CompFidelityError("output directory must not already exist")
    if not output_dir.parent.is_dir() or output_dir.parent.is_symlink():
        raise CompFidelityError("output parent must be an existing non-symlink directory")
    if observed_at is None:
        observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed_observed_at = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CompFidelityError("observed_at must be an ISO-8601 timestamp") from exc
    if "T" not in observed_at or parsed_observed_at.tzinfo is None:
        raise CompFidelityError("observed_at must include a time and UTC offset")
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        heatmap = _heatmap(reference, rendered)
        pair = _side_by_side(reference, rendered)
        heatmap_path = stage / "heatmap.png"
        pair_path = stage / "side-by-side.png"
        write_png(heatmap_path, heatmap)
        write_png(pair_path, pair)
        artifact_records: dict[str, Any] = {
            "heatmap": _artifact(heatmap_path, stage, heatmap),
            "side_by_side": _artifact(pair_path, stage, pair),
        }
        regions_dir = stage / "regions"
        regions_dir.mkdir()
        regions: list[dict[str, Any]] = []
        for region in spec["regions"]:
            region_id = region["id"]
            reference_crop = _crop(reference, region["box"])
            rendered_crop = _crop(rendered, region["box"])
            region_pair = _side_by_side(reference_crop, rendered_crop)
            region_heatmap = _heatmap(reference_crop, rendered_crop)
            region_pair_path = regions_dir / f"{region_id}-pair.png"
            region_heatmap_path = regions_dir / f"{region_id}-heatmap.png"
            write_png(region_pair_path, region_pair)
            write_png(region_heatmap_path, region_heatmap)
            regions.append(
                {
                    **region,
                    "metrics": _metrics(reference, rendered, region["box"], spec["changed_pixel_delta"]),
                    "artifacts": {
                        "pair": _artifact(region_pair_path, stage, region_pair),
                        "heatmap": _artifact(region_heatmap_path, stage, region_heatmap),
                    },
                }
            )
        overall = _metrics(reference, rendered, [0, 0, reference.width, reference.height], spec["changed_pixel_delta"])
        advisory = _advisory(overall, spec)
        report = {
            "schema": REPORT_SCHEMA,
            "verdict": "measurement_only",
            "case_id": spec["case_id"],
            "observed_at": observed_at,
            "coordinate_space": spec["coordinate_space"],
            "measurement_policy": {
                "alignment": "exact_coordinates_no_registration_or_resize",
                "changed_pixel_delta": spec["changed_pixel_delta"],
                "color_channels": "8_bit_srgb_bytes_alpha_ignored",
            },
            "inputs": {
                "reference": _input(reference_snapshot, reference),
                "rendered": _input(rendered_snapshot, rendered),
                "spec": _spec_input(spec_snapshot),
            },
            "overall_metrics": overall,
            "regions": regions,
            "artifacts": artifact_records,
            "advisory": advisory,
            "limitations": [
                "Pixel measurements do not establish product correctness, accessibility, interaction feel, or final visual quality.",
                "Alignment, fonts, browser, viewport, state, and capture timing must be controlled outside this tool.",
                "Human region review remains required; advisory thresholds are project-owned and non-final.",
            ],
        }
        report_path = stage / "report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if output_dir.exists():
            raise CompFidelityError("output directory appeared before atomic promotion")
        os.replace(stage, output_dir)
        return report
    except Exception:
        for candidate in sorted(stage.rglob("*"), reverse=True):
            if candidate.is_file() or candidate.is_symlink():
                candidate.unlink(missing_ok=True)
            elif candidate.is_dir():
                candidate.rmdir()
        stage.rmdir()
        raise


def _safe_artifact(report_dir: Path, record: Any, *, label: str) -> Path:
    record = _exact_fields(
        record,
        {"path", "bytes", "sha256", "width", "height"},
        label=f"{label} artifact",
    )
    raw = record.get("path")
    if not isinstance(raw, str) or not raw or "\\" in raw or PurePosixPath(raw).is_absolute() or ".." in PurePosixPath(raw).parts:
        raise CompFidelityError(f"{label}.path must be a safe relative path")
    byte_count = _positive_integer(record.get("bytes"), label=f"{label}.bytes")
    width = _positive_integer(record.get("width"), label=f"{label}.width")
    height = _positive_integer(record.get("height"), label=f"{label}.height")
    expected_sha = _validate_sha(record.get("sha256"), label=f"{label}.sha256")
    if byte_count > MAX_FILE_BYTES:
        raise CompFidelityError(f"{label}.bytes exceeds the {MAX_FILE_BYTES}-byte artifact bound")
    if width > MAX_DIMENSION or height > MAX_DIMENSION or width * height > MAX_SINGLE_ARTIFACT_PIXELS:
        raise CompFidelityError(f"{label} dimensions exceed the artifact processing bound")
    path = report_dir / PurePosixPath(raw)
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(report_dir.resolve())
    except ValueError as exc:
        raise CompFidelityError(f"{label}.path leaves the report directory") from exc
    current = report_dir
    for part in PurePosixPath(raw).parts:
        current = current / part
        if current.is_symlink():
            raise CompFidelityError(f"{label}.path must not traverse a symlink")
    snapshot = _snapshot_file(path, label=f"{label} artifact")
    if snapshot.size != byte_count or snapshot.sha256 != expected_sha:
        raise CompFidelityError(f"{label} artifact hash or size mismatch")
    image = _decode_png(
        snapshot.data,
        label=f"{label} artifact PNG",
        max_pixels=MAX_SINGLE_ARTIFACT_PIXELS,
    )
    if (image.width, image.height) != (width, height):
        raise CompFidelityError(f"{label} artifact dimensions mismatch")
    return path


def _exact_fields(value: Any, fields: set[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        actual = set(value) if isinstance(value, dict) else set()
        raise CompFidelityError(
            f"{label} fields mismatch: missing={sorted(fields - actual)}, unsupported={sorted(actual - fields)}"
        )
    return value


def _positive_integer(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise CompFidelityError(f"{label} must be a positive integer")
    return value


def _validate_sha(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise CompFidelityError(f"{label} must be a lowercase SHA-256")
    return value


def _validate_input_record(value: Any, *, label: str, image: bool) -> dict[str, Any]:
    fields = {"name", "bytes", "sha256", "width", "height"} if image else {"name", "bytes", "sha256"}
    record = _exact_fields(value, fields, label=label)
    if not isinstance(record["name"], str) or not record["name"] or "/" in record["name"] or "\\" in record["name"]:
        raise CompFidelityError(f"{label}.name must be one non-empty filename")
    byte_count = _positive_integer(record["bytes"], label=f"{label}.bytes")
    byte_limit = MAX_FILE_BYTES if image else 1024 * 1024
    if byte_count > byte_limit:
        raise CompFidelityError(f"{label}.bytes exceeds the {byte_limit}-byte input bound")
    _validate_sha(record["sha256"], label=f"{label}.sha256")
    if image:
        _positive_integer(record["width"], label=f"{label}.width")
        _positive_integer(record["height"], label=f"{label}.height")
    return record


def _validate_metrics(value: Any, *, label: str, changed_delta: float) -> dict[str, float]:
    record = _exact_fields(value, METRIC_FIELDS, label=label)
    normalized: dict[str, float] = {}
    for key in METRIC_FIELDS:
        minimum = -1.0 if key == "signed_luminance_shift" else 0.0
        normalized[key] = _number(record[key], label=f"{label}.{key}", minimum=minimum, maximum=1.0)
    if normalized["max_delta_threshold"] != changed_delta:
        raise CompFidelityError(f"{label}.max_delta_threshold disagrees with measurement policy")
    return normalized


def _validate_report_structure(report: dict[str, Any]) -> None:
    top_fields = {
        "schema",
        "verdict",
        "case_id",
        "observed_at",
        "coordinate_space",
        "measurement_policy",
        "inputs",
        "overall_metrics",
        "regions",
        "artifacts",
        "advisory",
        "limitations",
    }
    _exact_fields(report, top_fields, label="manifest")
    if report["schema"] != REPORT_SCHEMA or report["verdict"] != "measurement_only":
        raise CompFidelityError("manifest schema or measurement-only verdict is invalid")
    if not isinstance(report["case_id"], str) or not SLUG.fullmatch(report["case_id"]):
        raise CompFidelityError("manifest.case_id must be a lowercase slug")
    if not isinstance(report["observed_at"], str):
        raise CompFidelityError("manifest.observed_at must be an ISO-8601 timestamp")
    try:
        observed = datetime.fromisoformat(report["observed_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise CompFidelityError("manifest.observed_at must be an ISO-8601 timestamp") from exc
    if "T" not in report["observed_at"] or observed.tzinfo is None:
        raise CompFidelityError("manifest.observed_at must include a time and UTC offset")
    coordinate = _exact_fields(report["coordinate_space"], {"width", "height"}, label="manifest.coordinate_space")
    width = _positive_integer(coordinate["width"], label="manifest.coordinate_space.width")
    height = _positive_integer(coordinate["height"], label="manifest.coordinate_space.height")
    if width > MAX_SPEC_WIDTH or height > MAX_DIMENSION or width * height > MAX_PIXELS:
        raise CompFidelityError("manifest coordinate space exceeds the processing bound")
    policy = _exact_fields(
        report["measurement_policy"],
        {"alignment", "changed_pixel_delta", "color_channels"},
        label="manifest.measurement_policy",
    )
    if policy["alignment"] != "exact_coordinates_no_registration_or_resize" or policy["color_channels"] != "8_bit_srgb_bytes_alpha_ignored":
        raise CompFidelityError("manifest measurement policy is unsupported")
    changed_delta = _number(policy["changed_pixel_delta"], label="manifest.measurement_policy.changed_pixel_delta")
    inputs = _exact_fields(report["inputs"], {"reference", "rendered", "spec"}, label="manifest.inputs")
    _validate_input_record(inputs["reference"], label="manifest.inputs.reference", image=True)
    _validate_input_record(inputs["rendered"], label="manifest.inputs.rendered", image=True)
    _validate_input_record(inputs["spec"], label="manifest.inputs.spec", image=False)
    for name in ("reference", "rendered"):
        if (inputs[name]["width"], inputs[name]["height"]) != (width, height):
            raise CompFidelityError(f"manifest.inputs.{name} dimensions disagree with coordinate_space")
    _validate_metrics(report["overall_metrics"], label="manifest.overall_metrics", changed_delta=changed_delta)
    regions = report["regions"]
    if not isinstance(regions, list) or not 1 <= len(regions) <= 24:
        raise CompFidelityError("manifest.regions must contain 1 to 24 entries")
    seen: set[str] = set()
    region_pixels = 0
    for index, region in enumerate(regions):
        label = f"manifest.regions[{index}]"
        record = _exact_fields(
            region,
            {"id", "box", "salience", "dimensions", "note", "metrics", "artifacts"},
            label=label,
        )
        region_id = record["id"]
        if not isinstance(region_id, str) or not SLUG.fullmatch(region_id) or region_id in seen:
            raise CompFidelityError(f"{label}.id must be a unique lowercase slug")
        seen.add(region_id)
        box = record["box"]
        if not isinstance(box, list) or len(box) != 4 or any(isinstance(item, bool) or not isinstance(item, int) for item in box):
            raise CompFidelityError(f"{label}.box must be [x, y, width, height] integers")
        x, y, region_width, region_height = box
        if x < 0 or y < 0 or region_width < 1 or region_height < 1 or x + region_width > width or y + region_height > height:
            raise CompFidelityError(f"{label}.box leaves the coordinate space")
        region_pixels += region_width * region_height
        if record["salience"] not in SALIENCE:
            raise CompFidelityError(f"{label}.salience is invalid")
        dimensions = record["dimensions"]
        if not isinstance(dimensions, list) or not dimensions or len(dimensions) != len(set(dimensions)) or not set(dimensions) <= DIMENSIONS:
            raise CompFidelityError(f"{label}.dimensions is invalid")
        if not isinstance(record["note"], str) or not record["note"].strip():
            raise CompFidelityError(f"{label}.note must be non-empty")
        _validate_metrics(record["metrics"], label=f"{label}.metrics", changed_delta=changed_delta)
        _exact_fields(record["artifacts"], {"pair", "heatmap"}, label=f"{label}.artifacts")
    if region_pixels > MAX_REGION_PIXELS or 3 * (width * height + region_pixels) > MAX_ARTIFACT_PIXELS:
        raise CompFidelityError("manifest region or artifact work exceeds the processing bound")
    _exact_fields(report["artifacts"], {"heatmap", "side_by_side"}, label="manifest.artifacts")
    advisory = report["advisory"]
    if advisory is not None:
        advisory_record = _exact_fields(advisory, {"status", "failed_metrics", "thresholds"}, label="manifest.advisory")
        if advisory_record["status"] not in {"within", "outside"}:
            raise CompFidelityError("manifest.advisory.status is invalid")
        failed = advisory_record["failed_metrics"]
        thresholds = advisory_record["thresholds"]
        if not isinstance(failed, list) or len(failed) != len(set(failed)) or not set(failed) <= METRIC_NAMES:
            raise CompFidelityError("manifest.advisory.failed_metrics is invalid")
        if not isinstance(thresholds, dict) or not thresholds or not set(thresholds) <= METRIC_NAMES:
            raise CompFidelityError("manifest.advisory.thresholds is invalid")
        for key, value in thresholds.items():
            _number(value, label=f"manifest.advisory.thresholds.{key}")
        expected_status = "outside" if failed else "within"
        expected_failed = sorted(
            key
            for key, maximum in thresholds.items()
            if report["overall_metrics"][key] > maximum
        )
        if advisory_record["status"] != expected_status or failed != expected_failed:
            raise CompFidelityError("manifest.advisory disagrees with metrics and thresholds")
    limitations = report["limitations"]
    if not isinstance(limitations, list) or len(limitations) < 3 or any(not isinstance(item, str) or not item.strip() for item in limitations):
        raise CompFidelityError("manifest.limitations must contain at least three non-empty statements")


def _assert_expected_artifact(record: dict[str, Any], image: PngImage, *, label: str) -> None:
    payload = _png_bytes(image)
    expected = {
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "width": image.width,
        "height": image.height,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise CompFidelityError(f"strict {label}.{key} does not match recomputed evidence")


def validate_report(
    manifest_path: Path,
    *,
    reference_path: Path | None = None,
    rendered_path: Path | None = None,
    spec_path: Path | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    manifest_snapshot, report = _json_object(manifest_path, label="manifest")
    manifest_path = manifest_snapshot.path
    _validate_report_structure(report)
    artifacts = report.get("artifacts")
    regions = report.get("regions")
    if not isinstance(artifacts, dict) or set(artifacts) != {"heatmap", "side_by_side"} or not isinstance(regions, list) or not regions:
        raise CompFidelityError("manifest artifact or region inventory is invalid")
    count = 0
    artifact_paths: set[str] = set()
    for name, record in artifacts.items():
        _safe_artifact(manifest_path.parent, record, label=f"artifacts.{name}")
        if record["path"] in artifact_paths:
            raise CompFidelityError("manifest artifact paths must be unique")
        artifact_paths.add(record["path"])
        count += 1
    for index, region in enumerate(regions):
        if not isinstance(region, dict) or not isinstance(region.get("artifacts"), dict):
            raise CompFidelityError(f"regions[{index}] is invalid")
        for name, record in region["artifacts"].items():
            _safe_artifact(manifest_path.parent, record, label=f"regions[{index}].artifacts.{name}")
            if record["path"] in artifact_paths:
                raise CompFidelityError("manifest artifact paths must be unique")
            artifact_paths.add(record["path"])
            count += 1
    if strict:
        if reference_path is None or rendered_path is None or spec_path is None:
            raise CompFidelityError("strict validation requires reference, rendered, and spec inputs")
        reference_snapshot = _snapshot_file(reference_path, label="reference")
        rendered_snapshot = _snapshot_file(rendered_path, label="rendered")
        spec_snapshot, spec = _load_spec_snapshot(spec_path)
        reference = _decode_png(reference_snapshot.data, label="reference PNG")
        rendered = _decode_png(rendered_snapshot.data, label="rendered PNG")
        inputs = report["inputs"]
        if inputs["reference"] != _input(reference_snapshot, reference):
            raise CompFidelityError("strict reference input record mismatch")
        if inputs["rendered"] != _input(rendered_snapshot, rendered):
            raise CompFidelityError("strict rendered input record mismatch")
        if inputs["spec"] != _spec_input(spec_snapshot):
            raise CompFidelityError("strict spec input record mismatch")
        if report["case_id"] != spec["case_id"] or report["coordinate_space"] != spec["coordinate_space"]:
            raise CompFidelityError("strict report identity or coordinate space disagrees with spec")
        if (reference.width, reference.height) != (rendered.width, rendered.height) or [reference.width, reference.height] != [spec["coordinate_space"]["width"], spec["coordinate_space"]["height"]]:
            raise CompFidelityError("strict input dimensions disagree with the spec")
        overall = _metrics(reference, rendered, [0, 0, reference.width, reference.height], spec["changed_pixel_delta"])
        if report["overall_metrics"] != overall:
            raise CompFidelityError("strict overall metrics do not match recomputed evidence")
        if report["advisory"] != _advisory(overall, spec):
            raise CompFidelityError("strict advisory does not match recomputed evidence")
        if len(report["regions"]) != len(spec["regions"]):
            raise CompFidelityError("strict region inventory disagrees with spec")
        _assert_expected_artifact(report["artifacts"]["heatmap"], _heatmap(reference, rendered), label="artifacts.heatmap")
        _assert_expected_artifact(report["artifacts"]["side_by_side"], _side_by_side(reference, rendered), label="artifacts.side_by_side")
        for index, (region_report, region_spec) in enumerate(zip(report["regions"], spec["regions"])):
            for key in ("id", "box", "salience", "dimensions", "note"):
                if region_report[key] != region_spec[key]:
                    raise CompFidelityError(f"strict regions[{index}].{key} disagrees with spec")
            expected_metrics = _metrics(reference, rendered, region_spec["box"], spec["changed_pixel_delta"])
            if region_report["metrics"] != expected_metrics:
                raise CompFidelityError(f"strict regions[{index}].metrics do not match recomputed evidence")
            reference_crop = _crop(reference, region_spec["box"])
            rendered_crop = _crop(rendered, region_spec["box"])
            _assert_expected_artifact(region_report["artifacts"]["pair"], _side_by_side(reference_crop, rendered_crop), label=f"regions[{index}].artifacts.pair")
            _assert_expected_artifact(region_report["artifacts"]["heatmap"], _heatmap(reference_crop, rendered_crop), label=f"regions[{index}].artifacts.heatmap")
    return {"schema": "design-craft.comp-fidelity-validation.v1", "ok": True, "manifest": str(manifest_path), "artifact_count": count, "strict": strict}
