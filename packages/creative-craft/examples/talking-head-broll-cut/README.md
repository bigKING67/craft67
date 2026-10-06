# Talking head + B-roll cut (synthetic)

A traceable Video Harness v1 production: plan → select → assemble → inspect
(revise) → revise → inspect (accept) → export. `generate` is skipped because every
beat uses existing footage; `reference` is skipped with a recorded reason.

**All data is synthetic.** Media digests in the edit revisions are placeholders, no
render was produced, and both `qa/*.json` files are fabricated render-qa records
that are not real render or review evidence. `renders/r2-export.synthetic` is a placeholder for the
delivered file; `qa/r2-export.json` binds it to the export gate. The example shows the contracts,
digest bindings and gate decisions only.

```bash
python3 skills/creative-craft/scripts/creative_craft.py video-status \
  --root examples/talking-head-broll-cut
```

`tests/video_support.py` regenerates an equivalent production through the CLI.
