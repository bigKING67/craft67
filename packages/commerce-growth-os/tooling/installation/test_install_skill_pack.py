#!/usr/bin/env python3
"""Regression tests for bounded, transactional skill installation."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
from pathlib import Path

from install_skill_pack import (
    INSTALL_JOURNAL_NAME,
    INSTALL_JOURNAL_TEMP_NAME,
    INSTALL_LOCK_NAME,
    INSTALLER_VERSION,
    expand_root,
    install_bundles,
    load_install_manifest,
    prepare_install_root,
    recover_installation,
    tree_digest,
    write_install_journal,
)
from tooling.installation.tree_integrity import TreeIntegrityError, tree_hashes, validate_tree
from tooling.manifest import ManifestError, load_manifest


TEST_OWNED_SKILLS = {"first", "second"}


def test_journal_payload(phase: str, skills: list[dict[str, object]]) -> dict[str, object]:
    manifest = load_install_manifest()
    return {
        "schema_version": 2,
        "pack_name": manifest["pack_name"],
        "pack_version": manifest["pack_version"],
        "installer_version": INSTALLER_VERSION,
        "transaction_id": "1" * 32,
        "phase": phase,
        "skills": skills,
    }


def recover_test_installation(
    install_root: Path, *, force_stale_lock: bool = False
) -> list[str]:
    return recover_installation(
        install_root,
        force_stale_lock=force_stale_lock,
        owned_names=TEST_OWNED_SKILLS,
    )


def write_bundle(root: Path, name: str, content: str) -> Path:
    bundle = root / name
    bundle.mkdir()
    (bundle / "SKILL.md").write_text(content, encoding="utf-8")
    return bundle


def assert_content(install_root: Path, name: str, expected: str) -> None:
    actual = (install_root / name / "SKILL.md").read_text(encoding="utf-8")
    assert actual == expected, (name, actual, expected)


def assert_no_transaction_artifacts(install_root: Path) -> None:
    assert not list(install_root.glob(".*.staged"))
    assert not list(install_root.glob(".*.backup"))
    assert not (install_root / INSTALL_LOCK_NAME).exists()
    assert not (install_root / INSTALL_JOURNAL_NAME).exists()
    assert not (install_root / INSTALL_JOURNAL_TEMP_NAME).exists()


def expect_runtime_error(action, expected: str) -> None:
    try:
        action()
    except RuntimeError as exc:
        assert expected in str(exc), (expected, str(exc))
    else:
        raise AssertionError(f"expected RuntimeError containing {expected!r}")


def test_successful_replacement() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        second = write_bundle(bundles, "second", "new-second")
        write_bundle(install_root, "first", "old-first")

        warnings = install_bundles([first, second], install_root)

        assert warnings == []
        assert_content(install_root, "first", "new-first")
        assert_content(install_root, "second", "new-second")
        assert_no_transaction_artifacts(install_root)


def test_prepare_install_root_validates_ancestors_before_creation() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        safe_root = prepare_install_root(root / "safe" / "nested")
        assert safe_root.is_dir()

        target = root / "symlink-target"
        target.mkdir()
        linked = root / "linked"
        linked.symlink_to(target, target_is_directory=True)
        requested = linked / "must-not-be-created" / "nested"
        expect_runtime_error(
            lambda: prepare_install_root(requested),
            "real directory ancestor",
        )
        assert not (target / "must-not-be-created").exists()


def test_staging_failure_cleanup() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        second = write_bundle(bundles, "second", "new-second")
        write_bundle(install_root, "first", "old-first")

        def fail_after_first_stage(event: str, path: Path) -> None:
            if event == "after_stage" and path.name == ".first.staged":
                raise OSError("injected staging failure")

        try:
            install_bundles([first, second], install_root, fault_injector=fail_after_first_stage)
        except OSError as exc:
            assert "injected staging failure" in str(exc)
        else:
            raise AssertionError("injected staging failure should abort installation")

        assert_content(install_root, "first", "old-first")
        assert not (install_root / "second").exists()
        assert_no_transaction_artifacts(install_root)


def test_partial_backup_rolls_back() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        second = write_bundle(bundles, "second", "new-second")
        write_bundle(install_root, "first", "old-first")
        write_bundle(install_root, "second", "old-second")

        def fail_after_first_backup(event: str, path: Path) -> None:
            if event == "after_backup" and path.name == ".first.backup":
                raise OSError("injected backup failure")

        try:
            install_bundles([first, second], install_root, fault_injector=fail_after_first_backup)
        except OSError as exc:
            assert "injected backup failure" in str(exc)
        else:
            raise AssertionError("partial backup should abort installation")

        assert_content(install_root, "first", "old-first")
        assert_content(install_root, "second", "old-second")
        assert_no_transaction_artifacts(install_root)


def test_partial_activation_rolls_back() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        second = write_bundle(bundles, "second", "new-second")
        write_bundle(install_root, "first", "old-first")
        write_bundle(install_root, "second", "old-second")

        def fail_after_first_activation(event: str, path: Path) -> None:
            if event == "after_activate" and path.name == "first":
                raise OSError("injected activation failure")

        try:
            install_bundles([first, second], install_root, fault_injector=fail_after_first_activation)
        except OSError as exc:
            assert "injected activation failure" in str(exc)
        else:
            raise AssertionError("partial activation should abort installation")

        assert_content(install_root, "first", "old-first")
        assert_content(install_root, "second", "old-second")
        assert_no_transaction_artifacts(install_root)


def test_cleanup_failure_is_observable_after_commit() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        write_bundle(install_root, "first", "old-first")

        def fail_cleanup(event: str, path: Path) -> None:
            if event == "before_cleanup":
                raise OSError("injected cleanup failure")

        warnings = install_bundles([first], install_root, fault_injector=fail_cleanup)

        assert len(warnings) == 1
        assert "install committed" in warnings[0]
        assert_content(install_root, "first", "new-first")
        assert_content(install_root, ".first.backup", "old-first")
        assert not (install_root / INSTALL_LOCK_NAME).exists()
        assert (install_root / INSTALL_JOURNAL_NAME).is_file()

        (install_root / "first" / "SKILL.md").write_text("tampered", encoding="utf-8")
        expect_runtime_error(
            lambda: recover_test_installation(install_root),
            "target digest differs; backup retained",
        )
        assert_content(install_root, ".first.backup", "old-first")
        assert (install_root / INSTALL_JOURNAL_NAME).is_file()
        (install_root / "first" / "SKILL.md").write_text("new-first", encoding="utf-8")
        actions = recover_test_installation(install_root)
        assert any("removed committed backup" in action for action in actions)
        assert_content(install_root, "first", "new-first")
        assert_no_transaction_artifacts(install_root)


def test_keyboard_interrupt_rolls_back() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        write_bundle(install_root, "first", "old-first")

        def interrupt_after_backup(event: str, path: Path) -> None:
            if event == "after_backup":
                raise KeyboardInterrupt(f"injected interrupt after {path}")

        try:
            install_bundles([first], install_root, fault_injector=interrupt_after_backup)
        except KeyboardInterrupt as exc:
            assert "injected interrupt" in str(exc)
        else:
            raise AssertionError("KeyboardInterrupt should abort installation")

        assert_content(install_root, "first", "old-first")
        assert_no_transaction_artifacts(install_root)


def test_rollback_failure_preserves_journal_for_recovery() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        write_bundle(install_root, "first", "old-first")

        def obstruct_rollback(event: str, path: Path) -> None:
            if event == "after_backup":
                conflict = install_root / "first"
                conflict.mkdir()
                (conflict / "SKILL.md").write_text("conflict", encoding="utf-8")
                raise OSError(f"injected failure after {path}")

        expect_runtime_error(
            lambda: install_bundles([first], install_root, fault_injector=obstruct_rollback),
            "rollback also failed",
        )
        assert (install_root / INSTALL_JOURNAL_NAME).is_file()
        assert_content(install_root, ".first.backup", "old-first")

        conflict = install_root / "first"
        for child in conflict.iterdir():
            child.unlink()
        conflict.rmdir()
        actions = recover_test_installation(install_root)
        assert any("restored previous target" in action for action in actions)
        assert_content(install_root, "first", "old-first")
        assert_no_transaction_artifacts(install_root)


def test_precommit_journal_recovery_restores_old_target() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        install_root = root / "installed"
        install_root.mkdir()
        target = write_bundle(install_root, "first", "old-first")
        staged = write_bundle(install_root, ".first.staged", "new-first")
        backup = install_root / ".first.backup"
        target.rename(backup)
        assert staged.is_dir()
        write_install_journal(
            install_root,
            test_journal_payload(
                "activating",
                [
                    {
                        "name": "first",
                        "had_target": True,
                        "tree_sha256": tree_digest(staged),
                    }
                ],
            ),
        )

        actions = recover_test_installation(install_root)
        assert any("restored previous target" in action for action in actions)
        assert_content(install_root, "first", "old-first")
        assert_no_transaction_artifacts(install_root)


def test_recovery_rejects_unowned_journal_entries() -> None:
    with tempfile.TemporaryDirectory() as temp:
        install_root = Path(temp) / "installed"
        install_root.mkdir()
        unrelated = write_bundle(install_root, "unrelated-skill", "must-stay")
        write_install_journal(
            install_root,
            test_journal_payload(
                "activating",
                [
                    {
                        "name": "unrelated-skill",
                        "had_target": False,
                        "tree_sha256": "0" * 64,
                    }
                ],
            ),
        )

        expect_runtime_error(
            lambda: recover_test_installation(install_root),
            "unowned Skill",
        )
        assert unrelated.is_dir()
        assert_content(install_root, "unrelated-skill", "must-stay")
        assert (install_root / INSTALL_JOURNAL_NAME).is_file()
        assert not (install_root / INSTALL_LOCK_NAME).exists()


def test_recovery_validates_identity_uniqueness_and_new_target_digest() -> None:
    with tempfile.TemporaryDirectory() as temp:
        install_root = Path(temp) / "installed"
        install_root.mkdir()
        target = write_bundle(install_root, "first", "unexpected-content")
        expected = Path(temp) / "expected"
        expected.mkdir()
        expected_bundle = write_bundle(expected, "first", "expected-content")
        write_install_journal(
            install_root,
            test_journal_payload(
                "activating",
                [
                    {
                        "name": "first",
                        "had_target": False,
                        "tree_sha256": tree_digest(expected_bundle),
                    }
                ],
            ),
        )
        expect_runtime_error(
            lambda: recover_test_installation(install_root),
            "newly activated target digest differs; retained",
        )
        assert target.is_dir()
        assert_content(install_root, "first", "unexpected-content")

    for mutation, expected_error in (
        ("duplicate", "duplicate Skill entries"),
        ("pack", "pack identity"),
        ("legacy", "unsupported install transaction journal"),
    ):
        with tempfile.TemporaryDirectory() as temp:
            install_root = Path(temp) / "installed"
            install_root.mkdir()
            target = write_bundle(install_root, "first", "must-stay")
            entry = {"name": "first", "had_target": True, "tree_sha256": tree_digest(target)}
            payload = test_journal_payload("activating", [entry])
            if mutation == "duplicate":
                payload["skills"] = [entry, dict(entry)]
            elif mutation == "pack":
                payload["pack_name"] = "another-pack"
            else:
                payload["schema_version"] = 1
            write_install_journal(install_root, payload)
            expect_runtime_error(
                lambda: recover_test_installation(install_root),
                expected_error,
            )
            assert_content(install_root, "first", "must-stay")
            assert (install_root / INSTALL_JOURNAL_NAME).is_file()


def test_stale_transaction_paths_fail_closed() -> None:
    for suffix in ("staged", "backup"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundles = root / "bundles"
            install_root = root / "installed"
            bundles.mkdir()
            install_root.mkdir()
            first = write_bundle(bundles, "first", "new-first")
            stale = install_root / f".first.{suffix}"
            stale.mkdir()

            expect_runtime_error(
                lambda: install_bundles([first], install_root),
                "stale install staging path",
            )
            assert stale.is_dir()
            assert not (install_root / "first").exists()
            assert not (install_root / INSTALL_LOCK_NAME).exists()


def test_target_file_and_symlink_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        target = install_root / "first"
        target.write_text("not a directory", encoding="utf-8")

        expect_runtime_error(lambda: install_bundles([first], install_root), "not a real directory")
        assert target.read_text(encoding="utf-8") == "not a directory"
        target.unlink()

        real_target = root / "elsewhere"
        real_target.mkdir()
        target.symlink_to(real_target, target_is_directory=True)
        expect_runtime_error(lambda: install_bundles([first], install_root), "not a real directory")
        assert target.is_symlink()
        assert_no_transaction_artifacts(install_root)


def test_install_root_symlink_and_single_writer_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        real_install_root = root / "installed"
        linked_install_root = root / "linked-installed"
        bundles.mkdir()
        real_install_root.mkdir()
        linked_install_root.symlink_to(real_install_root, target_is_directory=True)
        first = write_bundle(bundles, "first", "new-first")

        expanded_link = expand_root(str(linked_install_root))
        assert expanded_link == linked_install_root.absolute()

        expect_runtime_error(
            lambda: install_bundles([first], expanded_link),
            "install root must be a real directory",
        )

        real_parent = root / "real-parent"
        real_parent.mkdir()
        ancestor_install_root = real_parent / "skills"
        ancestor_install_root.mkdir()
        linked_parent = root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        through_ancestor_link = linked_parent / "skills"
        expect_runtime_error(
            lambda: install_bundles([first], through_ancestor_link),
            "install root must be a real directory",
        )
        assert not (ancestor_install_root / INSTALL_LOCK_NAME).exists()

        lock = real_install_root / INSTALL_LOCK_NAME
        lock.mkdir()
        expect_runtime_error(
            lambda: install_bundles([first], real_install_root),
            "another installation is running",
        )
        assert lock.is_dir()
        assert not (real_install_root / "first").exists()

        expect_runtime_error(
            lambda: recover_test_installation(real_install_root),
            "confirm no installer is running",
        )
        actions = recover_test_installation(real_install_root, force_stale_lock=True)
        assert actions == ["no interrupted transaction found"]
        assert_no_transaction_artifacts(real_install_root)


def test_concurrent_writer_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundles = root / "bundles"
        install_root = root / "installed"
        bundles.mkdir()
        install_root.mkdir()
        first = write_bundle(bundles, "first", "new-first")
        first_writer_started = threading.Event()
        release_first_writer = threading.Event()
        first_writer_errors: list[Exception] = []

        def pause_after_stage(event: str, path: Path) -> None:
            if event == "after_stage":
                first_writer_started.set()
                if not release_first_writer.wait(timeout=5):
                    raise TimeoutError(f"timed out while holding install lock for {path}")

        def run_first_writer() -> None:
            try:
                install_bundles([first], install_root, fault_injector=pause_after_stage)
            except Exception as exc:
                first_writer_errors.append(exc)

        thread = threading.Thread(target=run_first_writer)
        thread.start()
        assert first_writer_started.wait(timeout=5), "first writer did not acquire the install lock"
        try:
            expect_runtime_error(
                lambda: install_bundles([first], install_root),
                "another installation is running",
            )
        finally:
            release_first_writer.set()
            thread.join(timeout=5)

        assert not thread.is_alive()
        assert first_writer_errors == []
        assert_content(install_root, "first", "new-first")
        assert_no_transaction_artifacts(install_root)


def test_tree_integrity_rejects_links_special_files_and_escape() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        allowed = root / "allowed"
        outside = root / "outside"
        allowed.mkdir()
        outside.mkdir()
        (outside / "payload.txt").write_text("outside", encoding="utf-8")

        try:
            validate_tree(outside, allowed_root=allowed)
        except TreeIntegrityError as exc:
            assert "escapes allowed root" in str(exc)
        else:
            raise AssertionError("source outside the allowed root should fail")

        linked = allowed / "linked.txt"
        linked.symlink_to(outside / "payload.txt")
        try:
            validate_tree(allowed, require_directory=True)
        except TreeIntegrityError as exc:
            assert "symlink is not allowed" in str(exc)
        else:
            raise AssertionError("nested symlink should fail tree validation")
        linked.unlink()

        if hasattr(os, "mkfifo"):
            fifo = allowed / "pipe"
            os.mkfifo(fifo)
            try:
                validate_tree(allowed, require_directory=True)
            except TreeIntegrityError as exc:
                assert "non-regular" in str(exc)
            else:
                raise AssertionError("special filesystem entry should fail tree validation")


def test_tree_hashes_never_follow_symlinks() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        safe = root / "safe"
        unsafe = root / "unsafe"
        safe.mkdir()
        unsafe.mkdir()
        payload = safe / "payload.txt"
        payload.write_text("same content", encoding="utf-8")
        (unsafe / "payload.txt").symlink_to(payload)

        assert tree_hashes(safe)
        try:
            tree_hashes(unsafe)
        except TreeIntegrityError as exc:
            assert "symlink is not allowed" in str(exc)
        else:
            raise AssertionError("tree_hashes must never follow a symlink")


def test_shared_manifest_contract() -> None:
    base = {
        "schema_version": 2,
        "pack_version": "2.0.0",
        "minimum_installer_version": "2.0.0",
        "pack_name": "test-pack",
        "default_install_root": "~/skills",
        "duplicate_discovery_roots": [],
        "skills": [
            {
                "name": "test-skill",
                "source": "skills/test-skill",
                "routing_terms": ["test"],
                "resources": [{"source": "shared/test.md", "target": "references/test.md"}],
            }
        ],
    }

    def check(payload: dict, expected: str | None = None) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            if expected is None:
                assert load_manifest(path)["skills"][0]["name"] == "test-skill"
                return
            try:
                load_manifest(path)
            except ManifestError as exc:
                assert expected in str(exc), (expected, str(exc))
            else:
                raise AssertionError(f"invalid manifest should fail with {expected!r}")

    check(base)
    invalid_version = copy.deepcopy(base)
    invalid_version["pack_version"] = "v2"
    check(invalid_version, "semantic version")
    invalid_name = copy.deepcopy(base)
    invalid_name["skills"][0]["name"] = "Test Skill"
    check(invalid_name, "invalid name")
    duplicate_name = copy.deepcopy(base)
    duplicate_name["skills"].append(copy.deepcopy(duplicate_name["skills"][0]))
    check(duplicate_name, "duplicate skill name")
    invalid_resource = copy.deepcopy(base)
    invalid_resource["skills"][0]["resources"][0]["extra"] = True
    check(invalid_resource, "invalid resource mapping")


def main() -> int:
    test_prepare_install_root_validates_ancestors_before_creation()
    test_successful_replacement()
    test_staging_failure_cleanup()
    test_partial_backup_rolls_back()
    test_partial_activation_rolls_back()
    test_cleanup_failure_is_observable_after_commit()
    test_keyboard_interrupt_rolls_back()
    test_precommit_journal_recovery_restores_old_target()
    test_recovery_rejects_unowned_journal_entries()
    test_recovery_validates_identity_uniqueness_and_new_target_digest()
    test_rollback_failure_preserves_journal_for_recovery()
    test_stale_transaction_paths_fail_closed()
    test_target_file_and_symlink_fail_closed()
    test_install_root_symlink_and_single_writer_fail_closed()
    test_concurrent_writer_is_rejected()
    test_tree_integrity_rejects_links_special_files_and_escape()
    test_tree_hashes_never_follow_symlinks()
    test_shared_manifest_contract()
    print("install_skill_pack regression tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
