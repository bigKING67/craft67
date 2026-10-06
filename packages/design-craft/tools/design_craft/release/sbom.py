from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from ..repo import REPO_ROOT
from .integrity import sha256_file


SPDX_SCHEMA = "SPDX-2.3"


def _created_at(source_commit: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", "-s", "--format=%cI", source_commit],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("cannot resolve deterministic creation time from source_commit")
    return (
        datetime.fromisoformat(result.stdout.strip())
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def build_spdx(package: Path, *, version: str, source_commit: str) -> dict[str, object]:
    package_digest = sha256_file(package)
    files: list[dict[str, object]] = []
    verification_hashes: list[str] = []
    with tarfile.open(package, "r:gz") as archive:
        for index, member in enumerate(sorted(archive.getmembers(), key=lambda item: item.name)):
            if member.isdir():
                continue
            relative = PurePosixPath(member.name)
            if member.issym() or member.islnk() or not member.isfile():
                raise ValueError(f"package contains a non-regular entry: {member.name}")
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"package contains an unsafe path: {member.name}")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"cannot read package entry: {member.name}")
            content = extracted.read()
            sha1 = hashlib.sha1(content).hexdigest()
            sha256 = hashlib.sha256(content).hexdigest()
            verification_hashes.append(sha1)
            files.append(
                {
                    "SPDXID": f"SPDXRef-File-{index + 1}",
                    "fileName": f"./{relative.as_posix()}",
                    "checksums": [
                        {"algorithm": "SHA1", "checksumValue": sha1},
                        {"algorithm": "SHA256", "checksumValue": sha256},
                    ],
                    "licenseConcluded": "NOASSERTION",
                    "copyrightText": "NOASSERTION",
                }
            )
    verification = hashlib.sha1("".join(sorted(verification_hashes)).encode("ascii")).hexdigest()
    package_spdx_id = "SPDXRef-Package-design-craft"
    return {
        "spdxVersion": SPDX_SCHEMA,
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"design-craft-{version}",
        "documentNamespace": (
            "https://github.com/bigKING67/design-craft/spdx/"
            f"design-craft-{version}-{package_digest}"
        ),
        "creationInfo": {
            "created": _created_at(source_commit),
            "creators": ["Tool: design-craft-release-sbom/1"],
        },
        "packages": [
            {
                "name": "design-craft",
                "SPDXID": package_spdx_id,
                "versionInfo": version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": True,
                "packageVerificationCode": {
                    "packageVerificationCodeValue": verification
                },
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": package_digest}
                ],
                "licenseConcluded": "MIT",
                "licenseDeclared": "MIT",
                "copyrightText": "NOASSERTION",
            }
        ],
        "files": files,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": package_spdx_id,
            },
            *[
                {
                    "spdxElementId": package_spdx_id,
                    "relationshipType": "CONTAINS",
                    "relatedSpdxElement": item["SPDXID"],
                }
                for item in files
            ],
        ],
    }


def write_spdx(
    package: Path, output: Path, *, version: str, source_commit: str
) -> dict[str, object]:
    payload = build_spdx(package, version=version, source_commit=source_commit)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
