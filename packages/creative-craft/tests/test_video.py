"""Video Harness v1: shared-contract semantics and production stage gates."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from creative_craft_video import evaluate_promises, plan_structure_changes
from support import ROOT, cc, load, write_json
from video_support import (
    build_talking_head_production,
    edit_document,
    generate_beat,
    production,
    production_plan,
    record_export_render,
    render_qa,
    run_cli,
    stage,
    write_doc,
    write_generation,
)

FIXTURES = ROOT / "tests/fixtures"


def errors(data: dict) -> list[str]:
    return cc.validate_data(data)[1].errors


class EditDocumentContractTests(unittest.TestCase):
    def test_shared_valid_fixtures_pass(self) -> None:
        for name in ("multitrack", "p2-packaging"):
            with self.subTest(name):
                path = f"tests/fixtures/edit-document-v2/valid/{name}.json"
                self.assertEqual([], errors(load(path)))

    def test_every_shared_invalid_fixture_is_rejected_for_its_rule(self) -> None:
        expected = {
            "audio-only-asset-on-video-track": "requires an asset with video",
            "caption-link-reversed-range": "source_to must be greater",
            "caption-link-unknown-item": "link must reference a media item",
            "caption-on-video-track": "must be on a caption track",
            "duplicate-item-id": "duplicates id",
            "first-revision-with-parent": "revision 1 must have parent_sha256 null",
            "free-caption-missing-timing": "caption without link requires start_frame",
            "media-missing-source-in": "requires source_in_seconds",
            "same-track-overlap": "overlap",
            "source-range-exceeds-asset": "beyond asset duration",
            "unknown-asset": "unknown asset",
            "unknown-track": "unknown track",
            "media-with-caption-field": "media item must not set text",
            "caption-with-media-field": "caption item must not set volume",
            "linked-caption-with-timing": "linked caption must not set start_frame",
            "later-revision-without-parent": "revision > 1 requires parent_sha256",
            "audio-item-with-visual-field": "audio-track item must not set fit",
            "caption-with-visual-field": "caption item must not set opacity",
            "caption-link-beyond-asset": "link.source_to exceeds the linked asset duration",
            "caption-with-speed": "caption item must not set speed",
            "graphic-with-transform": "graphic item must not set transform",
            "duck-under-caption-track": "duck must reference a video or audio track",
            "crossfade-same-start": "overlap without a matching crossfade",
            "crossfade-nested-in-predecessor": "must exactly overlap the end of its preceding media item talk1",
            "crossfade-after-graphic": "must exactly overlap the end of its preceding media item lower",
            "graphic-var-bad-name": "vars key 'Title' must match",
            "graphic-var-too-long-utf16": "vars.title must be a string of 1-200",
            "graphic-template-unbound": "graphic template 'lower-third' has no graphic_templates binding",
            "graphic-template-duplicate-binding": "duplicates binding for 'lower-third'",
            "graphic-template-unused-binding": "binds 'title-card', which no graphic uses",
            "graphic-template-file-mismatch": "file must be templates/<sha256>.json",
            "audio-asset-with-frame-rate": "asset 'music' frame_rate requires a video stream",
            "crossfade-overlap-mismatch": "must exactly overlap the end of its preceding media item talk1",
            "crossfade-without-overlap": "crossfade of 5 frames must exactly overlap",
            "duck-on-video-track": "duck is only allowed on audio tracks",
            "duck-under-self": "duck must not reference its own track",
            "duck-under-unknown-track": "duck references unknown track",
            "fades-exceed-item": "fade_in_frames + fade_out_frames exceed frames",
            "graphic-on-caption-track": "graphic item must be on a video track",
            "graphic-var-not-primitive": "vars.title must be a string of 1-200",
            "graphic-with-media-field": "graphic item must not set volume",
            "overlap-without-crossfade": "overlap without a matching crossfade",
            "speed-source-exceeds-asset": "source range ends at 22s beyond asset",
        }
        paths = sorted((FIXTURES / "edit-document-v2/invalid").glob("*.json"))
        self.assertEqual(set(expected), {path.stem for path in paths})
        for path in paths:
            with self.subTest(path.stem):
                found = errors(json.loads(path.read_text(encoding="utf-8")))
                self.assertTrue(
                    any(expected[path.stem] in message for message in found), found
                )

    def test_later_revision_requires_parent_and_duration_limit(self) -> None:
        doc = edit_document(2, None)
        self.assertIn("revision > 1 requires parent_sha256", errors(doc))
        doc = edit_document(1)
        doc["items"] = [
            item
            for item in doc["items"]
            if item["kind"] == "caption" and "link" not in item
        ]
        self.assertIn("edit duration must be at least one frame", errors(doc))

    def test_timeline_helpers(self) -> None:
        doc = edit_document(2, "f" * 64, generated=True)
        self.assertEqual(450, cc.edit_document_duration_frames(doc))
        self.assertAlmostEqual(90 / 450, cc.edit_document_generated_share(doc))
        frames = cc.edit_document_item_frames(doc)
        self.assertEqual((0, 90), frames["cap1"])
        self.assertEqual((300, 390), frames["cap2"])


P2_FIXTURE = "tests/fixtures/edit-document-v2/valid/p2-packaging.json"


def p2_doc() -> dict:
    return load(P2_FIXTURE)


def p2_item(doc: dict, item_id: str) -> dict:
    return next(item for item in doc["items"] if item["id"] == item_id)


class EditDocumentP2Tests(unittest.TestCase):
    """P2 packaging/audio rules beyond the one-rule shared fixtures."""

    def assert_error(self, doc: dict, fragment: str) -> None:
        found = errors(doc)
        self.assertTrue(any(fragment in message for message in found), found)

    def test_crossfade_only_with_the_immediately_previous_item(self) -> None:
        doc = p2_doc()
        doc["items"].append(
            {
                "id": "talk3",
                "track_id": "v_main",
                "kind": "media",
                "asset_id": "talk",
                "start_frame": 255,
                "frames": 30,
                "source_in_seconds": 0,
                "volume": 1,
                "transition_in": {"kind": "crossfade", "frames": 5},
            }
        )
        self.assertEqual([], errors(doc))
        p2_item(doc, "talk3").update(
            start_frame=145, frames=155, transition_in={"kind": "crossfade", "frames": 115}
        )
        self.assert_error(doc, "items talk1 and talk3 overlap without a matching crossfade")

    def test_audio_crossfade_and_fades_at_the_limit_are_valid(self) -> None:
        doc = p2_doc()
        p2_item(doc, "bed")["frames"] = 260
        doc["items"].append(
            {
                "id": "bed2",
                "track_id": "a_music",
                "kind": "media",
                "asset_id": "music",
                "start_frame": 250,
                "frames": 30,
                "source_in_seconds": 10,
                "volume": 0.2,
                "transition_in": {"kind": "crossfade", "frames": 10},
            }
        )
        p2_item(doc, "talk1").update(fade_in_frames=100, fade_out_frames=50)
        self.assertEqual([], errors(doc))

    def test_field_exclusivity_for_media_caption_and_graphic(self) -> None:
        cases = [
            ("talk1", {"template": "lower-third"}, "media item must not set template"),
            ("title", {"fade_in_frames": 2}, "caption item must not set fade_in_frames"),
            (
                "title",
                {"transition_in": {"kind": "crossfade", "frames": 2}},
                "caption item must not set transition_in",
            ),
            ("cap1", {"speed": 2}, "caption item must not set speed"),
            ("lower", {"speed": 2}, "graphic item must not set speed"),
            ("lower", {"transform": {"x": 0, "y": 0, "scale": 1}}, "graphic item must not set transform"),
            (
                "lower",
                {"transition_in": {"kind": "crossfade", "frames": 2}},
                "graphic item must not set transition_in",
            ),
            ("lower", {"text": "x"}, "graphic item must not set text"),
        ]
        for item_id, patch, fragment in cases:
            with self.subTest(fragment):
                doc = p2_doc()
                p2_item(doc, item_id).update(patch)
                self.assert_error(doc, fragment)
        doc = p2_doc()
        del p2_item(doc, "lower")["template"]
        self.assert_error(doc, "graphic item requires template")
        doc = p2_doc()
        p2_item(doc, "lower")["track_id"] = "a_music"
        self.assert_error(doc, "graphic item must be on a video track")

    def test_graphic_vars_are_bounded_primitives(self) -> None:
        for value, ok in (
            ("", False),
            ("x" * 200, True),
            ("x" * 201, False),
            (True, True),
            (3.5, True),
            (float("nan"), False),
            ([1], False),
            (None, False),
        ):
            with self.subTest(value=value if not isinstance(value, str) else len(value)):
                doc = p2_doc()
                p2_item(doc, "lower")["vars"]["subtitle"] = value
                found = [m for m in errors(doc) if "vars.subtitle" in m]
                self.assertEqual(ok, not found, found)

    def test_graphics_follow_same_track_overlap_and_count_toward_duration(self) -> None:
        doc = p2_doc()
        p2_item(doc, "lower")["frames"] = 400
        self.assertEqual([], errors(doc))
        self.assertEqual(400, cc.edit_document_duration_frames(doc))
        doc["items"].append(
            {
                "id": "card",
                "track_id": "v_gfx",
                "kind": "graphic",
                "template": "title-card",
                "vars": {"title": "Hi"},
                "start_frame": 80,
                "frames": 30,
            }
        )
        self.assert_error(doc, "items lower and card overlap without a matching crossfade")

    def test_duck_targets_one_level_of_video_or_audio(self) -> None:
        doc = p2_doc()
        doc["tracks"][3]["duck"]["under_track_id"] = "c_sub"
        self.assert_error(doc, "duck must reference a video or audio track")
        doc = p2_doc()
        doc["tracks"].insert(
            3,
            {
                "id": "a_vo",
                "kind": "audio",
                "locked": False,
                "duck": {
                    "under_track_id": "v_main",
                    "depth_db": -6,
                    "attack_frames": 0,
                    "release_frames": 0,
                },
            },
        )
        self.assertEqual([], errors(doc))
        doc["tracks"][4]["duck"]["under_track_id"] = "a_vo"
        self.assert_error(doc, "duck target a_vo must not have its own duck")

    def test_speed_scales_source_range_and_linked_captions(self) -> None:
        doc = p2_doc()
        doc["items"].append(
            {
                "id": "cap2",
                "track_id": "c_sub",
                "kind": "caption",
                "text": "x",
                "link": {"item_id": "talk2", "source_from": 11.5, "source_to": 13.0},
            }
        )
        self.assertEqual([], errors(doc))
        frames = cc.edit_document_item_frames(doc)
        # talk2: start 140, source_in 10 s, speed 1.5 -> 1.5 s of source per 30 frames.
        self.assertEqual((170, 200), frames["cap2"])
        self.assertEqual((0, 75), frames["cap1"])
        p2_item(doc, "talk1")["speed"] = 0.5
        # 2.0-4.5 s at half speed spans 150 frames, clipped to the item's source end.
        self.assertEqual((0, 150), cc.edit_document_item_frames(doc)["cap1"])
        p2_item(doc, "talk2")["frames"] = 201
        self.assert_error(doc, "beyond asset duration")

    def test_generated_share_counts_media_only_and_crossfades_as_either(self) -> None:
        plan = {
            "delivery_promises": [
                {"id": "gen", "check": {"kind": "max_generated_share", "max": 0.5}}
            ]
        }
        doc = p2_doc()
        # Generated B-roll 60-120 of 270 frames; the graphic above it does not occlude.
        self.assertAlmostEqual(60 / 270, cc.edit_document_generated_share(doc))
        generated = copy.deepcopy(doc["assets"][1])
        generated.update(id="gen_talk", duration=20)
        doc["assets"].append(generated)
        p2_item(doc, "talk2")["asset_id"] = "gen_talk"
        # B-roll 60 + talk2 140-260 (crossfade 140-150 counts as generated) = 180.
        self.assertAlmostEqual(180 / 270, cc.edit_document_generated_share(doc))
        p2_item(doc, "talk2")["asset_id"] = "talk"
        p2_item(doc, "talk1")["asset_id"] = "gen_talk"
        # talk1 0-150 including the crossfade it hands over to talk2.
        self.assertAlmostEqual(150 / 270, cc.edit_document_generated_share(doc))
        [promise] = evaluate_promises(plan, doc)
        self.assertEqual((0.5556, False), (promise["observed"], promise["passed"]))


class RenderQaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qa = load("tests/fixtures/render-qa/sample.json")

    def test_sample_passes(self) -> None:
        self.assertEqual([], errors(self.qa))

    def test_review_rules(self) -> None:
        cases = {
            "completed review requires reviewer": lambda qa: qa["review"].update(
                reviewer=None
            ),
            "completed review requires a decision": lambda qa: qa["review"].update(
                decision="pending"
            ),
            "pending decision requires review.status pending": lambda qa: (
                qa["review"].update(status="pending", decision="pending", reviewer="x")
                or qa["review"].update(status="done")
            ),
            "contradicts checks": lambda qa: qa.update(verdict="pass"),
            "critical finding requires fix": lambda qa: (
                qa["review"]["findings"][0].update(severity="critical")
                or qa["review"]["findings"][0].pop("fix")
            ),
            "unknown sample": lambda qa: qa["checks"][3]["refs"][0].update(
                sample_id="ghost"
            ),
        }
        for message, mutate in cases.items():
            with self.subTest(message):
                qa = copy.deepcopy(self.qa)
                mutate(qa)
                self.assertTrue(
                    any(message in error for error in errors(qa)), errors(qa)
                )

    def test_verdict_derivation(self) -> None:
        qa = copy.deepcopy(self.qa)
        qa["checks"][2]["status"] = "fail"
        qa["verdict"] = "fail"
        self.assertEqual([], errors(qa))
        qa["checks"][2]["status"] = "pass"
        qa["verdict"] = "pass"
        self.assertEqual([], errors(qa))


class ProductionPlanContractTests(unittest.TestCase):
    def test_plan_rules(self) -> None:
        self.assertEqual([], errors(production_plan()))
        cases = {
            "duplicates id": lambda plan: plan["beats"].append(
                copy.deepcopy(plan["beats"][0])
            ),
            "outside the selected source range": lambda plan: plan["beats"][0][
                "selection"
            ]["evidence"][0].update(start_seconds=40, end_seconds=41),
            "selection end must be after start": lambda plan: plan["beats"][0][
                "selection"
            ].update(source_end_seconds=1.0),
            "duration_range requires min and max": lambda plan: plan[
                "delivery_promises"
            ][0]["check"].pop("max"),
            "max between 0 and 1": lambda plan: plan["delivery_promises"][2][
                "check"
            ].update(max=1.5),
            "generation_ref requires source_kind generate": lambda plan: plan["beats"][
                0
            ].update(generation_ref={"job_path": "j.json", "receipt_path": None}),
            "must not set min or max": lambda plan: plan["delivery_promises"][1][
                "check"
            ].update(min=1),
        }
        for message, mutate in cases.items():
            with self.subTest(message):
                plan = production_plan()
                mutate(plan)
                self.assertTrue(
                    any(message in error for error in errors(plan)), errors(plan)
                )

    def test_production_state_rules(self) -> None:
        data = load("skills/creative-craft/templates/video-production.json")
        self.assertEqual([], errors(data))
        capped = copy.deepcopy(data)
        capped["policy"]["budget"]["mode"] = "cap"
        self.assertIn("budget mode cap requires a numeric cap", errors(capped))
        reordered = copy.deepcopy(data)
        reordered["stages"].reverse()
        self.assertTrue(any("in order" in error for error in errors(reordered)))


class VideoGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "prod"
        self.r = str(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cli(self, *argv: str, code: int = 0) -> str:
        actual, out, err = run_cli(*argv[:1], "--root", self.r, *argv[1:])
        self.assertEqual(code, actual, out + err)
        return out + err

    def via_root(self, *argv: str) -> str:
        # Adapts helpers that pass ("cmd", "--root", root, ...) to self.cli.
        return self.cli(argv[0], *argv[3:])

    def test_skip_requires_order_bound_plan_and_no_drift(self) -> None:
        self.init("--approval-required", "none")
        out = self.cli("video-skip", "--stage", "reference", "--reason", "n/a", code=1)
        self.assertIn("preceding stage brief is not completed or skipped", out)
        self.cli("video-skip", "--stage", "brief", "--reason", "brief given in chat")
        self.cli("video-skip", "--stage", "reference", "--reason", "no reference")
        write_doc(self.root, "plan.json", production_plan())
        self.cli(
            "video-record", "--stage", "plan", "--kind", "production-plan",
            "--artifact", "plan.json",
        )
        out = self.cli("video-skip", "--stage", "select", "--reason", "n/a", code=1)
        self.assertIn("preceding stage plan is not completed or skipped", out)
        (self.root / "plan.json").write_text("{}", encoding="utf-8")
        out = self.cli("video-skip", "--stage", "plan", "--reason", "n/a", code=1)
        self.assertIn("artifact drift: plan.json is modified", out)

    def init(self, *extra: str) -> None:
        self.cli("video-init", "--production-id", "gates", *extra)

    def plan_ready(
        self, plan: dict | None = None, *, approve: bool = False, init: tuple = ()
    ) -> None:
        self.init(*([] if approve else ["--approval-required", "none"]), *init)
        self.cli("video-skip", "--stage", "brief", "--reason", "brief given in chat")
        self.cli("video-skip", "--stage", "reference", "--reason", "no references")
        write_doc(self.root, "plan.json", plan or production_plan())
        self.cli(
            "video-record",
            "--stage",
            "plan",
            "--kind",
            "production-plan",
            "--artifact",
            "plan.json",
        )

    def assembled(self, *init: str) -> str:
        self.plan_ready(init=init)
        self.cli("video-complete", "--stage", "plan")
        self.cli("video-complete", "--stage", "select")
        self.cli("video-skip", "--stage", "generate", "--reason", "footage only")
        sha = write_doc(self.root, "rev/000001.json", edit_document(1))
        self.cli(
            "video-record",
            "--stage",
            "assemble",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000001.json",
        )
        self.cli("video-complete", "--stage", "assemble")
        return sha

    def inspect(self, rel: str, qa: dict, code: int = 0) -> str:
        write_doc(self.root, rel, qa)
        self.cli(
            "video-record",
            "--stage",
            "inspect",
            "--kind",
            "render-qa",
            "--artifact",
            rel,
        )
        return self.cli("video-complete", "--stage", "inspect", code=code)

    def test_init_refuses_existing_production(self) -> None:
        self.init()
        self.cli("video-init", "--production-id", "again", code=1)

    def test_predecessors_block_later_stages(self) -> None:
        self.init()
        out = self.cli("video-complete", "--stage", "select", code=1)
        self.assertIn("preceding stage brief is not completed or skipped", out)
        self.assertEqual("blocked", stage(self.root, "select")["status"])
        self.cli("video-complete", "--stage", "brief", code=1)  # no artifact recorded

    def test_plan_awaits_approval_then_completes(self) -> None:
        self.plan_ready(approve=True)
        self.assertIn(
            "awaiting_approval", self.cli("video-complete", "--stage", "plan")
        )
        self.cli("video-complete", "--stage", "select", code=1)
        self.cli("video-approve", "--stage", "select", "--by", "x", code=1)
        self.cli("video-approve", "--stage", "plan", "--by", "producer")
        plan_stage = stage(self.root, "plan")
        self.assertEqual("completed", plan_stage["status"])
        self.assertEqual("producer", plan_stage["approval"]["by"])

    def test_select_blocks_tbd_and_shows_candidates(self) -> None:
        plan = production_plan()
        plan["beats"].append(
            {**plan["beats"][0], "id": "open", "source_kind": "tbd", "selection": None}
        )
        self.plan_ready(plan)
        self.cli("video-complete", "--stage", "plan")
        self.assertIn(
            "beat open source is still tbd",
            self.cli("video-complete", "--stage", "select", code=1),
        )
        self.cli("video-skip", "--stage", "select", "--reason", "x", code=1)
        approved = (self.root / "plan.json").read_bytes()
        write_doc(self.root, "plan.json", production_plan())
        out = self.cli(
            "video-record", "--stage", "select", "--kind", "production-plan",
            "--artifact", "plan.json", code=1,
        )
        self.assertIn("bound by completed stage plan and must stay unchanged", out)
        (self.root / "plan.json").write_bytes(approved)
        write_doc(self.root, "plan-select.json", production_plan())
        self.cli(
            "video-record", "--stage", "select", "--kind", "production-plan",
            "--artifact", "plan-select.json",
        )
        # Dropping the tbd beat changes the approved structure: needs approval.
        out = self.cli("video-complete", "--stage", "select")
        self.assertIn("awaiting_approval", out)
        status = json.loads(self.cli("video-status", "--json"))
        select = next(s for s in status["stages"] if s["id"] == "select")
        self.assertIn("added, removed or reordered", " ".join(select["gate"]["plan_changes"]))
        self.cli("video-approve", "--stage", "select", "--by", "editor", "--note", "drop open beat")
        # The select-approved plan is now the baseline and is itself immutable.
        approved_select = (self.root / "plan-select.json").read_bytes()
        changed = production_plan()
        changed["delivery_promises"] = []
        write_doc(self.root, "plan-select.json", changed)
        out = self.cli(
            "video-record", "--stage", "generate", "--kind", "production-plan",
            "--artifact", "plan-select.json", code=1,
        )
        self.assertIn("bound by completed stage select", out)
        (self.root / "plan-select.json").write_bytes(approved_select)
        status = json.loads(self.cli("video-status", "--json"))
        generate = next(s for s in status["stages"] if s["id"] == "generate")
        self.assertNotIn("plan_changes", generate["gate"])
        # A structural change cannot be skipped past.
        write_doc(self.root, "plan-generate.json", changed)
        self.cli(
            "video-record", "--stage", "generate", "--kind", "production-plan",
            "--artifact", "plan-generate.json",
        )
        out = self.cli("video-skip", "--stage", "generate", "--reason", "none", code=1)
        self.assertIn("delivery_promises changed", out)
        write_doc(self.root, "plan-generate2.json", production_plan())
        self.cli(
            "video-record", "--stage", "generate", "--kind", "production-plan",
            "--artifact", "plan-generate2.json",
        )
        self.cli("video-skip", "--stage", "generate", "--reason", "no generated beats")
        status = json.loads(self.cli("video-status", "--json"))
        self.assertEqual(["broll"], status["candidates"])
        self.assertEqual("assemble", status["current_stage"])

    def test_generate_requires_bound_job_and_receipt(self) -> None:
        self.plan_ready(production_plan(extra_beats=[generate_beat()]))
        self.cli("video-complete", "--stage", "plan")
        self.cli("video-complete", "--stage", "select")
        self.cli("video-skip", "--stage", "generate", "--reason", "later", code=1)
        out = self.cli("video-complete", "--stage", "generate", code=1)
        self.assertIn("is not bound as video-job", out)
        write_generation(self.root, outcome="failed")
        self.cli(
            "video-record",
            "--stage",
            "generate",
            "--kind",
            "video-job",
            "--artifact",
            "jobs/gen-job.json",
        )
        self.cli(
            "video-record",
            "--stage",
            "generate",
            "--kind",
            "execution-receipt",
            "--artifact",
            "jobs/gen-receipt.json",
        )
        self.assertIn(
            "receipt outcome is failed",
            self.cli("video-complete", "--stage", "generate", code=1),
        )
        write_generation(self.root)
        self.cli(
            "video-record",
            "--stage",
            "generate",
            "--kind",
            "execution-receipt",
            "--artifact",
            "jobs/gen-receipt.json",
        )
        self.cli("video-complete", "--stage", "generate")

    def test_generate_completes_without_generate_beats(self) -> None:
        self.plan_ready()
        self.cli("video-complete", "--stage", "plan")
        self.cli("video-complete", "--stage", "select")
        self.cli("video-complete", "--stage", "generate")

    def test_record_rejects_unsafe_and_invalid_artifacts(self) -> None:
        self.init()
        outside = Path(self.tmp.name) / "outside.md"
        outside.write_text("x", encoding="utf-8")
        for value in ("../outside.md", str(outside)):
            self.cli(
                "video-record",
                "--stage",
                "brief",
                "--kind",
                "brief",
                "--artifact",
                value,
                code=1,
            )
        os.symlink(outside, self.root / "link.md")
        self.cli(
            "video-record",
            "--stage",
            "brief",
            "--kind",
            "brief",
            "--artifact",
            "link.md",
            code=1,
        )
        write_doc(self.root, "bad.json", {**production_plan(), "beats": []})
        self.cli(
            "video-record",
            "--stage",
            "plan",
            "--kind",
            "production-plan",
            "--artifact",
            "bad.json",
            code=1,
        )
        self.cli(
            "video-record",
            "--stage",
            "brief",
            "--kind",
            "edit-document",
            "--artifact",
            "bad.json",
            code=1,
        )
        self.cli(
            "video-record",
            "--stage",
            "brief",
            "--kind",
            "note",
            "--artifact",
            "production.json",
            code=1,
        )
        self.assertEqual(
            [],
            stage(self.root, "brief")["artifacts"]
            + stage(self.root, "plan")["artifacts"],
        )

    def test_drift_is_reported_and_blocks_completion(self) -> None:
        self.plan_ready()
        plan = production_plan()
        plan["title"] = "edited out of band"
        write_json(self.root / "plan.json", plan)
        status = self.cli("video-status", code=1)
        self.assertIn("DRIFT: plan.json", status)
        self.assertIn(
            "artifact drift: plan.json is modified",
            self.cli("video-complete", "--stage", "plan", code=1),
        )
        (self.root / "plan.json").unlink()
        self.assertEqual(
            "missing",
            json.loads(self.cli("video-status", "--json", code=1))["drift"][0]["state"],
        )

    def test_inspect_requires_current_revision_digest_and_review(self) -> None:
        sha = self.assembled()
        doc = edit_document(1)
        out = self.inspect("qa/stale.json", render_qa(doc, "0" * 64), code=1)
        self.assertIn("is not bound to current revision", out)
        out = self.inspect(
            "qa/pending.json", render_qa(doc, sha, review_status="pending"), code=1
        )
        self.assertIn("review is pending", out)
        self.inspect(
            "qa/fail.json", render_qa(doc, sha, decision="accept", status="fail")
        )
        self.assertEqual("in_progress", stage(self.root, "revise")["status"])
        self.assertEqual(
            "revise", json.loads(self.cli("video-status", "--json"))["current_stage"]
        )
        self.cli("video-complete", "--stage", "export", code=1)

    def test_accept_skips_revise_and_export_checks_revision_and_promises(self) -> None:
        sha = self.assembled()
        doc = edit_document(1)
        self.inspect(
            "qa/r1.json", render_qa(doc, sha, decision="accept", status="warn")
        )
        self.assertEqual("skipped", stage(self.root, "revise")["status"])
        self.cli(
            "video-record",
            "--stage",
            "revise",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000001.json",
            code=1,
        )
        other = write_doc(self.root, "rev/other.json", edit_document(2, sha))
        self.assertNotEqual(sha, other)
        self.cli(
            "video-record",
            "--stage",
            "export",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/other.json",
        )
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertIn("differs from the last accepted inspection", out)
        self.cli(
            "video-record",
            "--stage",
            "export",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000001.json",
        )
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertIn("record the delivered media file", out)
        record_export_render(self.root, doc, sha, self.via_root, kind="preview")
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertIn("must inspect an export render, not a preview", out)
        record_export_render(self.root, doc, sha, self.via_root)
        (self.root / "renders/other.bin").write_bytes(b"not the inspected render")
        self.cli(
            "video-record",
            "--stage",
            "export",
            "--kind",
            "media",
            "--artifact",
            "renders/other.bin",
        )
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertIn("is not the render inspected by export render-qa", out)
        record_export_render(self.root, doc, sha, self.via_root)
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertIn("delivery promise length failed: observed 20.0", out)

    def test_revise_round_limit_blocks(self) -> None:
        sha1 = self.assembled()
        data = production(self.root)
        data["policy"]["max_revision_rounds"] = 1
        write_json(self.root / "production.json", data)
        self.inspect("qa/r1.json", render_qa(edit_document(1), sha1, decision="revise"))
        self.cli("video-complete", "--stage", "revise", code=1)  # nothing recorded yet
        doc2 = edit_document(2, sha1)
        sha2 = write_doc(self.root, "rev/000002.json", doc2)
        self.cli(
            "video-record",
            "--stage",
            "revise",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000001.json",
            code=1,
        )  # not newer than current revision
        self.cli(
            "video-record",
            "--stage",
            "revise",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000002.json",
        )
        self.cli("video-complete", "--stage", "revise")
        self.assertEqual(1, production(self.root)["revision_rounds"])
        self.assertEqual("pending", stage(self.root, "inspect")["status"])
        out = self.inspect(
            "qa/r2.json", render_qa(doc2, sha2, decision="reject"), code=1
        )
        self.assertIn("round limit 1 is reached", out)
        self.assertEqual("blocked", stage(self.root, "revise")["status"])
        sha3 = write_doc(self.root, "rev/000003.json", edit_document(3, sha2))
        self.assertTrue(sha3)
        self.cli(
            "video-record",
            "--stage",
            "revise",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000003.json",
        )
        self.assertIn(
            "revision round limit 1 reached",
            self.cli("video-complete", "--stage", "revise", code=1),
        )
        status = json.loads(self.cli("video-status", "--json"))
        self.assertIn("video-extend-rounds", status["next_action"])
        self.cli("video-extend-rounds", "--by", "lead", "--reason", "x", "--rounds", "4", code=1)
        out = self.cli(
            "video-extend-rounds", "--by", "lead", "--reason", "client asked for one more pass"
        )
        self.assertIn("round limit 1 -> 2 by lead", out)
        data = production(self.root)
        self.assertEqual(2, data["policy"]["max_revision_rounds"])
        self.assertEqual(("revise", "extend-rounds"), (data["events"][-1]["stage"], data["events"][-1]["action"]))
        self.cli("video-complete", "--stage", "revise")
        self.assertEqual(2, production(self.root)["revision_rounds"])
        self.cli("video-extend-rounds", "--by", "lead", "--reason", "again", code=1)

    def test_rebinding_an_approved_plan_ignores_superseded_drafts(self) -> None:
        self.init("--approval-required", "none")
        self.cli("video-skip", "--stage", "brief", "--reason", "chat brief")
        self.cli("video-skip", "--stage", "reference", "--reason", "none")
        draft = production_plan()
        draft["title"] = "first draft"
        write_doc(self.root, "plan.json", draft)
        self.cli("video-record", "--stage", "plan", "--kind", "production-plan", "--artifact", "plan.json")
        write_doc(self.root, "plan.json", production_plan())
        self.cli("video-record", "--stage", "plan", "--kind", "production-plan", "--artifact", "plan.json")
        self.cli("video-complete", "--stage", "plan")
        self.cli("video-record", "--stage", "select", "--kind", "production-plan", "--artifact", "plan.json")
        write_doc(self.root, "plan.json", draft)
        out = self.cli(
            "video-record", "--stage", "select", "--kind", "production-plan",
            "--artifact", "plan.json", code=1,
        )
        self.assertIn("bound by completed stage plan", out)

    def test_extend_rounds_requires_a_limit_block(self) -> None:
        self.assembled()
        out = self.cli("video-extend-rounds", "--by", "lead", "--reason", "early", code=1)
        self.assertIn("not blocked by the revision-round limit", out)

    def test_plan_structure_changes(self) -> None:
        base = production_plan()
        base["beats"].append({**base["beats"][0], "id": "open", "source_kind": "tbd", "selection": None})
        same = copy.deepcopy(base)
        same["beats"][0]["selection"] = None
        same["beats"][-1]["source_kind"] = "footage"
        self.assertEqual([], plan_structure_changes(base, same))
        moved = copy.deepcopy(base)
        moved["beats"][0]["duration_seconds"] += 1
        moved["delivery_promises"] = []
        self.assertEqual(
            [f"beat {base['beats'][0]['id']} duration_seconds changed", "delivery_promises changed"],
            plan_structure_changes(base, moved),
        )
        locked = copy.deepcopy(base)
        locked["beats"][0]["locked"] = True
        relocked = copy.deepcopy(locked)
        relocked["beats"][0]["selection"] = None
        self.assertIn(
            f"locked beat {base['beats'][0]['id']} selection changed",
            plan_structure_changes(locked, relocked),
        )

    def test_unskippable_stages(self) -> None:
        self.init()
        for stage_id in ("assemble", "inspect", "revise", "export"):
            self.cli("video-skip", "--stage", stage_id, "--reason", "x", code=1)

    def test_budget_ledger(self) -> None:
        self.init("--budget-mode", "cap", "--budget-cap", "10")
        self.cli(
            "video-ledger",
            "reserve",
            "--id",
            "g1",
            "--stage",
            "generate",
            "--description",
            "shot",
            "--estimate",
            "6",
            "--provider-job-id",
            "job-1",
        )
        self.cli(
            "video-ledger",
            "reserve",
            "--id",
            "g2",
            "--stage",
            "generate",
            "--description",
            "retry",
            "--estimate",
            "1",
            code=1,
        )  # unknown outcome of job-1
        self.cli(
            "video-ledger",
            "reserve",
            "--id",
            "a1",
            "--stage",
            "assemble",
            "--description",
            "render",
            "--estimate",
            "5",
            code=1,
        )  # over cap
        self.cli("video-ledger", "settle", "--id", "g1", "--actual", "4")
        self.cli("video-ledger", "settle", "--id", "g1", "--actual", "4", code=1)
        self.cli(
            "video-ledger",
            "reserve",
            "--id",
            "a1",
            "--stage",
            "assemble",
            "--description",
            "render",
            "--estimate",
            "5",
        )
        self.cli("video-ledger", "release", "--id", "a1")
        budget = json.loads(self.cli("video-status", "--json"))["budget"]
        self.assertEqual(
            (0, 4, 4), (budget["reserved"], budget["settled"], budget["committed"])
        )
        self.assertTrue(all(event["at"] for event in production(self.root)["events"]))

    def test_export_human_review_policy_blocks_agent_accepted_inspection(self) -> None:
        sha = self.assembled("--export-requires-human-review")
        self.assertIs(True, production(self.root)["policy"]["export_requires_human_review"])
        doc = edit_document(1)
        self.inspect("qa/r1.json", render_qa(doc, sha, decision="accept"))
        self.cli(
            "video-record",
            "--stage",
            "export",
            "--kind",
            "edit-document",
            "--artifact",
            "rev/000001.json",
        )
        record_export_render(self.root, doc, sha, self.via_root)
        # An agent-written reviewer_kind is not a sign-off; inspect waits for one.
        self.assertEqual("awaiting_approval", stage(self.root, "inspect")["status"])
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertIn("preceding stage inspect is not completed", out)
        self.cli("video-approve", "--stage", "inspect", "--by", "reviewer")
        self.assertEqual("reviewer", stage(self.root, "inspect")["approval"]["by"])
        out = self.cli("video-complete", "--stage", "export", code=1)
        self.assertNotIn("policy.export_requires_human_review", out)
        self.assertIn("delivery promise", out)

    def test_record_on_awaiting_stage_says_it_reopened_and_approve_names_next_step(
        self,
    ) -> None:
        sha = self.assembled("--export-requires-human-review")
        doc = edit_document(1)
        self.inspect("qa/r1.json", render_qa(doc, sha, decision="accept"))
        self.assertEqual("awaiting_approval", stage(self.root, "inspect")["status"])
        write_doc(self.root, "notes/rights.md", {"note": "rights confirmed"})
        out = self.cli(
            "video-record", "--stage", "inspect", "--kind", "note",
            "--artifact", "notes/rights.md",
        )
        self.assertIn(
            "Stage inspect was awaiting_approval and is reopened to in_progress; "
            "run video-complete --stage inspect again before video-approve.",
            out,
        )
        self.assertEqual("in_progress", stage(self.root, "inspect")["status"])
        out = self.cli("video-approve", "--stage", "inspect", "--by", "r", code=1)
        self.assertIn(
            "stage inspect is in_progress, not awaiting_approval; "
            "run video-complete --stage inspect first",
            out,
        )
        # A stage never completed is told to complete, not that a record reopened it.
        out = self.cli("video-approve", "--stage", "export", "--by", "r", code=1)
        self.assertIn(
            "not awaiting_approval; record its artifacts (video-record --stage export)",
            out,
        )
        self.assertNotIn("reopens", out)
        # A record on a stage already in progress adds no reopen line.
        write_doc(self.root, "notes/more.md", {"note": "more"})
        out = self.cli(
            "video-record", "--stage", "inspect", "--kind", "note",
            "--artifact", "notes/more.md",
        )
        self.assertNotIn("reopened", out)
        self.cli("video-complete", "--stage", "inspect")
        self.cli("video-approve", "--stage", "inspect", "--by", "r")
        self.assertEqual("completed", stage(self.root, "inspect")["status"])
        # A completed stage cannot be approved again and gets no video-complete hint.
        out = self.cli("video-approve", "--stage", "inspect", "--by", "r", code=1)
        self.assertIn("stage inspect is completed, not awaiting_approval", out)
        self.assertNotIn("video-complete", out)

    def test_human_review_policy_rejects_unsigned_completed_inspect(self) -> None:
        sha = self.assembled("--export-requires-human-review")
        self.inspect("qa/r1.json", render_qa(edit_document(1), sha, decision="accept"))
        data = production(self.root)
        insp = next(s for s in data["stages"] if s["id"] == "inspect")
        insp.update(status="completed", approval=None)
        self.assertTrue(
            any("completed without its required approval" in e for e in errors(data))
        )

    def test_export_human_review_policy_defaults_off(self) -> None:
        self.init()
        self.assertNotIn("export_requires_human_review", production(self.root)["policy"])


class VideoEndToEndTests(unittest.TestCase):
    def test_human_review_policy_exports_after_human_accepted_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_talking_head_production(root, human_review=True)
            data = production(root)
            self.assertIs(True, data["policy"]["export_requires_human_review"])
            self.assertEqual("completed", stage(root, "export")["status"])

    def test_talking_head_broll_captions_with_one_revision_round(self) -> None:
        for generated in (False, True):
            with (
                self.subTest(generated=generated),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp)
                digests = build_talking_head_production(root, generated=generated)
                data = production(root)
                self.assertTrue(
                    all(
                        item["status"] in {"completed", "skipped"}
                        for item in data["stages"]
                    )
                )
                self.assertEqual(
                    (1, 2), (data["revision_rounds"], data["current_revision"])
                )
                exported = stage(root, "export")["artifacts"][-1]
                self.assertEqual(digests["doc2"], exported["sha256"])
                code, out, _ = run_cli("video-status", "--root", tmp, "--json")
                self.assertEqual(0, code)
                status = json.loads(out)
                self.assertEqual([], status["drift"])
                promises = {
                    item["id"]: item
                    for item in status["delivery_promises_on_current_revision"]
                }
                self.assertEqual(15.0, promises["length"]["observed"])
                self.assertIsNone(promises["tone"]["passed"])
                share = promises["generated"]["observed"]
                self.assertEqual(0.2 if generated else 0.0, share)
                actions = [
                    (event["stage"], event["action"]) for event in data["events"]
                ]
                self.assertIn(("revise", "complete"), actions)
                self.assertIn(("inspect", "reopen"), actions)


class VideoExampleTests(unittest.TestCase):
    def test_example_production_has_no_drift_and_is_exported(self) -> None:
        root = ROOT / "examples/talking-head-broll-cut"
        code, out, err = run_cli("video-status", "--root", str(root), "--json")
        self.assertEqual(0, code, err)
        status = json.loads(out)
        self.assertIsNone(status["current_stage"])
        self.assertEqual([], status["drift"])


if __name__ == "__main__":
    unittest.main()
