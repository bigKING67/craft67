"""Shared runtime loaders and fixture builders for Creative Craft tests."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = ROOT / "skills" / "creative-craft" / "scripts" / "creative_craft.py"
SPEC = importlib.util.spec_from_file_location("creative_craft_cli", CLI_PATH)
assert SPEC and SPEC.loader
cc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cc
SPEC.loader.exec_module(cc)

INSTALLER_PATH = ROOT / "scripts" / "install_skill.py"
INSTALLER_SPEC = importlib.util.spec_from_file_location(
    "creative_craft_installer", INSTALLER_PATH
)
assert INSTALLER_SPEC and INSTALLER_SPEC.loader
installer = importlib.util.module_from_spec(INSTALLER_SPEC)
sys.modules[INSTALLER_SPEC.name] = installer
INSTALLER_SPEC.loader.exec_module(installer)

BUILD_RELEASE_PATH = ROOT / "scripts" / "build_release.py"
BUILD_RELEASE_SPEC = importlib.util.spec_from_file_location(
    "creative_craft_build_release", BUILD_RELEASE_PATH
)
assert BUILD_RELEASE_SPEC and BUILD_RELEASE_SPEC.loader
build_release = importlib.util.module_from_spec(BUILD_RELEASE_SPEC)
sys.modules[BUILD_RELEASE_SPEC.name] = build_release
BUILD_RELEASE_SPEC.loader.exec_module(build_release)

PACKAGE_SMOKE_PATH = ROOT / "scripts" / "package_smoke.py"
PACKAGE_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "creative_craft_package_smoke", PACKAGE_SMOKE_PATH
)
assert PACKAGE_SMOKE_SPEC and PACKAGE_SMOKE_SPEC.loader
package_smoke = importlib.util.module_from_spec(PACKAGE_SMOKE_SPEC)
sys.modules[PACKAGE_SMOKE_SPEC.name] = package_smoke
PACKAGE_SMOKE_SPEC.loader.exec_module(package_smoke)


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def tree_snapshot(root: Path) -> dict[str, tuple[str, bytes | str | None]]:
    snapshot: dict[str, tuple[str, bytes | str | None]] = {}
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()
    ):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = ("symlink", str(path.readlink()))
        elif path.is_dir():
            snapshot[relative] = ("dir", None)
        else:
            snapshot[relative] = ("file", path.read_bytes())
    return snapshot


def refresh_manifest(root: Path) -> dict:
    manifest_path = root / "project-manifest.json"
    if not manifest_path.is_file():
        manifest_path = root / ".creative-craft" / "project-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["artifacts"]:
        entry["sha256"] = cc.sha256_file(root / entry["path"])
    write_json(manifest_path, manifest)
    return manifest


def approve_copy_sheet(copy_sheet: dict) -> dict:
    approved = copy.deepcopy(copy_sheet)
    approved["status"] = "approved"
    approved["use_scope"] = "public"
    approved["approval"].update(
        {
            "status": "approved",
            "approved_by": "fictional-business-owner",
            "approved_at": "2026-08-14T09:00:00Z",
            "basis": "Named owner approved the rights-safe fictional fixture.",
        }
    )
    evidence_groups = [approved["strategy"]]
    evidence_groups.extend(approved["proof_hierarchy"])
    evidence_groups.extend(approved["copy_routes"])
    evidence_groups.extend(approved["copy_units"])
    for item in evidence_groups:
        if item["evidence_state"] == "HYPOTHESIZED":
            item["evidence_state"] = "INFERRED"
    return approved


def init_brand_pack(
    root: Path, brand_id: str = "acme", brand_name: str = "Acme"
) -> Path:
    skill_root = root / f"{brand_id}-brand"
    args = type(
        "Args",
        (),
        {
            "target": str(skill_root),
            "brand_id": brand_id,
            "brand_name": brand_name,
            "owner": "fixture-owner",
            "force": False,
        },
    )()
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        if cc.cmd_init_brand_pack(args) != 0:
            raise AssertionError("Brand Pack fixture initialization failed")
    return skill_root


def approve_brand_pack(
    skill_root: Path, version: str = "0.1.0", *, require_valid: bool = True
) -> dict:
    manifest_path = skill_root / "brand-pack.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "version": version,
            "status": "approved",
            "approved_at": "2026-08-04T00:00:00Z",
            "review_after": "2027-08-04T00:00:00Z",
            "source_references": [
                {
                    "source_id": "fixture-authority",
                    "uri": "https://brand.invalid/authority",
                    "version": version,
                    "reviewed_at": "2026-08-04T00:00:00Z",
                    "notes": "Synthetic test authority only.",
                }
            ],
        }
    )
    for item in manifest["authority_files"]:
        authority_path = skill_root / item["path"]
        authority_path.write_text(
            f"# Reviewed {item['role']} authority\n\n"
            "Status: `APPROVED`\n\nSynthetic fixture authority; no real brand claim.\n",
            encoding="utf-8",
        )
        item["sha256"] = cc.sha256_file(authority_path)
    write_json(manifest_path, manifest)
    graph = cc.validate_brand_pack(skill_root)
    if require_valid and not graph.result.ok:
        raise AssertionError(graph.result.errors)
    return manifest


def bind_brand_pack(project: Path, skill_root: Path) -> None:
    args = type(
        "Args",
        (),
        {
            "brand_source_uri": "https://git.invalid/acme-brand-pack.git",
            "brand_source_ref": "main",
            "brand_source_commit": "1" * 40,
            "imported_by": "fixture-operator",
            "reason": "Initial fixture binding",
        },
    )()
    cc._install_brand_snapshot(
        project,
        skill_root,
        args,
        require_existing_binding=False,
        retain_backup=False,
    )


def init_reference_pack(
    root: Path,
    pack_id: str = "reference-fixture",
    name: str = "Reference Fixture",
) -> Path:
    skill_root = root / pack_id
    args = type(
        "Args",
        (),
        {
            "target": str(skill_root),
            "pack_id": pack_id,
            "name": name,
            "owner": "fixture-owner",
            "force": False,
        },
    )()
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        if cc.cmd_init_reference_pack(args) != 0:
            raise AssertionError("Reference Pack fixture initialization failed")
    return skill_root


def add_reference_entity(
    skill_root: Path,
    reference_id: str,
    *,
    with_asset: bool = False,
    rights_status: str = "CLEARED",
    rights_policy: str | None = None,
) -> dict:
    manifest_path = skill_root / "reference-pack.json"
    ledger_path = skill_root / "asset-ledger.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    source_id = f"source-{reference_id}"
    asset_refs: list[str] = []
    if with_asset:
        asset_id = f"asset-{reference_id}"
        asset_path = skill_root / "assets" / "approved" / f"{reference_id}.bin"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_bytes(f"synthetic-{reference_id}".encode())
        asset_refs.append(asset_id)
        ledger["assets"].append(
            {
                "asset_id": asset_id,
                "path_or_uri": asset_path.relative_to(skill_root).as_posix(),
                "mime_type": "application/octet-stream",
                "sha256": cc.sha256_file(asset_path),
                "creator": "fixture",
                "owner": "fixture",
                "rights_status": rights_status,
                "consent_status": "NOT_APPLICABLE",
                "allowed_use": ["synthetic-tests"],
                "expires_at": None,
                "reference_roles": ["research"],
                "parent_assets": [],
                "notes": "Synthetic test asset only.",
            }
        )
    manifest["source_references"].append(
        {
            "source_id": source_id,
            "authority": "research",
            "uri": f"https://reference.invalid/{reference_id}",
            "captured_at": "2026-08-04T00:00:00Z",
            "snapshot_path": None,
            "sha256": None,
            "notes": "Synthetic test source only.",
        }
    )
    manifest["entities"].append(
        {
            "reference_id": reference_id,
            "entity_type": "other",
            "name": f"Synthetic {reference_id}",
            "relationship": "reference",
            "summary": "Synthetic test reference only.",
            "source_refs": [source_id],
            "observations": [
                {
                    "observation_id": f"observation-{reference_id}",
                    "dimension": "synthetic-test",
                    "evidence_state": "OBSERVED",
                    "statement": "Synthetic observation for contract testing.",
                    "evidence_refs": [source_id],
                }
            ],
            "transferable_principles": [
                {
                    "principle_id": f"principle-{reference_id}",
                    "derived_from": [f"observation-{reference_id}"],
                    "statement": "Adapt the abstract principle; do not copy expression.",
                    "application_scope": ["synthetic-tests"],
                    "adaptation_required": True,
                    "must_preserve_primary_brand": ["identity", "claims", "rights"],
                }
            ],
            "non_transferable_elements": ["identity", "distinctive expression"],
            "applicable_to": ["synthetic-tests"],
            "reference_roles": ["principle"],
            "rights_policy": rights_policy
            or ("approved_reference_input" if with_asset else "principle_only"),
            "prohibited_use": ["identity imitation"],
            "asset_refs": asset_refs,
            "may_override_primary_brand": False,
        }
    )
    write_json(ledger_path, ledger)
    manifest["asset_ledger"]["sha256"] = cc.sha256_file(ledger_path)
    write_json(manifest_path, manifest)
    graph = cc.validate_reference_pack(skill_root)
    if not graph.result.ok:
        raise AssertionError(graph.result.errors)
    return manifest


def bind_reference_source_snapshot(
    skill_root: Path, manifest: dict, index: int = 0
) -> dict:
    source = manifest["source_references"][index]
    source_path = skill_root / "sources" / f"{source['source_id']}.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        f"Synthetic content-bound evidence for {source['source_id']}.\n",
        encoding="utf-8",
    )
    source["snapshot_path"] = source_path.relative_to(skill_root).as_posix()
    source["sha256"] = cc.sha256_file(source_path)
    write_json(skill_root / "reference-pack.json", manifest)
    return manifest


def bind_reference_pack(
    project: Path,
    skill_root: Path,
    selected: list[str] | None = None,
) -> None:
    args = type(
        "Args",
        (),
        {
            "reference_source_uri": "https://git.invalid/reference-pack.git",
            "reference_source_ref": "main",
            "reference_source_commit": "3" * 40,
            "imported_by": "fixture-operator",
            "reason": "Initial synthetic reference binding",
            "select": selected,
        },
    )()
    cc._install_reference_snapshot(
        project,
        skill_root,
        args,
        require_existing_binding=False,
        retain_backup=False,
    )
