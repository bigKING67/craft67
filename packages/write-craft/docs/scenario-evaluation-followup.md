# Scenario-writing development check

Status: targeted calibration and fresh-case checks completed. The r30-r32
development failures below remain part of the record. This is not full release
evidence or a human-reader result.

## Changes

The existing decision-document reference now explains source-supported scenario
openings, real versus illustrative cases, deferred materials, and how to avoid
repeating a workflow in paragraphs, steps, and tables. A synthetic customer
support example teaches the behavior; a different warehouse scenario tests it.
No private business documents or media were added to the runtime or test set.

## Observed results

All calls used Pi `deepseek/deepseek-flash` for generation and judging, with raw
JSONL disabled. The local ignored artifacts are under
`.artifacts/write-craft-evals/`:

| Run | Machine result | Author inspection |
| --- | --- | --- |
| `scenario-targeted-r30` | 3/3 PASS | Sparse-module and short-status cases passed. New scenario repeated its purpose and changed an unstated history into no historical records. Its PASS is disputed. |
| `scenario-targeted-r31` | 1/1 PASS | Repetition improved, but the draft inferred an existing item-by-item manual workflow from a time-saving goal. Its PASS is disputed. |
| `scenario-targeted-r32` | 1/1 PASS | Explicit proposed state, human decision, no stock mutation, deferred materials, and no approval request were preserved. A redundant second paragraph and irrelevant absent-information inventory remained. Its PASS is disputed. |

These are successive development candidates with strengthened instructions and
criteria, not independent repetitions of one frozen candidate. Do not aggregate
them into a success rate. The earlier two compatibility checks do not establish
full regression coverage for the final candidate.

Final r32 evidence: after a complete scenario the draft adds a second paragraph
beginning `这套助手承担的只是`, restating its purpose and human boundary. It also
lists unspecified historical errors and goods despite their irrelevance to the
explanation. The judge accepts these against the explicit anti-repetition and
absence-inventory criterion. Inspect the candidate, not only the PASS label.

## Checks and remaining work

Source validation, package-boundary validation, Skill metadata validation, and
35 repository tests passed during this change. Final source/package checks and
diff whitespace checks passed after the last instruction/contract edit.

## Calibration follow-up

Added four fixed fixtures: reject a redundant paragraph, reject an irrelevant
absence inventory, accept a concise scenario, and accept a repeated boundary
that adds an actual acceptance check. The judge prompt now requires an
information-contribution check when the contract prohibits repetition, while
preserving useful emphasis and avoiding universal style-based blocking.

- `scenario-judge-calibration-r33`: 15/15 fixtures matched expected judgments,
  including the existing 11 fixtures.
- `scenario-targeted-r32/business-scenario-with-deferred-materials--1/rejudge-1`:
  the unchanged actual failed draft now receives FAIL for both its redundant
  paragraph and irrelevant absence inventory. Original artifacts are retained.
- `scenario-verified-r34`: a fresh draft received PASS on its first attempt,
  with zero revisions. Author inspection confirms a single workflow, proposed
  state, preserved human decision and no stock mutation, time-saving target
  distinguished from measurement, deferred real materials, and no approval
  request. It still contains an unnecessary sentence explaining that the current
  manual workflow is unspecified; this is an editorial improvement opportunity,
  not proof of ideal concision or universal effectiveness.

All these calls used Pi `deepseek/deepseek-flash`, low thinking, with raw JSONL
storage disabled. Static validation, 35 local tests, packaging, and whitespace
checks passed after the judge change. The runtime Skill was not changed in this
calibration follow-up. These checks preceded the final regression below.

## Final regression before commit

`scenario-final-regression-r35` completed all 18 regression cases with PASS,
using the same Pi model and low-thinking settings. Seventeen passed without
revision; `ai-video-proposal-rewrite` required the configured single revision.
Skill SHA-256: `984b940d86934d20a5d72a1b878daf8f8a3a91accc8934dc33a5e9cd6cebaccb`.
Reported model cost: 0.162944852. Raw JSONL storage remained disabled.

The scenario draft was inspected: one use scenario, evidence/communication
purpose, and the deferred-material note, without a redundant workflow paragraph
or absence inventory. The presentation draft retained factual boundaries but
still repeated the historical-evidence caveat. That remains a prose-quality
limitation; machine contract PASS does not establish uniformly concise prose.

Source validation, 35 local tests, package validation (15 entries, 76,538
unpacked bytes), and diff checks passed. This batch is prepared for a local
scoped commit. Human reading, real-media cases, exploration on this candidate,
and release acceptance remain unverified. No installation, push, or release
was performed.

## Adjacent repetition follow-up

The presentation reference now checks adjacent sentences and paragraphs for
new information rather than merely different wording. The presentation case
explicitly prohibits redundant evidence paraphrases, without rejecting useful
independent summaries or acceptance checks. Two fixed fixtures preserve the
actual r35 draft and a counterpart with only its duplicate paragraph removed.

- `adjacent-repetition-calibration-r36`: 17/17 judgments matched expectations.
  The unchanged r35 draft received FAIL; deleting only the duplicate evidence
  paragraph produced PASS. Existing positive and negative fixtures also passed.
- `adjacent-repetition-regression-r37`: both the scenario and presentation cases
  passed on their first attempt, with zero revisions. The presentation draft no
  longer contains the duplicate evidence paragraph. It preserves the proposed
  state, workflow, human judgment, excluded scope, and unresolved commitments.

These calls used Pi `deepseek/deepseek-flash`, low thinking for generation and
fact judging, with raw JSONL storage disabled. Candidate Skill SHA-256:
`794ae923b9775569eeb9dc1e5c3e2d19713d5b7732e29ba02f79ed45d846ab01`.
Reported model costs were 0.014068683 for calibration and 0.022725183 for the
targeted regression. Source validation, 35 local tests, package validation
(15 entries, 76,973 unpacked bytes), and whitespace checks passed.

Inspection still finds opportunities for concision: the presentation heading
restates the evidence conclusion before the paragraph explains its basis, and
the scenario mentions the unspecified current manual workflow. The specific
duplicate-paragraph failure is now covered; uniformly concise prose is not
established. This was a two-case targeted regression, not a rerun of all 18
cases on this candidate. Independent reader stages and human reading were not
run. No Feishu edit, installation, push, or release was performed.

## Editorial-pass candidate: r38 (quality acceptance not passed)

The candidate independently applies selected ljg-writes/ljg-paper methods:
content review followed by whole-draft Chinese editing, paragraph contribution,
sentence relationships, and reader-facing explanation. It revises two complete
examples, makes the editorial pass common to Chinese drafts, limits unsolicited
reader-test prompts, and reconciles relevant unknowns with absent fields.
See `upstream-absorption.md` for the pinned source and exclusions.

`editorial-pass-r38` used Pi `deepseek/deepseek-flash` for generation and fact
judging, low thinking, raw JSONL disabled. Skill SHA-256:
`25bec4a0153b724f86f7b0ce4abcddb2206875befe355455076f329ae688cfdd`.
All four selected cases received machine PASS without revision. The sufficient-
source case also passed its declared blind-reader and reader-judgment stages;
the other three do not declare those stages. This is targeted development
evidence, not unseen comparison or full regression evidence.

Direct inspection disputes the interpretation that all four are ready to send:

| Case | Inspection result |
| --- | --- |
| `sufficient-source-no-repeat-questions` | Preserves scope, budget, human confirmation, acceptance and risk. The draft does not expose the example's former author-facing causality disclaimer. No new blocking editorial issue identified in this inspection. |
| `clean-delivery-without-process-commentary` | A short update repeats completed/next work in a bold opening and bullets; `无` is immediately restated as no coordination matters. The clean-output contract passes, but brevity is not established. |
| `business-scenario-with-deferred-materials` | The second paragraph still explains that the old manual workflow was not provided, although the task asks to explain the proposed use rather than compare old and new workflows. The existing relevance criterion was not reliably enforced. |
| `formatted-document-uses-semantic-emphasis` | The opening workflow is retold in the first scope-table row. The exact adjacent evidence-paragraph failure is gone, but cross-form repetition remains. |

Do not label this candidate's general writing-quality acceptance PASS. Preserve
the raw candidates and machine judgments; no rerun was used to select a nicer
sample. The next evaluation change should distinguish factual blockers, explicit
delivery violations and located editorial defects, using these actual outputs
as development evidence alongside positive examples of useful repetition. It
must not silently redefine old PASS reports or treat every style preference as
a blocker. General editorial reporting, unseen comparison and human acceptance
remain incomplete.

Source validation, 35 local tests, package validation (15 entries, 80,325
unpacked bytes), and whitespace checks passed. They establish structural and
packaging validity, not language quality. No installation, Feishu edit, commit,
push, or release was performed in this batch.

## Editorial reporting protocol

New live fact judgments also require a `write-craft.editorial.v1` object. Each
issue has a category, a verbatim candidate quote, a reason and an editing
direction. Python validates the shape and quote occurrence, then derives
`NEEDS_EDIT` or `NO_ISSUES_FOUND`; the model does not choose that status.
These are observations, not a factual verdict or proof of send-readiness.
An issue that violates an explicit contract must still fail that contract.

The existing judgment status and exit-code meaning remain unchanged. Editorial
observations are persisted in judgments and result records, not automatically
used to trigger extra revisions or override release policy. Historical reports
without this object mean editorial review was not recorded, never that it
passed. Current live calls missing the object fail validation. No new agent or
additional per-draft model call is required.

The three unmodified r38 drafts were rejudged in their respective `rejudge-1`
directories, preserving original reports. All received `NEEDS_EDIT` alongside
contract PASS. The short-update judgment located the repeated coordination
status; the presentation judgment located the repeated workflow in the scope
table. Both support the observed editorial problem.

The scenario judgment located the unwanted manual-workflow sentence, but its
reason conflated a comparison of workflows with the source's time comparison.
This is a disputed rationale, not successful calibration of that failure type.
It should not be accepted merely because the overall label matches. No claim
is made that all three editorial diagnoses are now reliable or that writing
quality itself improved. The change so far makes observations visible; unseen
evaluation and human acceptance remain outstanding.

`editorial-calibration-r39` completed 19/19 fixtures with expected contract
judgments. The two new fixtures additionally asserted editorial status: a
redundant short update remained contract PASS with NEEDS_EDIT, while a boundary
repeated to add an acceptance check was NO_ISSUES_FOUND. The other 17 fixtures
check their existing contract verdicts, not universal editorial correctness.
All calls used Pi `deepseek/deepseek-flash`, low judge thinking, raw JSONL off.
The live evaluator digest was
`55da1869596111963f891017b74a95006891bdef8f44da5c8413982079b91713`.
Thirty-seven local tests, source/package validation and whitespace checks
passed; tests cover legacy absence, required live fields, quote validation and
separate verdict semantics. No commit, installation, push or release occurred.

## Gap relevance: minimal pair and one fresh draft

Two fixtures use identical source and candidate text; only the requested task
and corresponding contract differ. A missing old workflow is irrelevant to
explaining the proposed workflow, but relevant to a requested old/new comparison.
The evaluator now explicitly distinguishes the objects being compared before
diagnosing a relationship. The Chinese editing reference expresses the same
task-dependent relevance rule without inventing the missing workflow.

The new pair in `gap-relevance-calibration-r40` produced the expected observations:
`irrelevant_commentary` for the explanation-only task, and no editorial issue
for the requested comparison. The quoted issue and its explanation were checked,
not just the status. This is development calibration, not an unseen test.

The unchanged r38 scenario was preserved and rejudged as `rejudge-2`. Its
editorial verdict was NEEDS_EDIT, but it missed the target irrelevant sentence
and instead suggested a nearly unchanged version of the time-evidence sentence.
This is another disputed diagnosis. The minimal pair's success does not show
that the reviewer reliably generalizes to longer documents. Retain both rejudges;
do not promote matching status labels into successful defect detection.

`gap-relevance-draft-r41` generated the scenario once, with zero revisions:
contract PASS and NO_ISSUES_FOUND. Direct inspection confirms the unnecessary
old-workflow disclaimer is absent, while proposed state, input, difference list,
human recount decision, no inventory mutation, unmeasured time-saving target,
deferred samples and no approval request remain. This is one improved observed
draft, not a measured success rate. Its wording can still be tightened, and no
blind-reader stage or human reading was performed on this case.
Candidate Skill SHA-256:
`530b00a37ebb3291fb739db49b453ae770c66867d43d4577989fa8e01e0fdf97`.
All calls used Pi `deepseek/deepseek-flash`, low generator/judge thinking,
with raw JSONL disabled. No further prompt tuning or selective regeneration was
used after the disputed rejudge. Overall editorial reliability remains PARTIAL.

The full r40 calibration finished 21/21 with expected contract judgments and
all declared editorial-status expectations satisfied. Most fixtures still check
contract judgments only; this result does not cancel the observed r38 rejudge
failure. Source validation, 37 local tests, package validation (15 entries,
80,790 unpacked bytes), and whitespace checks passed. No commit, installation,
Feishu edit, push or release was performed.
