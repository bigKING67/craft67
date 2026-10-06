#!/usr/bin/env python3
"""Offline verification for one atomic Commerce Skill Pack release directory."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    is_runtime_cache,
    validate_real_directory,
    validate_tree,
)


MAX_ARCHIVE_FILES = 10_000
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
HEX_64 = re.compile(r"\A[0-9a-f]{64}\Z")
GIT_SHA = re.compile(r"\A[0-9a-f]{40,64}\Z")
SEMVER = re.compile(r"\A(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")


class ReleaseVerificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(hashes: dict[str, str]) -> str:
    encoded = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require_hex64(value: object, field: str) -> str:
    if not isinstance(value, str) or not HEX_64.fullmatch(value):
        raise ReleaseVerificationError(f"attestation field must be a SHA-256 digest: {field}")
    return value


def require_artifact_name(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or Path(value).name != value
        or value in {".", ".."}
    ):
        raise ReleaseVerificationError(f"attestation field must be a plain artifact name: {field}")
    return value


def read_attestation(release_dir: Path) -> tuple[Path, dict[str, Any]]:
    candidates = sorted(release_dir.glob("*.attestation.json"))
    if len(candidates) != 1:
        raise ReleaseVerificationError("release directory must contain exactly one attestation")
    path = candidates[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseVerificationError(f"cannot read release attestation: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ReleaseVerificationError("release attestation has an unsupported schema_version")
    return path, payload


def verify_archive(
    archive: Path,
    *,
    prefix: str,
    expected_tree_digests: dict[str, str],
) -> dict[str, Any]:
    if not isinstance(prefix, str) or not prefix or "/" in prefix or prefix in {".", ".."}:
        raise ReleaseVerificationError("archive prefix must be one plain path component")
    if not expected_tree_digests:
        raise ReleaseVerificationError("attestation bundle tree digest map is empty")
    for skill, digest in expected_tree_digests.items():
        require_artifact_name(skill, f"bundle_tree_sha256.{skill}")
        require_hex64(digest, f"bundle_tree_sha256.{skill}")

    member_names: set[str] = set()
    file_hashes: dict[str, dict[str, str]] = {skill: {} for skill in expected_tree_digests}
    seen_skills: set[str] = set()
    file_count = 0
    total_bytes = 0
    try:
        archive_handle = tarfile.open(archive, mode="r:gz")
    except (OSError, tarfile.TarError) as exc:
        raise ReleaseVerificationError(f"cannot open release archive: {exc}") from exc
    with archive_handle:
        members = archive_handle.getmembers()
        if len(members) > MAX_ARCHIVE_FILES * 2:
            raise ReleaseVerificationError("release archive has too many members")
        for member in members:
            if member.name in member_names:
                raise ReleaseVerificationError(f"release archive contains a duplicate member: {member.name}")
            member_names.add(member.name)
            path = PurePosixPath(member.name)
            parts = path.parts
            if (
                not parts
                or parts[0] != prefix
                or path.is_absolute()
                or any(part in {"", ".", ".."} for part in parts)
            ):
                raise ReleaseVerificationError(f"release archive member escapes its prefix: {member.name}")
            relative = parts[1:]
            if member.uid != 0 or member.gid != 0 or member.uname or member.gname or member.mtime != 0:
                raise ReleaseVerificationError(f"release archive metadata is not normalized: {member.name}")
            if not relative:
                if not member.isdir():
                    raise ReleaseVerificationError("release archive prefix entry must be a directory")
                if member.mode & 0o777 != 0o755:
                    raise ReleaseVerificationError("release archive prefix directory mode is not 0755")
                continue
            skill = relative[0]
            if skill not in expected_tree_digests:
                raise ReleaseVerificationError(f"release archive contains an unexpected Skill: {skill}")
            seen_skills.add(skill)
            if member.isdir():
                if member.mode & 0o777 != 0o755:
                    raise ReleaseVerificationError(f"release archive directory mode is not 0755: {member.name}")
                continue
            if not member.isreg():
                raise ReleaseVerificationError(
                    f"release archive contains a link or special entry: {member.name}"
                )
            if len(relative) < 2:
                raise ReleaseVerificationError(f"release archive has a file at the Skill root name: {member.name}")
            relative_file_path = Path(*relative[1:])
            if is_runtime_cache(relative_file_path):
                raise ReleaseVerificationError(f"release archive contains a runtime cache artifact: {member.name}")
            expected_mode = 0o755 if "scripts" in relative_file_path.parts else 0o644
            if member.mode & 0o777 != expected_mode:
                raise ReleaseVerificationError(
                    f"release archive file mode is not {expected_mode:04o}: {member.name}"
                )
            file_count += 1
            total_bytes += member.size
            if file_count > MAX_ARCHIVE_FILES or total_bytes > MAX_ARCHIVE_BYTES:
                raise ReleaseVerificationError("release archive exceeds offline verification limits")
            extracted = archive_handle.extractfile(member)
            if extracted is None:
                raise ReleaseVerificationError(f"cannot read release archive member: {member.name}")
            digest = hashlib.sha256()
            actual_size = 0
            with extracted:
                for chunk in iter(lambda: extracted.read(1024 * 1024), b""):
                    actual_size += len(chunk)
                    digest.update(chunk)
            if actual_size != member.size:
                raise ReleaseVerificationError(f"release archive member size mismatch: {member.name}")
            relative_file = PurePosixPath(*relative[1:]).as_posix()
            if relative_file in file_hashes[skill]:
                raise ReleaseVerificationError(f"release archive repeats a Skill file: {member.name}")
            file_hashes[skill][relative_file] = digest.hexdigest()

    if seen_skills != set(expected_tree_digests):
        missing = sorted(set(expected_tree_digests) - seen_skills)
        raise ReleaseVerificationError(f"release archive is missing Skills: {', '.join(missing)}")
    for skill, hashes in file_hashes.items():
        if "SKILL.md" not in hashes:
            raise ReleaseVerificationError(f"release archive Skill is missing SKILL.md: {skill}")
        if tree_digest(hashes) != expected_tree_digests[skill]:
            raise ReleaseVerificationError(f"release archive tree digest mismatch: {skill}")
    return {
        "archive_prefix": prefix,
        "skills": sorted(file_hashes),
        "files": file_count,
        "uncompressed_bytes": total_bytes,
    }


def verify_release_directory(path: Path) -> dict[str, Any]:
    try:
        release_dir = validate_real_directory(path)
        validate_tree(release_dir, require_directory=True)
    except TreeIntegrityError as exc:
        raise ReleaseVerificationError(f"release directory is not a safe regular-file tree: {exc}") from exc

    attestation_path, attestation = read_attestation(release_dir)
    version = attestation.get("pack_version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ReleaseVerificationError("attestation pack_version is not strict semantic versioning")
    archive_name = require_artifact_name(attestation.get("archive"), "archive")
    checksum_name = require_artifact_name(attestation.get("checksum"), "checksum")
    expected_archive = f"consumer-brand-skill-pack-v{version}.tar.gz"
    expected_checksum = f"{expected_archive}.sha256"
    expected_attestation = f"consumer-brand-skill-pack-v{version}.attestation.json"
    if (
        archive_name != expected_archive
        or checksum_name != expected_checksum
        or attestation_path.name != expected_attestation
    ):
        raise ReleaseVerificationError("release artifact names do not match pack_version")

    expected_entries = {archive_name, checksum_name, expected_attestation}
    actual_entries = {entry.name for entry in release_dir.iterdir()}
    if actual_entries != expected_entries or any(not entry.is_file() for entry in release_dir.iterdir()):
        raise ReleaseVerificationError("release directory must contain exactly the archive, checksum, and attestation")

    archive = release_dir / archive_name
    checksum = release_dir / checksum_name
    archive_bytes = attestation.get("archive_bytes")
    if not isinstance(archive_bytes, int) or archive_bytes <= 0 or archive.stat().st_size != archive_bytes:
        raise ReleaseVerificationError("release archive size does not match attestation")
    archive_digest = sha256_file(archive)
    if archive_digest != require_hex64(attestation.get("archive_sha256"), "archive_sha256"):
        raise ReleaseVerificationError("release archive SHA-256 does not match attestation")
    attestation_digest = sha256_file(attestation_path)
    expected_checksum_text = (
        f"{archive_digest}  {archive_name}\n"
        f"{attestation_digest}  {expected_attestation}\n"
    )
    try:
        checksum_text = checksum.read_text(encoding="ascii")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReleaseVerificationError(f"cannot read release checksum: {exc}") from exc
    if checksum_text != expected_checksum_text:
        raise ReleaseVerificationError("release checksum does not bind the exact archive and attestation")

    if attestation.get("artifact_set_atomic") is not True:
        raise ReleaseVerificationError("attestation does not assert atomic artifact-set publication")
    if attestation.get("isolated_install_parity_verified") is not True:
        raise ReleaseVerificationError("attestation does not assert isolated install parity")
    if attestation.get("quality_regression_passed") is not True:
        raise ReleaseVerificationError("attestation does not assert a passing quality regression")
    quality_evidence_trust = attestation.get("quality_evidence_trust")
    quality_execution_authenticity = attestation.get("quality_execution_authenticity_verified")
    if quality_evidence_trust is not None and quality_evidence_trust != "self-attested-local":
        raise ReleaseVerificationError("attestation has an unsupported quality-evidence trust level")
    if quality_execution_authenticity is not None and quality_execution_authenticity is not False:
        raise ReleaseVerificationError(
            "attestation must not claim externally verified quality-execution authenticity"
        )
    git_head = attestation.get("git_head")
    if not isinstance(git_head, str) or not GIT_SHA.fullmatch(git_head) or attestation.get("git_clean") is not True:
        raise ReleaseVerificationError("attestation does not bind a clean Git commit")
    require_hex64(attestation.get("manifest_sha256"), "manifest_sha256")
    require_hex64(attestation.get("quality_evidence_sha256"), "quality_evidence_sha256")
    contract_hashes = attestation.get("quality_contract_input_sha256")
    if not isinstance(contract_hashes, dict) or not contract_hashes:
        raise ReleaseVerificationError("attestation quality contract hashes are missing")
    for name, digest in contract_hashes.items():
        if not isinstance(name, str) or not name:
            raise ReleaseVerificationError("attestation quality contract hash name is invalid")
        require_hex64(digest, f"quality_contract_input_sha256.{name}")
    tree_digests = attestation.get("bundle_tree_sha256")
    if not isinstance(tree_digests, dict):
        raise ReleaseVerificationError("attestation bundle tree hashes are missing")
    archive_summary = verify_archive(
        archive,
        prefix=attestation.get("archive_prefix"),
        expected_tree_digests=tree_digests,
    )
    return {
        "passed": True,
        "release_dir": str(release_dir),
        "pack_version": version,
        "archive_sha256": archive_digest,
        "quality_evidence_trust": quality_evidence_trust or "legacy-unspecified",
        "quality_execution_authenticity_verified": quality_execution_authenticity,
        **archive_summary,
    }


def write_fixture_archive(bundle_root: Path, archive: Path, prefix: str) -> None:
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as output:
                for source in sorted(bundle_root.rglob("*")):
                    relative = source.relative_to(bundle_root).as_posix()
                    info = output.gettarinfo(str(source), arcname=f"{prefix}/{relative}")
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    if source.is_file():
                        with source.open("rb") as handle:
                            output.addfile(info, handle)
                    else:
                        output.addfile(info)


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="release-verifier-self-test-") as temp:
        root = Path(temp).resolve()
        bundles = root / "bundles"
        skill = bundles / "example"
        skill.mkdir(parents=True)
        skill_file = skill / "SKILL.md"
        skill_file.write_text("example\n", encoding="utf-8")
        release = root / "v1.0.0"
        release.mkdir()
        archive_name = "consumer-brand-skill-pack-v1.0.0.tar.gz"
        checksum_name = f"{archive_name}.sha256"
        attestation_name = "consumer-brand-skill-pack-v1.0.0.attestation.json"
        archive = release / archive_name
        write_fixture_archive(bundles, archive, "consumer-brand-skill-pack-v1.0.0")
        archive_digest = sha256_file(archive)
        checksum = release / checksum_name
        attestation = {
            "schema_version": 1,
            "pack_version": "1.0.0",
            "git_head": "a" * 40,
            "git_clean": True,
            "manifest_sha256": "b" * 64,
            "quality_contract_input_sha256": {"manifest": "b" * 64},
            "archive": archive_name,
            "checksum": checksum_name,
            "archive_prefix": "consumer-brand-skill-pack-v1.0.0",
            "archive_sha256": archive_digest,
            "archive_bytes": archive.stat().st_size,
            "artifact_set_atomic": True,
            "isolated_install_parity_verified": True,
            "bundle_tree_sha256": {
                "example": tree_digest({"SKILL.md": hashlib.sha256(b"example\n").hexdigest()})
            },
            "quality_evidence_sha256": "c" * 64,
            "quality_evidence_trust": "self-attested-local",
            "quality_execution_authenticity_verified": False,
            "quality_regression_passed": True,
        }
        attestation_path = release / attestation_name
        attestation_path.write_text(
            json.dumps(attestation, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        checksum.write_text(
            f"{archive_digest}  {archive_name}\n"
            f"{sha256_file(attestation_path)}  {attestation_name}\n",
            encoding="ascii",
        )
        verify_release_directory(release)

        original_archive = archive.read_bytes()
        original_attestation = attestation_path.read_bytes()
        original_checksum = checksum.read_bytes()
        archive.write_bytes(archive.read_bytes() + b"tamper")
        try:
            verify_release_directory(release)
        except ReleaseVerificationError:
            pass
        else:
            raise AssertionError("tampered release archive must fail verification")
        archive.write_bytes(original_archive)

        attestation_path.write_bytes(original_attestation + b" ")
        try:
            verify_release_directory(release)
        except ReleaseVerificationError:
            pass
        else:
            raise AssertionError("tampered release attestation must fail verification")
        attestation_path.write_bytes(original_attestation)

        checksum.write_bytes(original_checksum.replace(archive_digest.encode("ascii"), b"0" * 64, 1))
        try:
            verify_release_directory(release)
        except ReleaseVerificationError:
            pass
        else:
            raise AssertionError("tampered release checksum must fail verification")
        checksum.write_bytes(original_checksum)

        extra = release / "unexpected.txt"
        extra.write_text("unexpected\n", encoding="utf-8")
        try:
            verify_release_directory(release)
        except ReleaseVerificationError:
            pass
        else:
            raise AssertionError("an extra release artifact must fail verification")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_dir", nargs="?")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print("release verifier self-test passed")
            return 0
        if not args.release_dir:
            raise ReleaseVerificationError("release_dir is required")
        result = verify_release_directory(Path(args.release_dir).expanduser())
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(
                f"release verification passed: v{result['pack_version']} / "
                f"{result['skills']} / {result['files']} files"
            )
        return 0
    except (OSError, TypeError, KeyError, TreeIntegrityError, ReleaseVerificationError) as exc:
        print(f"verify_release error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
