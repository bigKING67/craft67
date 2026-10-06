# Changelog

All notable changes are documented here.

## Unreleased — Video Harness v1

Gated video production on top of the existing contracts (see
`docs/content-production-architecture.md#video-harness-v1`):

- shared `edit-document.v2` (multi-track, engine-independent edit truth) and
  `render-qa.v1` contracts, with cross-language semantic fixtures enforcing that
  the Node and Python validators agree;
- `production-plan.v1` and `video-production.v1` with `video-*` CLI stage gates:
  approval, footage evidence, bound generation Job/Receipt, render-qa bound to the
  current revision, revision-round limit with an explicit human extension, export
  bound to the delivered file and its export render-qa, delivery promises computed
  on the exported revision, approved-plan protection, and a reserve-then-settle
  budget ledger;
- optional `integrations/local-production` 0.2.0: v2 edit batches (11 operations,
  dry-run, stale-revision rejection, locked tracks, single-batch lock changes),
  v1 migration, multi-track compilation, HyperFrames lint gate, ffmpeg-based QA
  with composited samples; HyperFrames pinned to 0.8.108; the caption font binary
  is fetched and digest-checked instead of committed;
- `docs/upstream-watch.json` and `make upstream-check` for read-only upstream drift
  review.
- P2 packaging and audio (local-production 0.3.0): constant speed changes,
  fades, crossfades, music ducking under a reference track, `lower-third` and
  `title-card` graphic templates with typed variables, edit-time checks of the
  512-point volume automation limit, limiter evidence (`audioLoweredDb`) and
  caption/graphic safe-area checks in QA;
- optional `policy.export_requires_human_review`: an accepted inspection waits
  for a named `video-approve --stage inspect` sign-off. The local CLI records who
  signed; verifying that the signer is a person is left to the host.
- P2.1 from real-footage validation (local-production 0.4.0): burned-caption
  cut-point check (light subtitles; frame-difference heuristic, not OCR), at least
  one QA sample per shot, named template placements with a minimum text size of 3%
  of the short edge, render receipts naming template id/version/digest, and a
  local whisper.cpp `transcribe` command with a pinned, digest-checked model and
  automatic clean-audio retry.
- graphic templates pinned to edit revisions (local-production 0.5.0): optional
  `graphic_templates` bindings to content-addressed, normalized template bytes in
  the project; renders load only pinned bytes, `rebind_template` is an explicit
  upgrade, `revert_to` restores the target's bindings, and locked tracks keep
  their template bytes. Unpinned historical revisions render with runtime
  templates and are marked `pinned: false`.
- second real-footage run fixes (local-production 0.5.1): ASR `phrases` split
  dense whisper segments at punctuation using token timestamps; QA samples are
  extracted frame-exactly; burned-caption suggestions and all reported times use
  frame midpoints; frame times come from integer pts and stream time base; new
  `cut-boundary-fragments` check flags previous-shot fragments and transition
  flashes at cut points, while short shots shown whole stay aligned.
- source frame alignment (local-production 0.6.0): v2 imports record an exact
  `frame_rate` for constant-frame-rate video whose own stream starts at 0; at
  compile time a video-track in-point truncated to just below a frame start
  (≤ 2 ms and < 0.1 frame, e.g. 24.4333 or 24.433 at 30 fps) is moved to that
  frame start + 0.1 ms, other in-points are untouched; render, captions and QA
  share one compiled view. QA suggestions are relative to the written value.
- render size and media time zero (local-production 0.7.0): captures below 88 px
  high stall in the Chrome capture viewport regardless of codec (width is not
  limiting down to 2 px); outputs below the limit are now captured at the
  smallest integer multiple and scaled back with ffmpeg, so every valid canvas
  renders and exports at its own size (receipt `capture`). A measured, sequential
  support matrix (H.264/HEVC 8/10-bit, HLG, VFR, rotation, VP9/WebM, MKV and
  common audio codecs all render, also at 128x72) replaces the earlier wrong
  codec conclusion. `frame_rate` is recorded only when the video stream starts at
  the media time zero (the earliest stream start; measured for MKV and MP4 edit
  lists); loading a project re-checks it once (the decision is bound to the
  loaded document and used by every compilation of it, carried by edits) so
  stale values from 0.6.0 projects are not applied (receipt `frame_alignment`;
  QA compiles with the receipt's, or all applied for older receipts, and checks
  resolution against the receipt's output size). Previews are never captured
  larger than their export, captures are capped at the measured 7680 px, and the
  scale-back uses fixed CRF 18 and cleans up after failure or cancellation.
  Browser captures within one process now run one at a time (concurrent captures
  were measured to corrupt each other); a render cancelled while waiting for the
  capture returns `cancelled` at once.
- cut tools and cut audio (local-production 0.8.0): `analyze` writes a footage
  report (frame-exact shots, ASR phrases split at punctuation, spaces and long
  pauses, 20 ms energy, burned-caption changes, R128 loudness); `suggest-cuts`
  snaps rough beats to complete phrases, energy valleys, caption changes and shot
  boundaries at frame midpoints, suggests volumes and an items draft, and marks
  conflicts `needs_decision` instead of choosing silently. On two real client
  films all eight in-points matched hand-finalized values within one frame. Hard
  audio cuts get 4 ms de-click fades, except at a split join (same track, same
  asset, volume and speed, back to back, source continuous within one source
  frame), where the waveform runs on. Crossfades are equal-gain only when both
  sides play the same source samples over the overlap, otherwise equal-power
  (including one asset at different source times). QA adds a `cut-point-clicks`
  check; a failed or timed-out decode, or a cut past the end of the audio, makes
  it `unknown`. Analysis times (phrases, energy, loudness) are all media time:
  ASR/transcript phrase times are shifted by the audio stream's start offset.
  **Behavior change and migration:** re-rendering an already published revision
  adds the 4 ms fade at its hard audio cuts, so its audio is not byte-identical
  to a 0.7.0 render (picture unchanged; no document change needed). A volume
  lane that would exceed 512 automation points with the de-click is compiled
  without it instead of failing; such lanes are listed as
  `declick.skipped_lanes` in the compile result, the render receipt and (when
  any) the edit result. A lane over 512 points even without it is still refused.
- review page (local-production 0.9.0): `qa` also writes `review.html`, a
  single-file offline page for the human reviewer. All CSS and JS are inline, and
  a `default-src 'none'` CSP allows them only by hash. The page shows:
  - the review decision first, with the automated verdict secondary;
  - the finished film, with "jump to" buttons for every review finding and
    automated warning or failure;
  - before/after clips and samples at each cut point, and the contact sheet;
  - all checks, the `video-approve` sign-off commands and the unverified list.

  `review-page QA_DIR [--video] [--production]` regenerates the page after the
  review is written into `qa.json`. It atomically replaces only `review.html`;
  the evidence files are never rewritten. The page records the `qa.json`
  SHA-256 and the generator version, and checks the film's SHA-256 against
  `qa.json`. Older or partial `qa.json` files render explicit empty states. The
  `qa.json` schema is unchanged. Verified in a real browser:
  - jumps land within 3 ms;
  - keyboard focus works, including the native player controls;
  - light and dark themes both render;
  - a 390 px layout has no overflow.
- review page polish (local-production 0.9.1):
  - Cut-point clips have one play/pause/replay button instead of native
    controls: one tab stop per clip instead of about four. Starting any video
    pauses the others.
  - A jump made before the film has loaded (browsers can defer media in
    background tabs) announces "loading, will seek to …". The last jump is
    applied once metadata arrives, and a load error is announced.
  - The video reference asks for review findings in the signer's language,
    with output times; a source time must be labelled as source time.
- fixes from the first end-to-end real-footage run (local-production 0.10.0):
  - **Out-point caption cascade.** An out-point aligned on a caption change is
    no longer moved by a further change within 0.5 s before it. Before, that
    change could be the switch to the line still being spoken, and the move
    cut the last words. The QA burned-caption check does the same for both
    edges when the edge frame is a caption change: such a point is `aligned`
    with `short_line` instead of `warn`. suggest-cuts reports it in
    `evidence.out.closing_caption`. An edge on a source shot change still
    warns, marked `edge_on_shot_change`: the frame difference cannot tell a
    new line starting with the cut from the previous line running on, so the
    reviewer checks it by eye.
  - **Dips to black.** `analyze` detects gradual dips to black (`dips`), which
    the shot detector misses.
    - suggest-cuts moves an edge out of a dip when that cuts ≤ 0.25 s of
      speech; otherwise it keeps the edge and reports it.
    - QA `cut-boundary-fragments` warns when an edge lands inside a dip.
    - Any moved in-point left < 0.05 s before the speech onset is reported, so
      a reviewer listens to the first syllable.
  - **`apply-cuts`.** The new `apply-cuts CUTS.json NEW_OUT.json [--choose BEAT.EDGE=OPTION]`
    applies the chosen decisions and recomputes back-to-back frames. It emits
    v2 items and production-plan beats with ASR evidence. Plan beat problems
    are reported as `plan_status`/`plan_errors` without losing the items. It
    refuses choices it cannot apply safely: a beat with no usable range, or
    an in option other than the draft's when the out edge depends on it. suggest-cuts passes
    optional role/purpose/requirement/hard_constraints through from BEATS.json.
  - **`qa --production`.** The review page it writes then carries the real
    sign-off command.
  - **Review page.**
    - The headline separates agent review from human sign-off. "人工已签字"
      needs `production.json`: an approved inspect stage whose latest
      render-qa is this qa.json. An export render-qa, checked after the
      sign-off, shows "导出检查：签字人未审看本文件". Otherwise the headline reads "等待人工签字", or gives
      the reason the signature does not cover this qa.json.
    - Checks show Chinese summaries built from `measured`, with the English
      original folded.
    - The reviewer is labelled once.
  - **`video-record` / `video-approve`.** They say when recording an artifact
    reopened a stage awaiting approval. The approve hint follows the stage
    status: run `video-complete` again, complete the stage first, or resolve
    its blockers.
  - **Dips at file edges.** A fade-up at the start or fade-out at the end of
    the source counts as a dip only when it gets near black, since no light
    returns on that side.
  - Real-footage regression (byq-cushion-05) with no hand edits:
    - the hook out-point lands after "无滤镜" (frame 1803) with no decision;
    - the only dip in the 157.6 s film is found and the wear in-point leaves it;
    - the caption check keeps one warn, on the test in-point, which sits on a
      source shot change. Checked by eye, it is the new line starting with the
      cut.
- caption/speech sync (local-production 0.11.0):
  - **New QA check `caption-speech-sync`, run with `qa --analysis ANALYSIS.json`.**
    It looks for an in-point that opens on a burned caption line belonging to
    speech before the cut. It compares outlined caption strokes in the first
    shown frame with a frame inside the last earlier speech, within 1 s. It
    warns when both frames hold text and ≥ 80 % of the cut frame's strokes
    are already there.
    - It compares the caption band directly, without relying on detected
      caption-change times. Those times were too unreliable: changes during
      motion and fades are missed.
    - Calibration on 5 real films: about 5 in 6 warns are right at ≥ 0.8.
    - On byq-cushion-05 it flags only the texture in-point ("你看" still on
      screen under "哇哦").
    - `--analysis` files are matched to assets by media SHA-256. A foreign,
      duplicate or phrase-less analysis is refused.
    - The review page gives it a Chinese summary.
  - **Fix: `analyze --asr` failed on some films.** On a 160.24 s film,
    whisper.cpp got a fractional `execFile` timeout. The timeout is now an
    integer.
- apply-cuts writes the plan and spec (local-production 0.12.0):
  `--plan-template P --plan-out NEW_PLAN` fills a hand-written plan head with
  the applied beats and validates the whole plan against the schema.
  `--spec-template S --spec-out NEW_SPEC` replaces the media items on the
  applied track and keeps the other tracks. Incomplete beats, an unknown
  track or asset, or a plan that fails the schema are refused. All outputs
  are new, separate files, and nothing is written unless every output is
  valid. This replaces the hand-written merge script the first real run needed.
  The written spec passes the same checks as `create` (`prepareProject`)
  before anything is written. Outputs are written as temporary files, then
  linked into place, which never replaces an existing file. Everything is
  removed if any step fails. Refused: a locked track, an fps mismatch,
  non-media items on the replaced track, and kept items linked to replaced
  media. Kept items on other tracks that run past the new end are named in
  the notes. The plan's selection reason records `prefer` and any `--choose`.
  `BEATS.json` `prefer: "keep_speech" | "cut_at_change"` decides a beat's
  conflicts up front. Example: montage footage whose speech runs across shot
  cuts, where dropping whole phrases shrank a 4.4 s beat to 0.67 s.
- QA knows the edit decisions (local-production 0.13.0): `qa --decisions APPLIED.json`
  reads the `decisions` that apply-cuts now writes. Each decision is a
  `prefer` or `--choose` entry and records the cut rules its option accepts:
  keep_speech accepts caption, shot or dip findings.
  - A burned-caption or cut-fragment warning at the decided edge is reported
    as `accepted` instead of `warn`, provided the edge has not moved since
    and the decision accepts every rule behind the warning.
  - caption-speech-sync is never accepted this way: keeping the speech does
    not mean accepting a mismatched caption.
  - The review page shows such findings as "已接受（保留整句，BEATS.json
    事先决定）".
  - On byq-velvet-03 the two fragment warnings the plan had accepted now
    pass. The caption-speech warning remains.

The package size guard is re-measured (650,000 unpacked / 165,000 packed); the
growth is scripts and schemas that agents do not load into context. All media in
tests, smoke runs and the example is synthetic: this proves contracts and the
technical pipeline, not creative quality or production acceptance.

## 0.3.2 — unreleased candidate

Practical copy guidance and creative judgment improvements:

- separate everyday copy development from the unchanged formal Copy Sheet
  contract, keeping Quick Craft direct;
- connect supported product features to a concrete reason to choose or use,
  including desired activities rather than only storage or operation;
- add eight fictional teaching contrasts with explicit limits on user acceptance,
  and preserve expressive variety rather than prescribe a headline formula;
- explicitly route a headline plus body text through copy-development guidance;
- add repository-only Chinese diagnostic and human-feedback materials without
  including evaluation logs in the installed Skill.

One new-product first draft received user willingness to use; a backpack
headline was accepted after collaborative revision. These are bounded examples,
not evidence of stable creative improvement. Reference reading passed one
focused recheck, not a repeatability test. This candidate includes the existing
0.3.1 work below and is not a public release.

## 0.3.1 — unreleased candidate

Direction-gated refinement and Grok discovery portability:

- distinguish bounded output defects from feedback that reopens shot scale,
  subject hierarchy, visual world, narrative mechanism, or product role;
- keep unresolved high-impact choices exploratory and allow at most two
  targeted refinement passes only after direction selection and execution
  authorization;
- stop on no material improvement, reopened direction, conflicting evidence,
  or cost/authorization limits, while preserving the best prior candidate;
- clarify that generative masks are not pixel locks and route exact preservation
  to deterministic compositing, retouch, or pixel restoration with verification;
- add Grok Skill discovery documentation and an optional, no-model-call host
  smoke while keeping Codex and Pi as the only runtime-verified Tier 1 hosts;
- extend the isolated Agent quality suite with paired unlocked-direction and
  locked-direction refinement cases without increasing its 40-call ceiling;
- isolate user-level Skill discovery roots, bind observed entrypoint reads to
  the intended fixture digest before later calls, and report quality-only
  canaries as `PARTIAL` without requiring unrelated routing results.

This candidate changes Agent behavior and host discovery evidence only. It adds
no Provider adapter, real image/video Golden Eval, public release, or new
versioned artifact contract.

## 0.3.0 — 2026-08-26

Agent-first creative quality, copy authority, and modular runtime release:

- make Quick Craft the default Agent path so bounded concept, copy, image,
  video, and critique requests produce the requested artifact without mandatory
  project files, schemas, gates, or CLI work;
- isolate durable artifact graphs, lifecycle states, approval gates, pack
  snapshots, and common CLI commands in an opt-in Traceable Project reference;
- shorten the canonical Skill entrypoint, make automatic routing concrete, and
  exclude content calendars/KOL planning, brand strategy, media buying,
  product UI/UX, and software review;
- ground video product interactions in supplied evidence, require one coherent
  end-frame state, and preserve the creative premise through the closing line;
- verify hard copy constraints, remove internal decision taxonomy from quick
  critiques, and avoid repeated preservation language in compact edit briefs;
- add a maintainer-only isolated Codex A/B/C text evaluation harness with seven
  quality cases, blind weighted judging, four routing cases, a 40-call ceiling,
  auth symlink/redaction checks, and ignored content-bound evidence reports;
- add first-class `creative-craft.copy-sheet.v1` with strategy, audience
  tension, proposition, voice, proof hierarchy, mandatory/prohibited/legal
  copy, distinct copy routes, selected units, evidence refs, render method,
  approval, and unknowns;
- add `creative-craft.project-manifest.v2` with `copy_policy=required`, bind v2
  Image/Video Jobs to explicit Copy Sheets and units, and require reviewed copy
  for internal readiness plus approved public copy with a named owner for
  public delivery;
- preserve Project Manifest v1 and legacy copy-unbound projects as readable
  compatibility inputs without silently upgrading or approving them;
- replace the 5,491-line runtime entrypoint with a compatibility facade over
  domain modules for contracts, project graph, evaluation, pack transactions,
  project operations, runtime checks, and CLI parsing; split the test suite by
  the same ownership boundaries;
- replace fixed sibling temporary files with random same-directory exclusive
  files, fsync before atomic replace, reject symlink destinations/parents, and
  reject Brand/Reference write transactions through symlink Project roots;
- replace quadratic `uniqueItems` scanning with typed canonical indexing plus
  collision verification, preserving JSON Schema equality while gating the
  1,600-to-3,200 item median-time ratio at `<=2.5`;
- declare Python `>=3.10`, add Python 3.10 to the CI matrix, lint all runtime
  modules, and include the benchmark and new files in release/package gates.

This release remains GitHub-only and is not published to npm. Its public fixture
is fictional and internally reviewed only; it does not include real Provider
output, a real owner approval, private company evidence, or a Creative Golden
Eval. The repository-only text evaluation is outside CI and does not change
`real_golden_evals=false`.

## 0.2.6 — 2026-08-05

Review evidence and transaction hardening release:

- bind output and delivery Evaluation gates to a stage-compatible target and a
  matching Job, Receipt, Output, and Inspection chain instead of accepting an
  unrelated project-global Inspection;
- make `seed` a symlink-safe, same-filesystem staged-tree transaction covering
  force backups, generated Manifest content, optional Brand binding, full
  validation, commit, and exact-tree failure recovery;
- reject symlink Project roots and Manifests, and make `doctor-project` report
  unsafe top-level JSON symlinks without following snapshot trees;
- implement JSON Schema `uniqueItems` with JSON deep-equality in the portable
  runtime and add keyword-complete parity mutations for all 12 public uses;
- require timezone-bearing Receipt and approved-Inspection timestamps and
  compare their UTC-normalized values without leaking mixed-datetime errors;
- synchronize immutable Pi and Codex install snippets with `v0.2.6`, gate future
  adapter tag drift, and add repository-local Review Craft E3 commands for the
  exact packaged runtime.

This release remains GitHub-only, contains no private company content, does not
call provider networks, and does not claim real Creative Golden Evals.

## 0.2.5 — 2026-08-05

Evidence-safe seed and project diagnostics release:

- separate descriptive evidence about current or historical assets from the
  approved Brand Pack and locked project authority that govern future work;
- prevent `seed` from creating placeholder Execution Receipt, Output
  Inspection, or Revision Lineage files before the corresponding real event;
- register seeded Critique in the Project Manifest and require its target
  `asset_id` to resolve to the project Asset Ledger;
- add the read-only `doctor-project` command, distinguishing a valid manifest
  graph from a healthy project directory and reporting known unregistered
  Creative Craft artifacts;
- classify byte-identical unregistered templates as `seed_template_residue`
  without automatically registering or deleting them;
- verify that project diagnosis leaves the complete project tree unchanged and
  exercise `doctor-project` through the installed leaf runtime;
- synchronize the new lifecycle boundary across English and Chinese install and
  operating documentation.

This release remains GitHub-only, contains no private company content, does not
call provider networks, and does not claim real Creative Golden Evals.

## 0.2.4 — 2026-08-04

Reference evidence and filesystem hardening release:

- reject symlinks and project-root escapes across Brand and Reference staging,
  snapshot, binding, lineage, and retained-backup write destinations;
- remove failed-operation backups and newly created empty directories after a
  successful rollback, restoring the exact pre-operation project tree;
- require every source in a `reviewed` Reference Pack to use a non-placeholder
  URI plus a local, symlink-free source snapshot whose SHA-256 matches;
- add `creative-craft.reference-binding-history.v1` and register an immutable,
  content-bound predecessor artifact for every successful Reference update;
- resolve the complete predecessor chain during project validation and reject
  fictional, cyclic, cross-project, cross-pack, or orphan lineage records;
- reject new bindings and updates from `superseded` Reference Packs while
  preserving already-bound snapshots as historical evidence with a warning;
- expand installed leaf-runtime smoke through seed, reviewed source validation,
  bind, update, project validation, and exact-tree rollback;
- safely unpack the exact generated `.tgz` in CI and release builds, then repeat
  leaf self-test plus
  Reference bind, update, validation, and exact-tree rollback against its
  packaged runtime;
- normalize public release command receipts so local user and workspace paths
  are not written into `release-validation.json`.

This release remains GitHub-only, contains no private brand/reference content,
does not call provider networks, and does not claim real Creative Golden Evals.

## 0.2.3 — 2026-08-04

Reference intelligence portability release:

- added non-authoritative `creative-craft.reference-pack.v1` and
  `creative-craft.reference-binding.v1` contracts without adding any private
  brand, competitor, team, source, or asset data to the public package;
- added `init-reference-pack` and `validate-reference-pack` for thin private
  Reference Skills with evidence classes, source links, transferable
  principles, non-transferable elements, content digests, safe paths, and
  input-rights checks;
- added `bind-reference-pack` with `0..N` immutable project snapshots,
  selected-entity bindings, selected-asset ledger merge, and source lineage;
- added `update-reference-snapshot` with per-pack previous-binding lineage,
  scoped retained backup, complete project validation, and rollback on failure;
- enforced `may_override_primary_brand: false`, kept the existing `0..1`
  Primary Brand Pack invariant, rejected revoked references, and made draft
  references warning-only so they cannot block an otherwise Ready Job;
- added installed-runtime, package-boundary, multiple-pack, snapshot-drift,
  selection, rights, update-isolation, and rollback regression coverage.

This release intentionally does not implement Partner/co-brand authority,
contain company-specific private reference data, publish to npm, call provider
networks, or claim real Creative Golden Evals.

## 0.2.2 — 2026-08-04

Brand authority portability release:

- added generic `creative-craft.brand-pack.v1` and
  `creative-craft.brand-binding.v1` contracts without adding any private brand
  content to the public package;
- added `init-brand-pack` and `validate-brand-pack` for thin private Brand
  Skills with placeholder-only authority, content digests, safe paths, source
  review, asset rights, and consent checks;
- extended `seed` with opt-in Brand Pack binding that copies an immutable
  project snapshot, projects `BRAND.md`, merges Asset Ledger entries, and binds
  source/ref/commit plus SHA-256 identity;
- added `update-brand-snapshot` with previous-binding lineage, retained backup,
  complete project validation, and rollback on failure;
- blocked `ready` Jobs when a bound Brand Pack is not approved while preserving
  backward compatibility for unbound projects;
- added installed-runtime Brand Pack smoke coverage and regression tests for
  traversal, symlinks, digest drift, unresolved rights, snapshot drift,
  binding mismatches, updates, and rollback.

This release does not contain company-specific knowledge, real brand assets,
approved claims, provider network adapters, or real Creative Golden Evals.

## 0.2.1 — 2026-08-04

Installed-runtime verification patch:

- split repository integrity checks from canonical Skill runtime checks;
- made `self-test` automatically select repository scope in a checkout and
  runtime scope in a Pi, Codex, or generic leaf Skill installation;
- added explicit `scope`, `repository_valid`, and `runtime_valid` JSON evidence;
- made the atomic installer validate its staged leaf copy through the same
  installed-runtime self-test used after installation;
- added isolated leaf-install regression coverage and a Host smoke gate for the
  installed-runtime self-test.

## 0.2.0 — 2026-08-04

Evidence-bound production-contract release:

- added Project Manifest, Creative Direction, Image/Video Job v2, Execution
  Receipt, Output Inspection, Revision Lineage, Evaluation v2, and Delivery v2;
- made JSON Schema the public structural validation source of truth, with a
  standard-library runtime evaluator and `jsonschema` mutation parity gate;
- added safe project-relative path, SHA-256, cross-artifact reference,
  Provider/Surface, rights, and lifecycle validation;
- replaced Job-generated/approved self-declaration with evidence-derived
  `generated`, `inspected`, `revision_required`, `approved`, and `delivered`
  projections;
- split evaluation coverage from evidence strength, distribution, confidence,
  uncertainty, and project-derived gates;
- added OpenAI Image API / Responses Image Tool and ByteDance Jimeng / Doubao
  Pro Surface Profiles; ModelArk remains explicitly unavailable;
- added `validate-project`, `project-status`, `inspect-output`,
  `start-revision`, and `verify-delivery` CLI commands;
- made seed inventory registry-derived and included Critique plus a generated,
  content-bound project manifest;
- fixed `doctor --root` Provider isolation and duplicate metadata ID handling;
- replaced destructive installation with validated same-filesystem staging,
  atomic replacement, rollback, backup, and install provenance;
- documented GitHub-only distribution and Tier 1 Pi/Codex installation;
- added real GitHub CI, Schema/reference parity, host package smoke, atomic
  installer failure tests, and a v2 fictional example.

This release does not include provider network adapters or claim real image or
video Golden Evals.

## 0.1.0 — 2026-08-04

Initial public foundation:

- canonical Creative Craft skill and authority model;
- CRAFT operating loop and task modes;
- creative brief, concept, direction, asset-analysis, image, video, evaluation,
  provenance, iteration, and delivery references;
- provider-scoped profiles for OpenAI GPT Image 2 and ByteDance Seedance 2.5;
- versioned JSON artifacts and Draft 2020-12 JSON Schemas;
- GPT Image 2 single/multi-turn execution mode, output compression, and masked-edit guidance;
- standard-library CLI for doctoring, package self-testing, seeding, validation,
  prompt compilation, scoring, and hashing;
- fictional premium haircare example;
- cross-platform unit tests, full schema validation, publish-boundary smoke tests, and CI.
