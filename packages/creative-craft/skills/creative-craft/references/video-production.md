# Video production

For authorized local assembly of existing footage, a source checkout offers the
optional `integrations/local-production/` module. Read its `README.md` from the
repository root before execution: read the project, submit revision-bound edits,
render a new preview, and inspect the actual output. It supports basic cuts,
reordering, source-timed captions and audio; it is not bundled into the installed
Skill and does not call video-generation providers. Do not install or invoke it
for treatment-only requests. Check the actual host integration before claiming
that an editor or any particular operation is available.

Video production is the coordination of story, performance, blocking, camera,
motion, sound, references, continuity, and editability over time.

Read the matching dated Seedance provider profile before using current limits or
features.

## Task types

- `text_to_video`;
- `image_to_video`;
- `reference_to_video`;
- `extend_video`;
- `edit_video`.

Choose the smallest task type that preserves the best existing evidence.

## Video job fields

A production-ready job contains:

- job ID and schema version;
- intended use;
- provider, model, platform, and execution mode;
- duration, ratio, resolution target, and language;
- creative premise and end state;
- subject, scene, props, style, camera, motion, and audio references;
- reference role map;
- continuity locks;
- timestamped beats;
- performance and blocking;
- camera and transition plan;
- environment, materials, lighting, weather, and physics;
- dialogue, voice, ambience, effects, and music;
- edit changes and preserved invariants;
- exclusions and failure conditions;
- extension boundary;
- inspection checklist;
- rights and approval state.

## Prompt architecture

```text
FORMAT AND INTENDED USE
CREATIVE PREMISE AND END STATE
REFERENCE MAP BY ASSET AND ROLE
CONTINUITY LOCKS
TIMESTAMPED BEATS
ENVIRONMENT / MATERIAL / LIGHT / PHYSICS
DIALOGUE / VOICE / AMBIENCE / EFFECTS / MUSIC
EDIT-ONLY CHANGES
PRESERVE
EXCLUSIONS / FAILURE CONDITIONS
```

## Timeline

Use a timestamped plan when timing, cuts, actions, or edits matter.

Example:

```text
0–3s
- close product macro;
- condensation slides down the bottle;
- slow push-in;
- quiet room tone and one soft glass click.

3–8s
- talent lifts the product into frame;
- camera arcs 30 degrees while the background opens;
- music enters with restrained percussion.
```

Each beat should state only feasible concurrent actions. Preserve enough time
for transitions and physical completion.

## Evidence-grounded footage selection

Use this method when finding existing footage for a brief or storyboard. Query
the host's available search tools; these instructions do not provide an index,
retrieval API or permission to access another asset library.

Translate each beat into a footage request: narrative role, observable subject
or action, desired duration, framing, audio needs and necessary usage constraints.
Separate hard requirements from preferences. Use visual, transcript or on-screen
text search only where supported; report keyword-only or transcript-only coverage
instead of calling it full multimodal retrieval.

For shortlisted candidates, retain the source asset identity/version, source-time
range with units, and a playable locator when exposed by the host. Attach the
supporting evidence and its time, the selection reason, and unresolved conditions.
Keep these evidence types distinct:

| Evidence | What it can support | What still needs checking |
| --- | --- | --- |
| ASR transcript | Words reportedly spoken in that interval | Recognition accuracy, speaker and actual visual action |
| OCR or sampled frame | Text or appearance at that sampled time | Persistence, motion and the rest of the interval |
| Inspected video/audio interval | Observed action, sequence, timing and sound within the inspected range | Uninspected ranges and intended-use fit |
| Model inference or reuse suggestion | A candidate interpretation or creative use | Confirmation from the source; it is not an observation |

Search scores rank candidates within the host's retrieval method; they are not
quality probabilities and may not be comparable across models or search modes.
Keep per-modality scores and the contributing evidence for each hit rather than
one opaque number, and note the retrieval method or model version with the
shortlist. Hard constraints such as scope, usage rights or source should be
applied before ranking; if the host can only filter an already truncated top-k,
report that matching candidates may have been missed.
Merge overlapping hits from the same source into a review candidate while
retaining their evidence times. An index window is not an exact cut boundary.
Inspect the candidate with surrounding context before choosing in/out points:
avoid severed speech, unfinished actions and misleading changes of meaning.

For spoken footage, keep detected shot ranges separate from utterance ranges.
A scene change can occur mid-sentence, and an ASR segment can contain an
incomplete thought. Preserve the complete meaning, including qualifications and
negations; verify proposed speech boundaries by listening with surrounding
context. OCR subtitles and silence detection can nominate boundaries but cannot
prove speech completeness. Without listening, label the cut a candidate rather
than an approved speech edit.

Source footage often carries burned-in subtitles and disclaimers. Keep them, do
not add duplicate captions, and keep graphics clear of them. Burned subtitles can
lag speech: a cut must fall in a speech gap *and* after the subtitle changes, or
viewers read a line whose audio was cut. Music under voice defeats silence
detection; use ASR timing plus audio-energy valleys. ASR can hallucinate whole
sentences over music or tones, so cross-check its text with burned subtitles or
listening before using it as evidence. Place in-points at frame midpoints ((n+0.5)/fps):
a value a hair before a shot's first frame shows the previous shot. Check each
cut for fragments of an adjacent shot or a transition flash, and verify cut
frames by frame index, not timestamp seeks. The optional local-production module's `analyze` and
`suggest-cuts` commands apply these rules and mark conflicts for a decision. Begin audio crossfades after
the previous line ends, sample at least one frame per shot (fixed intervals miss
short shots), match segment loudness, and flag likenesses, endorsements or
promotions inherited from the source instead of extending them.

Where the host supports independent audio/video editing, continuous source
speech may span several picture cuts. Keep its source timing and caption alignment
explicit; check visible lip sync and whether covering footage misleadingly appears
to demonstrate the spoken claim. If independent tracks are unsupported, retain
a longer synchronized source interval or revise the sequence. Do not promise
split audio edits that the host cannot execute, or truncate a statement merely
to fit a preset duration.

Select for the beat's purpose, continuity and editability, not similarity alone.
Record the useful mechanism (for example, a clear product reveal or a concise
spoken hook) and how it will serve the new sequence. Do not label a clip
high-performing from visual appeal alone; performance claims need linked outcome
data and its evaluation context. Check source availability, identity and relevant
usage restrictions again before inserting it into the project. If the source
changed, treat old analysis as stale and request refreshed evidence.

For example, a frame at 12.4 s showing a hand and a bottle can nominate source
12–16 s for review. It cannot prove that the bottle is opened in that interval.
Confirm the action in playback before using it for an opening-action beat.

When no candidate fits, name the missing beat and required continuity references
for a generation brief or reshoot; absence from search does not prove absence
from the library. A generation brief is not an executed provider job. For small
requests, a compact shortlist with evidence and reasons suffices.

Host acceptance should cover Chinese visual/transcript/OCR queries according to
supported modalities, overlapping hits, direct source-time playback, stale source
analysis, inaccessible assets and no-match results. Confirm that the selected
cut supports its stated reason. Method documentation alone does not pass these
runtime checks.

## Mixing existing footage with generated shots

Use generation for a defined narrative or visual need within the selected
direction. First map the sequence to usable existing clips and remaining gaps.
For each gap, compare a local edit, a different existing clip, generation and a
reshoot against the required result. A deliberately new creative beat can justify
generation even when footage exists; state that purpose. Do not regenerate the
whole sequence to fill one missing shot.

Build the missing-shot brief from the video job fields above, emphasizing:

- **Role and slot:** what the shot contributes, intended timeline position,
  usable duration and any extra handles needed for cutting;
- **References:** source identities and exact frame/time selections, each with
  a role such as product geometry, character, lighting or camera language;
- **Continuity:** preceding end state and following start state, screen direction,
  subject scale, gaze, movement, lighting and sound that must carry across cuts;
- **Allowed invention:** what may change and what must stay faithful; references
  are not evidence that an invented product action or performance claim is true;
- **Acceptance:** a visible start/action/end state, boundary requirements and
  specific failure conditions, including label, identity and audio drift.

For Seedance or another provider, verify the current chosen model and access
surface before execution. Reference types, duration, audio and extension/editing
features depend on that surface; a brief must not promise unsupported controls.
Reuse existing execution and budget authorization where applicable. If the
available route or cost exceeds it, finish the brief and pause only that call.
Record provider job identity and reported cost when exposed; label estimates and
unknown cost explicitly. Follow the existing refinement and ambiguous-retry rules
in [iteration-and-versioning.md](iteration-and-versioning.md).

Treat a completed generation as a candidate asset. Inspect the actual video and
sound against the brief before placement. Preserve the reference lineage and
generation method separately from the original footage; do not overwrite source
assets or describe generated scenes as observed source evidence. If the output
misses the requirement, make a bounded revision or choose another production
method rather than silently weakening acceptance.

Insert an accepted candidate through the
[project-editing loop](#editing-an-existing-project), using the latest project
revision and retaining unrelated manual changes. If the generated duration differs
from the slot, choose a supported trim or explicit timing adjustment and check
its downstream effect. Inspect the assembled sequence across both joins: a good
standalone generation may still break motion, narrative or sound continuity.

Host acceptance requires an existing-footage sequence plus at least one actual
generated shot, traceable references/job/output, a bounded replacement preserving
manual edits, and audiovisual inspection of the assembled result. A placeholder,
mock provider response or written brief proves planning only. This method does
not itself supply a provider connector or establish that any host passed.

## Reference map

Give each reference a department-like responsibility:

- character identity;
- product geometry;
- scene;
- prop;
- composition;
- storyboard;
- camera language;
- subject motion;
- lighting;
- material;
- visual style;
- pacing;
- dialogue/voice;
- ambience;
- effects;
- music.

Example:

```text
@Image 1 — product geometry and label.
@Image 2 — talent identity and wardrobe.
@Video 1 — camera path and reveal timing, not character identity.
@Audio 1 — ambience density and energy arc, not direct reuse.
```

## Continuity lock

State invariants:

- subject appearance and voice;
- product geometry and label;
- wardrobe;
- environment and time of day;
- color and lighting logic;
- spatial relationships;
- motion direction;
- sound bed;
- narrative state at the extension boundary.

For an extension, restate the final state of the source and the exact next
action.

## Camera

Describe:

- shot size;
- angle;
- camera path;
- speed and acceleration;
- stabilization character;
- transition or occlusion;
- subject relationship;
- final framing.

Avoid stacking incompatible movements. Use a few purposeful moves instead of
continuous spectacle.

## Performance and physics

Describe behavior, not only appearance:

- gaze;
- facial temperature;
- body orientation;
- hand-object contact;
- weight transfer;
- pace;
- clothing and hair response;
- prop interaction;
- environmental forces;
- start and completed end state.

Physical plausibility must be inspected in the actual output.

## Audio

Separate:

- dialogue;
- voice character and delivery;
- ambience;
- synchronized sound effects;
- music function and energy arc;
- silence;
- rights or replacement status.

Do not assume a generated track is cleared for every commercial use. Record
provider and rights state.

## Editing

For targeted edits:

```text
EDIT
- exact time range;
- exact character, action, camera, background, or audio change.

PRESERVE
- all unchanged subjects;
- action timing outside the range;
- visual style;
- lighting continuity;
- audio continuity;
- first and final boundary frames.
```

A localized edit should not become an implicit full redesign.

### Editing an existing project

Use this loop when authorized to change an editable video project. A treatment
or critique alone does not require executing it. Discover the host's actual
tools and supported operations; this guidance does not supply an editing API.

1. **Read the current project.** Identify its revision, affected tracks and clip
   instances, source assets and source in/out points. Output-timeline time is
   different from source-media time; repeated uses of one asset are distinct
   instances. Preserve the user's latest manual edits and explicit locks.
   Read in layers: a project overview first, then only the affected timeline
   range, tracks or instances. A field the host omitted is unknown, not empty.
2. **Bound the change.** State the intended result and affected instances/ranges.
   Include necessary ripple, caption and audio adjustments in the scope; do not
   silently shift later clips. Prefer a supported local edit to regenerating
   footage. If the operation is unavailable, report that limit and the feasible
   alternative without inventing a tool or claiming execution.
3. **Apply against the read revision.** Follow the conflict and retry rules in
   [iteration-and-versioning.md](iteration-and-versioning.md#shared-project-revisions).
   Continue within existing authorization without adding approval at every step.
   Use the host's validate or preview mode when one exists, and submit one
   intended change as a single batch so it can be reviewed or undone as a unit.
   Keep cost-bearing or irreversible operations, such as generation, export and
   deletion, out of a reversible draft; run them only after the edit is accepted.
4. **Re-read and inspect.** Confirm the resulting revision, source bounds,
   duration, ordering, preserved tracks and caption/audio alignment. Preview the
   changed interval including both cut boundaries; listen when sound is affected.
   For a ripple edit, also inspect displaced downstream content. Bind the preview
   to the resulting revision so an older render cannot pass as the new result.
   Structurally, check for unintended same-track overlaps or gaps, edits on
   locked tracks, and wrong layer order where an upper track covers lower video.
   Inspect composed timeline frames: source-media frames support selection but
   do not prove trims, layers, captions or effects in the composition.

A successful edit response or render job proves neither visual quality nor
audio correctness. Report structural checks, actual audiovisual inspection and
unverified aspects separately. For a simple local cut, the host state and a brief
result note suffice; do not require a new manifest or a full production dossier.

### Host acceptance scenarios

When validating an editing integration, use an isolated project with repeated
uses of one source, captions and audio. Verify these behaviors on the actual host:

- a human moves a clip; the Agent reads that revision, edits the intended
  instance and preserves the human change;
- another edit lands between read and write; the stale write is rejected or
  safely prevented, then the Agent reassesses the latest project;
- a source becomes unavailable or changes identity; the affected edit/render
  reports the mismatch instead of substituting a different source silently;
- an unsupported operation returns a clear limit without claiming a change;
- the resulting preview matches the saved revision, including cut boundaries,
  Chinese captions when present, and affected audio.

These are acceptance criteria, not a claim that a host has passed them.

## Production flow

For a multi-beat production, keep state in `production.json`; a single trim or
caption fix uses the editing loop above without it. Stages run
`brief → reference → plan → select → generate → assemble → inspect ⇄ revise → export`;
skipping needs a reason. `scripts/creative_craft.py` provides `video-init`,
`video-record` (binds a project-relative file digest), `video-complete` (runs the
gate), `video-approve`, `video-skip`, `video-ledger` and `video-status`. Gates
check predecessors, approval (default `plan`), selected footage evidence, bound
generation Job/Receipt, render-qa against the current revision digest, the revision
round limit, and delivery promises on the exported revision. A modified bound file
blocks completion. Write plan changes after approval to a new file; structural
changes (beats, timing, roles, promises) send select/generate to approval. When the
round limit blocks revise, a person decides: accept, change the plan, or
`video-extend-rounds --by --reason`. `video-init --export-requires-human-review`
makes an accepted inspection wait for a named `video-approve --stage inspect
--by` sign-off before export; `reviewer_kind` inside render-qa is not evidence. Edit
documents may add speed, fades, crossfades, ducking and template graphics; see
the schema. Passing a gate proves contract consistency only; the render-qa
review of composited frames remains the visual evidence.

Write render-qa review findings for the person who signs off:
- Use their language.
- Give every time as output time (`m:ss.ss` of the rendered film), matching
  `refs[].time_seconds` and the review page's jump buttons.
- When a source time matters for the fix, label it as source time.
- Then regenerate `review.html` (`review-page`) so the page shows the review.

## Extension

Specify:

- source video;
- continuity locks;
- source final frame/state;
- next action;
- narrative purpose;
- duration;
- ending state;
- whether later extension is expected.

## Inspection

Review actual video for:

- prompt/brief adherence;
- subject and product consistency;
- multi-subject identity separation;
- movement and physical plausibility;
- blocking and spatial continuity;
- camera path and transitions;
- lighting and material continuity;
- accidental text or subtitles;
- dialogue, voice, effects, music, and sync;
- edit boundary integrity;
- start/end states;
- technical delivery;
- rights/provenance.

## Retry diagnosis

- identity drift: simplify subject count, strengthen reference roles and
  continuity locks;
- action failure: reduce concurrent actions and specify start/end states;
- camera confusion: use fewer movements and timestamp them;
- physics defects: make forces, contact, weight, and completion explicit;
- audio mismatch: separate dialogue, ambience, effects, and music;
- edit bleed: narrow the time range and repeat preserved invariants;
- narrative compression: remove a beat or extend in a second pass;
- inconsistent continuation: restate source end state and audiovisual locks.
