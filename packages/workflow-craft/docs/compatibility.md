# Host compatibility

## 0.6.0 native Windows support

The runtime now uses a Windows byte-range lock for worktree mutations and a
kill-on-close Job Object for verification. A gated launcher is assigned before
it can execute the approved argv; job assignment failure never starts project
code. Missing executables, failed checks, timeout/cancellation, retained output
and surviving children remain distinct from a passed check. Ordinary descendants
inherit the job; processes started through external services/WMI are outside this
lifecycle guarantee. This is not an OS sandbox.

The platform workflow runs the package contracts on Windows, Linux and macOS,
with Python 3.11 and 3.12. Native CI results and exact source revision are recorded
when available; macOS tests or mocked Windows behavior do not qualify Windows.
A colleague's Windows + Claude Code session remains a separate acceptance step.
Historical 0.5.x and 0.2.x limitations below describe those fixed versions.

Windows project commands must use an available interpreter (`py -3` / `python`)
and the native virtualenv layout (`Scripts/python.exe`). Fixed installed payloads
must retain their bytes when cloned: use repository `.gitattributes` with LF or
`-text` for installed Skill trees. Do not overwrite a member's global Claude rules.

## Codex entry archival and rollback (2026-10-31)

The [follow-up entry trial](aios-codex-entry.md) archives 12 legacy Skills and
three Codex Agent definitions outside discovery, preserving all 49 source
files and legacy contract checks. Codex 0.166.0 discovers Workflow Craft from
the repository root and an ETL subdirectory without Skill-disable overrides.
A native model session implicitly loads the Skill and completes the named
pilot task; a second session reads its current completion without writes or
reverification. Entry rollback preserves new task records and correctly marks
the evidence stale until the same candidate is restored.

Native CLI startup also wrote a project trust entry. That side effect and the
user-authorized temporary trust for the second session are explicitly recorded;
the global configuration is restored afterward. This is not a claim that trust
is unnecessary, all AIOS tasks have migrated, or Claude/Pi are runtime-qualified.
The fixed 0.5.1 payload is unchanged by this documentation-only delivery.

## 0.5.1 AIOS source replay and fresh-clone correction (2026-10-30)

The [isolated AIOS trial](aios-pilot.md) replays nine existing business tests,
simulated-member worktree handoffs, partial/failed integration rejection and
fresh-clone continuation. It found a namespaced-base fallback defect in 0.5.0.
The final 0.5.1 candidate fixes it, preserves ambiguous-ref rejection and passes
installed upgrade/reverification/fresh-clone checks. Its SHA-256 is
`55fb8d9fed573cc689155c31e984ea6bee85e062b06b3648aa1fb828f2acfcc4`
(95,172 bytes, 39 payload files). The source replay and initial independent Agent
used the fixed 0.5.0 candidate below; the final correction was verified through
installed CLI use, not a new native-host model session or human team.

The final stable-input package gate passes **193 tests, with no skips**, including
three new base-resolution regressions. Version checks, payload/source parity and
local documentation links pass. A prior gate overlapped a source revision and
reported the expected toolchain-lock mismatch; its log is retained as an invalid
stable-candidate sample, not counted as a passing run.

The project gate still requires a legacy Trellis entry. Passing while retaining
that entry establishes bounded coexistence, not retirement or superiority over
Trellis. Real AIOS, global installation, remote services and release are unchanged.

The subsequent [2026-10-31 Codex pilot](aios-pilot.md#codex-接管试点2026-10-31)
preserves that cross-host gate and adds a separate pilot gate. It distinguishes
native project trust/configuration loading from actual Skill availability:
on Codex 0.166.0 the observed catalogue only reports the legacy Skills disabled
with explicit process overrides. The controlled model trial, its initial
interpreter/dependency failure, and the corrected project environment are
recorded separately. This does not establish automatic project-only cutover.
After correcting the fixture's interpreter entry, the second native session
completed the task, both checks, handoff and session finish in 257.17 seconds
with exit 0 and no out-of-scope writes. The temporary user-authorized project
trust entry was removed and global configuration bytes matched the original.

## 0.5.0 lifecycle candidate acceptance (2026-10-30)

The source candidate adds local execution lifecycle and explicit session bindings;
it does not migrate AIOS, enable global discovery, or change running host settings.
Package version is 0.5.0, runtime protocol 3, existing exchange records remain v2
with optional execution v1 data inside TaskRecord.

- Offline package gate: **190 tests passed**, including 15 new lifecycle regressions.
  Cases cover parent/child completion, paused/resumed work, session finish without
  completion, separate worktrees, competing processes, stale evidence, explicit
  review observations, contract updates and changes during completion validation.
- Skill static validation passed using an isolated cached PyYAML environment.
- Final fixed ZIP: 95,073 bytes, 39 payload files, SHA-256
  `0250e64deaa37fbb73336f1bf74ab4e1165321f04ae61044f7924c42bc1c5914`.
  Every payload file matched that candidate's source snapshot or injected VERSION/LICENSE.
- Mutating workflow commands use POSIX worktree locking. Native Windows writes
  are unsupported; reading records is not equivalent to write-path qualification.
- These checks do not establish native Codex/Claude/Pi automatic discovery,
  independent human collaboration, AIOS business acceptance, migration or release.

An independent Agent used the initial fixed candidate (94,998 bytes; SHA-256
`fa560f29a9877369ea6a895a193cfa6e2ff52b57369ed380368b0a18f6adf2ee`)
in a temporary personal-mode Python project. It created one parent and two children,
wrote a handoff, paused and resumed a child in a new session, implemented the second
child, then reopened/reverified the earlier child after the code changed. All three
tasks ended completed/current; task lint passed and the project passed three actual
Python assertions. No Skill files were changed by the evaluator. This is explicit
Skill reading and CLI use by an independent Agent, not native discovery or two humans.

The initial trial retains three first-attempt obstacles: creating a child while its
parent still held the same session binding, unignored Python bytecode changing the
verification fingerprint, and using a local task ID in the URL-only dependencies
field. The fixture corrected session usage, ignored generated files, and used the
supported parent relationship. These observations are retained, not erased from the
trial. Local dependency graphs beyond parent/child relationships remain unsupported.

The final candidate differs only in `scripts/twc_lib/tasks.py`: an unbound explicit
session now suggests listing/reading existing tasks before authorized start, instead
of suggesting prepare. The final artifact passed a separate installed-CLI regression
showing that hint and unchanged task bytes, and the full 190-test gate passed again.
The entire Agent scenario was not rerun against this final hint-only revision.

Workflow Craft packages one portable Agent Skill directory. The artifact
contains `SKILL.md`, its runtime `scripts/`, references/assets when present,
and injected `VERSION` and `LICENSE`. It does not contain a link back to the
craft67 checkout. Each host installation is a separate, explicit project-local
copy; an artifact being built or installed does not prove a host loaded it in a
current session.

| Host | `install.py --project` destination | Explicit invocation | Historical native discovery on macOS, 2026-10-16 |
| --- | --- | --- | --- |
| Codex 0.162.1 | `.agents/skills/workflow-craft/` | `$workflow-craft` | `PASS`: native prompt-input catalog resolves to the project installation. |
| Claude Code 2.1.296 | `.claude/skills/workflow-craft/` | `/workflow-craft` | `PASS`: native initialization lists the command with project scope. |
| Pi 1.1.0 | `.agents/skills/workflow-craft/` | `/skill:workflow-craft` | `PASS`: native RPC lists the skill and exact project source path. |

The current destinations and invocation names above use workflow-craft. The dated host observations used the former team-workflow-craft name and do not establish discovery of the renamed package.

The destinations are project-relative. The installer has no default target and
rejects global installation paths. It never updates a host profile, account,
settings file, hook, or running session.

## 0.4.1 project-rule cooperation acceptance (2026-10-30)

The fixed local candidate is `workflow-craft-0.4.1.zip`, SHA-256
`6272e477567ad7789250855b09c3d27b752e8efd23071dcd4f7236cccd5168db`,
85,794 bytes and 37 payload files. An independent rebuild is byte-identical.
The final offline package gate passes 163 tests, including a regression that
defers verification, reruns one selected check, and keeps the other check stale
and handoff unready until its required evidence is available. Version metadata
and Skill validation pass. Protocol and record schema remain 2.

Three fresh Codex 0.166.0 sessions explicitly invoked the installed Skill using
the existing user-selected `gpt-6.1-sol` / `max`. Each fixture contains project
AGENTS.md, shared code conventions in CLAUDE.md, an existing quick/full test
runner and server merge-queue configuration. Project instructions are enabled;
global AGENTS may also apply. Other Skills, plugins, memory, multi-agent features
and external search are disabled in the evaluation configuration. Implementation
cases use workspace-write; the inspection case uses read-only. Each is capped
at 300 seconds, with no retries or model changes.

| Scenario | Observed result | Project writes | Time |
| --- | --- | --- | --- |
| Ordinary multi-file change, no workflow task | PASS: implemented blank-name fallback and whitespace normalization with existing functions/tests; ran quick once after the implementation; no mode/name/approval questions, task initialization or extra workflow directory | Three requested source/test files and the ignored test ledger | 64.67 s |
| Continue an existing task with stale evidence | PASS: resumed without repeating prepare; preserved existing WIP; implemented the change and ran only quick once through the installed CLI; quick becomes passed while full remains stale, explicitly left for project integration CI | Same source/test files, quick evidence and the existing handoff; rules, contract and integration config unchanged | 132.70 s |
| Read-only team handoff with an existing merge queue | PASS: no file changes or project checks; retained the queue, distinguished local checking from server approval, and identified that old passing tests did not cover the next requested behavior | None; all project file hashes unchanged | 135.05 s |

The event-stream SHA-256 values in table order are
`a7b847d002123fab86f526fc130166f63fdc15fd5036204e8a89466543393154`,
`b47fa304d3fb07894a701f504ce3d085837a527d0e15e021a94b878427838800`,
and `aac637246728d61da8082ed8d182abee1c8fce2868ba1f4a5f6c0cbf9f95cb17`.
The parent reviewer checked actual command/write traces, test ledgers, source
behavior, evidence states and final messages; model self-reports alone were
not the acceptance criterion. No host prompt supplied the expected Skill route.

These are three bounded, synthetic, explicit-invocation observations on one
host/model configuration, not proof of universal rule compatibility or a
comparison against the prior version. Reading CLAUDE.md in Codex does not
establish native Claude Code behavior. No live merge queue, remote platform,
global installation or external project configuration was changed. The local
checker still cannot certify queue-generated merges or CI; unsupported profiles
remain rejected rather than being silently treated as verified.

## 0.4.0 workflow references and optional status adapters (2026-10-30)

The fixed local candidate is `workflow-craft-0.4.0.zip`, SHA-256
`1ccaa3a7d7600f5fd939e1899603182d4cd3ccbe07146d377bc159e501a9639d`,
83,972 bytes and 37 payload files. An independent rebuild is byte-identical;
installed integrity is `matched`. Protocol remains 2. The final package gate
passes 162 tests with no skips on Python 3.14.7 / Node 24.22.1. Version metadata,
Skill validation and local reference links also pass.

The entrypoint now states how it cooperates with project instructions and routes
detailed commands to `references/task-loop.md`. The original command, evidence
and authorization paragraphs were checked against the moved text; only heading,
relative links and the wording about not requiring Hooks changed there. Feature
verification guidance reuses existing project tests and documentation. These
are source/structure checks, not a new model-behavior evaluation.

| Surface | Verified result | Boundary |
| --- | --- | --- |
| Python mode reader | Actual Git roots, subdirectories, nested repositories, linked worktrees, legacy team config, mode refresh, invalid input, bounded Git failure and no project writes/check execution | Displays configured mode; does not validate task readiness or host Skill discovery |
| Claude Code adapter | Real stdin JSON command handles workspace.current_dir/cwd and malformed input; script is present and runnable in source-independent installed bundles | Native Claude TUI rendering and composition with a user's existing status renderer remain unverified |
| Pi 1.4.0 RPC | Native loader executes the installed TypeScript extension; emits solo, clears its status on session replacement, then emits team after the fixture changes config | Explicit extension path and isolated runtime; no model prompt or automatic discovery |
| Pi 1.4.0 terminal | Native terminal renders `Workflow: team` from the final installed artifact | Captured through a PTY; the harness explicitly terminated its own process after capture, so this does not claim graceful terminal shutdown |
| Pi event contract | Preserves another extension's status, refreshes on session/agent events, clears its own key, rejects stale callbacks and reports missing interpreter | Automated event fixture; no user footer/settings were changed |

The first terminal-capture attempt was an invalid sample because the harness
timed out during shutdown before persisting its output. The corrected capture
retains the terminal output and termination result. RPC shuts down normally.
The RPC project changes only in the fixture's explicit config edit; no new
project files appear. No paid model call, global installation, settings update,
Git commit/push or formal release was performed in this slice.

See [verification paths](verification-paths.md) for repeatable checks and
[status integration](../skills/workflow-craft/references/statusline.md) for
opt-in host configuration. Codex has no custom status-script adapter in this
version; it continues to use mode/resume and a brief opening mode statement.

## 0.3.1 rename and installed migration (2026-10-30)

The package and Skill are now `workflow-craft`. The fixed local candidate has
SHA-256 `bb0d7b1f1f7811f9f0601077182e20d520d2418c6ee30de665723fbbbce5ba90`,
75,428 bytes and 31 payload files; an independent rebuild is byte-identical.
The package gate passes 151 tests; root metadata tests pass 23 tests and layout
validation reports 11 packages/19 Skills. Skill metadata validation also passes.

A scratch project using the fixed 0.3.0 installation and a verified personal
local task passed migration to the new installation name. Preview writes nothing;
explicit `--allow-upgrade --apply` verifies the old bundle and leaves only the
new Skill directory. Configuration, task history, actors, evidence, binding and
old lock retain their bytes. The new runtime reports the old lock mismatch and
stale verification; after reviewing the new lock, re-verification and `check`
pass. Repeated installation is idempotent. Regression cases reject drift,
unknown markers, symlinks, duplicate names and concurrent source edits, and
restore the old directory when the new destination cannot be written.

This is installed-CLI evidence. No new host-model session, global installation
or release was performed for the renamed Skill; earlier host observations below
retain their original names and versions. Existing member installations are not
changed by the source rename.

## 0.3.0 candidate: personal/team installed CLI acceptance (2026-10-30)

The fixed ZIP SHA-256 is
`a00f05319fd95e7a006a9eda6312d7e013fa4f1761cfd4976d11e567dcbad6f8`.
The package gate passes 147 tests, including source-independent installed CLI
checks for the Codex/Claude/Pi destination conventions and a platform-free
personal task loop. First use requires an explicit project mode; another project
chooses independently, while subdirectories reuse the project configuration.
Mode changes retain task history, attribution, checks and existing platform or
integrator requirements; changed policy invalidates old verification.

A separate fixed-0.2.5 upgrade accepts the existing v1 configuration as team,
preserves old records and lock, rejects execution until the new runtime lock is
reviewed, and requires re-verification. A subsequent change to personal preserves
the original PR's platform and integration requirements. These are local CLI and
installation results; they do not establish global discovery, cross-machine use
or independent human collaboration. See [operations](operations.md#本地-030-候选验收2026-10-30)
for the artifact and rollback boundary.

## 0.3.0 first-use prompt: controlled Codex acceptance (2026-10-30)

One fresh Codex 0.166.0 session used the current user-configured `gpt-6.1-sol`
with `max`, the fixed 0.3.0 candidate above, and a synthetic repository with an
existing name `67`, no email and no workflow configuration. The read-only prompt
explicitly invoked the Skill to inspect development/continuation readiness; it
did not supply a mode or tell the model to ask about personal/team development.

The session read the installed Skill, ran `doctor --local` and `resume`, asked
the personal/team question, reused the existing name without asking for an
email, and stopped short of initialization. It completed in 133.53 seconds with
20 local read-only commands; all 61 project files, including Git state, retained
their hashes. No project checks or platform requests ran. The event-stream
SHA-256 is `89f48ff20b6370f72014c33f35045cee876beff81d79db185ece280e7c3ea512`.

This follows the [explicit-invocation and captured-trace evaluation approach](https://developers.openai.com/blog/eval-skills).
It establishes this first-use behavior in one controlled host session, not
implicit/global discovery, repeated-session mode reuse, model quality improvement,
or independent human acceptance. Global AGENTS may still apply; mode reuse and
switching are covered by the CLI regressions above. The old harness stopped at
a local model-configuration assertion before making any model call; the run then
used the live user configuration without changing it.

## 0.2.5 candidate: installed CLI acceptance (2026-10-29)

The fixed local ZIP SHA-256 is
`35f5015097034d828df35361c30c6eb8043ad2ee758e769528aa40b3916c7589`.
Six temporary projects passed fresh installation and fixed-0.2.4 upgrade checks
for Codex, Claude and Pi target parameters. Checks cover name-only onboarding,
unchanged legacy task/verification attribution, newly recorded names, explicit
upgrade, lock mismatch, stale old evidence, re-verification, nonmutating preview,
idempotency and drift rejection. These are installed-CLI checks, not three
host-model sessions. The first fixture's uncommitted setup was correctly blocked
at handoff; its failure is retained, and the same candidate passed with committed
fixture state. Rebuilding produced identical bytes. See
[operations](operations.md#本地-025-候选验收2026-10-29) for the artifact and rollback boundary.

## Name-only onboarding: controlled Codex acceptance (2026-10-29)

One fresh Codex 0.165.0 session used `gpt-6-astra` with `xhigh`, an installed
development snapshot, and a synthetic project whose current member had no name
or email. The prompt explicitly invoked the Skill for read-only takeover,
without supplying the expected name question. Codex read the installed Skill,
ran `doctor --local` and `resume`, asked only for a name or nickname, and continued
with a takeover summary. It made nine local read-only commands in 94.73 seconds;
all 78 project files, including Git config/index, were unchanged. It ran no
project tests and made no platform requests.

The development ZIP SHA-256 was
`1ecc0e37179b98c777652b953eefd882347ebbeb531a34d157d7ae2e1f297523`;
it carried 0.2.4 but was not the fixed 0.2.4 candidate below. Only VERSION differs
from the fixed 0.2.5 candidate. This establishes content parity, not a fresh
0.2.5 host session. Global AGENTS remained part of the host context; the result
does not isolate TWC causality or establish automatic discovery, other hosts,
independent-member collaboration, cross-machine use or remote release.

## 0.2.4 candidate: installed CLI acceptance (2026-10-29)

The fixed local candidate SHA-256 is
`635f4e7898f06f584f2a158ea384be11b7892b46a77cf1307fce026ff1f098b4`.
Six temporary projects passed fresh installation and 0.2.3-to-0.2.4 upgrade
checks for the Codex, Claude and Pi target parameters: nonmutating preview,
explicit upgrade, preserved old lock/evidence, detected lock mismatch,
reviewed lock update, stale old verification, successful re-verification,
idempotency and drift rejection. Codex/Pi share one directory convention;
these are installer and installed-CLI checks, not three host-model sessions.
Rebuilding with the same toolchain produced identical bytes. Details and
rollback limits are recorded in [operations](operations.md#本地-024-候选验收2026-10-29).

Only VERSION differs from the source-guidance test ZIP below; the runtime
content hash is unchanged. That establishes content parity, not a new-version
host-loading result. Fresh 0.2.4 model sessions, independent members,
cross-machine use and remote release remain unverified.

## Source guidance: controlled Codex behavior acceptance (2026-10-29)

Four fresh Codex 0.165.0 sessions used the configured `gpt-6-astra` model with
`xhigh` reasoning, one synthetic project per case. Each prompt explicitly
invoked the project Skill and supplied the task and permitted scope, without
the expected answer. This tests explicit invocation, not automatic selection.
The first three cases used `read-only`; the small edit used `workspace-write`.
Each had a 300-second limit; all four completed without changing model or
extending the limit.

The uncommitted guidance was built and installed with this package's own tools
into fresh temporary projects. The test ZIP SHA-256 is
`0607d1d9b6e954380f3249f91aa66a552460c43a3793f768efa99108151c93d1`;
the runtime content hash is
`c8950a2b95736e7ff4404c1c7ef5b0f733967bc6ca27db6e558f93a6bc2310d1`.
At the time of these sessions the source carried development version 0.2.3; this disposable test
build is distinct from the earlier fixed candidate below. It was not used to
upgrade an existing installation or distributed as a replacement candidate.
The later 0.2.4 candidate above gives this content its own version; the original
test build and session evidence retain their identities.

| Case | Observed result | File changes | Duration |
| --- | --- | --- | --- |
| Broad goal to first usable release | `PASS`: proposed date selection, reconciliation and CSV export; deferred weekly automation and alerts; separated observable acceptance from unresolved business rules. Read `context.md` and ran `resume`. | None | 228.65 s |
| Diagnosis after two failed attempts | `PASS`: retained both failed attempts, kept the real cause unknown, and proposed correlation evidence to distinguish duplicate requests from duplicate processing. Read `handoff.md` and ran `resume`. | None | 156.89 s |
| Unresolved findings after three review-and-fix rounds | `PASS`: retained `not_ready`, named both permission blockers, and requested product/security adjudication before targeted remediation. Read `collaboration.md` and ran `resume`; did not equate the round limit with approval. | None | 157.65 s |
| One-line CLI copy edit | `PASS`: applied the L0 route, corrected the message, checked the actual CLI output and passed the two existing tests. Created no task, handoff or extra test. | Only `cli.py` in the fixture | 51.89 s |

All four traces show reads of the project `SKILL.md`; before/after content
hashes and Git heads confirm the stated scope and no commits. No observed
command contacted a collaboration platform. Extra MCP, hooks, apps, plugins,
memory and multi-agent features were disabled for the test process. Codex
still supplied the user's global AGENTS guidance, so these results belong to
that combined host setup; they do not isolate a causal improvement from TWC.

Two earlier setup failures remain excluded and retained: an invalid disabled
MCP configuration stopped before a model task, then a direct source-directory
copy omitted the injected `VERSION` file and made `resume` fail. The latter
session was stopped and marked `INVALID SAMPLE`; no partial answer was counted
as a pass. Fresh fixtures created by `build.py`/`install.py` passed CLI preflight
before the four valid sessions. A nonexistent-file search in the first valid
case and a no-match AGENTS search in L0 were recoverable reads, not successful
checks or reasons to discard their original traces.

Final-answer SHA-256 values, in table order:

- `6f89ab61bbf87d445609a6e1511f9f773f7dfa16daee584549a1526de49a1e5d`
- `3b9c800a9891f757ae30ca8008e0ff0a20f10e9622f2f8aaaa4f8520ef7bb8b6`
- `26677968ac644c4ec44cc70af8e844d0c7a070e1b96c60814d07756d5a877515`
- `49e0f5f3daf32a79153ea4b7f69e622d4739b5618a10c0baf0d669d26f0fc0ed`

These are same-machine synthetic cases assessed by the initiating operator,
not an independent-member pilot, a model benchmark, a before/after comparison,
or Pi/Claude/platform acceptance. No global installation or release was made.
The test used [Codex exec](https://learn.chatgpt.com/docs/developer-commands#codex-exec)
with ephemeral sessions and local JSON event capture; ephemeral mode alone is
not a claim of host-state isolation.

## Local 0.2.3 candidate: command semantics and upgrade (2026-10-29)

The local unreleased ZIP SHA-256 is
`2f428a5497f2a59aebbcde892a0bb934b5f36c31fc182a58c77b5c16df946eda`.
Its 29 payload files match the source snapshot before the workflow-guidance
additions described above. The version, Skill,
identity reference and CLI help differ from the original fixed 0.2.2 artifact;
runtime dispatch and argument behavior are unchanged. Prior artifacts and
historical evidence remain separate.

Three synthetic projects exercised the Codex, Claude and Pi install paths.
Each refused an upgrade without `--allow-upgrade`, left files unchanged during
preview, upgraded from fixed 0.2.2 to 0.2.3 with explicit apply, and accepted an
identical reinstall without mutation. A locally edited installation was refused
without overwriting the edit. The old project toolchain lock was preserved;
`doctor --local` reported its mismatch until the new runtime identity was
reviewed and explicitly pinned. The subsequent toolchain and installation
checks matched. These are installer/installed-CLI results, not three host-model
acceptances.

Two new Pi 1.4.0 / `deepseek/deepseek-flash` / `high` sessions retained native
retry settings and used the same ordinary and conflict prompts as the earlier
synthetic tests. The ordinary case read the Skill and ran `resume`, local checks
and a verification preview (17 calls). The conflict case read the updated
identity reference, inferred the conflict from files and made 9 calls; it did
not read the Skill body or run `resume`.

The conflict answer correctly identified `prepare` as networked by default,
`--offline` as still writing locally, `doctor --online` as not writing packets,
and possible network access by project checks. It did not propose
`prepare --online`. All 26 calls were reviewed; 41/42 files plus Git config and
index retained bytes and modes. No repair, project test or platform request ran.
Both sessions ended normally without connection errors. The ordinary case also
checked the configured interpreter path's existence and queried global Git
configuration redirected to an empty file; no outside project contents were
read.

The targeted command-semantics check passed, not full workflow-advice quality:
the conflict answer still overstated `doctor --online` as confirming task
assignment, which that diagnostic does not inspect. This remains a bounded,
same-machine synthetic result, with no OS sandbox guarantee. Package checks
passed 127 tests. New-version Codex/Claude model sessions, independent members,
cross-machine use, native Windows and remote release remain outside this result.

## Session acceptance: read-only handoff (0.2.2, 2026-10-26)

The CNB pilot's fixed 0.2.2 candidate was installed in a fresh branch clone at
`60fa7741678eba594e51859a35154c646c57b9c7`, with base
`008bd37814a883edee71854c5d95386b9efbba92`. Artifact and merge identities are
recorded in [the pilot acceptance snapshot](operations.md).

A new ephemeral Codex session received an ordinary prompt to inspect the
handoff state and next step, without naming the Skill. Its first command read
the project 0.2.2 `SKILL.md`. It identified PR #6, the fresh unit evidence for
that branch, and stale evidence for older tasks, leaving verification and
reviewed rebind as next actions. The session ran in a read-only sandbox with
extra MCP, hooks, apps, memory and multi-agent execution disabled, and no CNB
credentials injected. All 26 observed commands were read-only queries; none
ran tests, contacted the platform, prepared a task or rebound it. The 46 tracked
files and 30 installation files remained byte-for-byte unchanged.

This is one controlled Codex session on a synthetic task, not an independent
member or cross-machine acceptance. The later merged-main clone had the same
installation bytes but no additional host session. The Claude Code and Pi
follow-up is recorded below; older results retain their own dates and artifact
versions.

## Initial session follow-up (0.2.2, 2026-10-28)

On macOS 27.0.1 arm64 with Python 3.12.10, each host received a new local clone
from the verified PR #6 seed, pinned to the same `60fa7741` head and `008bd378`
base as the Codex sample above. These were offline clones of that fixed branch,
not a fresh observation of remote main. Each project installation came from
the same 0.2.2 artifact (29 payload files), and neither clone inherited ignored
local task state. Both received the same ordinary read-only handoff prompt,
without a Skill name or explicit invocation.

| Host / actual model | Result |
| --- | --- |
| Claude Code 2.1.308 / `claude-opus-5-5` | `PASS` for this bounded case: native discovery and `Skill` invocation loaded the project copy; `doctor --local` and `resume` identified PR #6, its fresh unit evidence and AC-2 through AC-5 as `needs_review`. |
| Pi 1.4.0 / `deepseek/deepseek-flash`, then the existing `anthropic/claude-sonnet-5` configuration | `BLOCKED` at the model channel: startup listed the exact project Skill path, but both attempts ended before any project tool call. Skill-body invocation and `resume` remain `UNVERIFIED`. |

Claude ran with isolated host state, project settings, hooks disabled, an empty
strict MCP configuration and Read/Glob/Grep/Skill/Bash available. Its successful
session made one Skill call and two Bash calls. Parent review of both command
strings found only local doctor/resume, Git and directory queries; no tests,
platform/network commands, task preparation or rebind ran. Its answer preserved
the previous executor, required human review for text ACs and left current
platform/identity facts unknown. It checked the current PR's fresh evidence;
older-task stale evidence and explicit rebind conflicts were not separate
model cases in this sample.

The first Claude attempt was an `INVALID SAMPLE`: a literal Bash allowlist
rejected a read-only command that used a shell variable. It was retained and
stopped (exit 143). One new session used the same actual model, prompt, fixture,
600-second limit and USD 5 budget cap with Bash available, matching Pi's tool
availability. Only that corrected session counts as the passing sample.

Pi used isolated host state, disabled extensions/MCP/startup network operations,
ephemeral sessions and read/bash tools. The default DeepSeek attempt reported
`Connection error`; a separate Node HEAD probe to that endpoint observed
`ECONNRESET` before TLS establishment. The existing Anthropic configuration
reported `Anthropic stream ended without a stop reason`. Both CLI processes
exited 0 while the assistant record had `stopReason=error`; process exit alone
was not accepted as success. The failed attempts were retained, and no further
model retry was counted as a pass.

No CNB credentials were injected. Each clone's 46 tracked files and 30 installed
files retained their exact bytes and modes, with no local task binding created.
Read-only behavior here is an observed trace/file result, not an OS sandbox
claim. Host configuration files and the original worktree were unchanged before
the acceptance documentation update. Independent people, cross-machine use,
native Windows and Pi's successful 0.2.2 handoff remain outside this evidence.

## Pi repair and scoped handoff (0.2.2, 2026-10-28)

The later Pi 1.4.0 / `deepseek/deepseek-flash` / `high` session completed project
Skill loading and read-only `resume` with native retry recovery. It used a fresh
clone of the same fixed PR #6 head/base and artifact. The ordinary handoff prompt
added an explicit current-repository-only constraint; this is a separate scoped
case, not an identical-prompt comparison with the earlier samples.

Two causes were investigated separately:

- DeepSeek resolved to two IPv4 addresses: one completed TLS while the other
  reset it. The initial harness had forced `retry.enabled=false`, although the
  user's normal Pi settings already enabled retries (maximum 5, base delay
  1,000 ms). The corrected harness preserved those settings, the default
  provider/model and `high` reasoning. It did not pin an IP or change system DNS.
- The machine's custom `claude-sonnet-5` record omitted the native Pi 1.4.0
  `compat.forceAdaptiveThinking=true` metadata. The other four configured Claude
  models already had it. With `high`, the uncorrected record sent legacy
  `thinking.type=enabled`; a captured response was HTTP 200 with zero content,
  followed by the stream error. Changing only that field produced
  `thinking.type=adaptive`, complete SSE through `message_stop`, and a normal
  result using the same endpoint, model and credential. A separate real Pi
  process then loaded the corrected canonical configuration and returned
  `PI_CONNECTION_OK` at `high`, without an observer or transport shim.

Only the Sonnet 5 compatibility field changed in the machine-owned model
configuration. Authentication, the default provider/model, the launcher and Pi
version stayed unchanged. No model router, provider fallback or runtime patch
was added. The diagnostic observer recorded only request/response metadata;
the final handoff ran without it.

In the final scoped handoff, parent review covered all 18 tool calls (one Read,
17 Bash). They read the project Skill, queried `resume`, `doctor --local` and
`check`, previewed `verify`, and inspected local Git/files/hashes. No outside
clone read, project test, platform request, prepare, rebind or write command
ran. All 46 tracked files and 30 installation files retained their bytes and
modes, and no local task binding was created. Four `Connection error` records
were retained; native retries recovered them in two groups before the final
assistant response ended normally. The external failing address remains a
network limitation; successful recovery does not certify every route as healthy.

An earlier recovered handoff inspected sibling pilot clones. That sample is
retained as `PARTIAL` for repository-only acceptance, and is not the scoped
passing sample. The final answer also incorrectly placed `git config --local`
under a “no-write” advice heading; it requested approval and did not execute
that write. The pass therefore covers observed loading/resume/read-only
execution, with this advice-quality limitation. Independent people,
cross-machine use, explicit rebind conflicts, native Windows and an OS sandbox
guarantee remain outside the result. TWC runtime files, version and fixed
artifact were unchanged.

## Local read-only advice follow-up (0.2.2, 2026-10-29)

The Skill body and identity reference now distinguish identity queries from
local identity setters, and classify `prepare` (including `--rebind`) as task
record/binding writes. Existing authorization still determines whether a later
write may run; no new approval gate or CLI behavior was added.

The resulting local, unreleased 0.2.2 ZIP has SHA-256
`8187ac176c01700568bfa527a7d3213d08ed97ee061dbad534eabdff7a869fb0`.
Only those two instruction files differ among its 29 payload files. It was
built from the uncommitted worktree and is distinct from the prior CNB-pinned
`e3b6b51f…` artifact. The old artifact, tasks and CI evidence were preserved;
their earlier acceptance does not transfer to this candidate.

Two new Pi 1.4.0 / `deepseek/deepseek-flash` / `high` sessions used the existing
native retry settings and fresh offline synthetic repositories. Global Git
configuration was excluded from these fixture processes so repository-level
identity fields were absent. No transport observer, provider fallback or
global configuration change was used. Only the current repository was in
scope, and neither prompt supplied the Skill name or the expected answer.

| Case | Observed behavior | Calls | Files unchanged |
| --- | --- | --- | --- |
| Ordinary read-only handoff | Read the new Skill and identity reference; ran `resume`, `check` and `doctor --local`; classified identity setters and task preparation as writes | 14 (one Read, 13 Bash) | 41 |
| Identity/binding conflict | Read the updated identity reference and task files; classified identity setters and rebind as writes; inferred the cross-branch binding conflict without running `resume` or reading the Skill body | 10 Bash | 42 |

Parent review covered all 24 calls. Repository files, ignored local bindings,
Git configuration and index retained their bytes and modes; no project check,
repair, platform request or write command ran. The configured check deliberately
writes a sentinel; it was not executed and its marker remained absent. Both
sessions ended normally, with no connection errors (about 40 and 26 seconds).
This is observed behavior, not an OS sandbox guarantee or a general model
quality measurement.

The targeted identity/rebind write classification passed. Broader advice did
not receive a complete-workflow pass: the conflict answer confused `prepare`'s
default network behavior and some option names. The CLI still contacts the
platform by default during `prepare`; `--offline` is required to avoid that
request. No suggested correction was executed. Package checks passed 127 tests;
they remain separate from these host traces. Independent people, cross-machine
use and native Windows remain unverified.

## Source compatibility update (0.2.1)

The shared v2 check summary now stores `command_sha256` for canonical `{argv,cwd}`;
full argv remains in ignored local evidence. Existing v2 argv records remain readable,
and missing legacy actor fields remain unknown. `check` flags absolute paths in legacy
command arguments; owners must review any historical migration rather than expecting
an automatic rewrite. Task bindings now retain the prepared branch; legacy bindings
recover it from their local packet when available. An unavailable branch observation or a branch conflict requires reviewed
`prepare --rebind` before execution. Explicit rebind can recover an unreadable old local packet.

Runtime changes require a reviewed toolchain-lock and fixed-installation upgrade. The
host results below are historical 0.2.0/0.1.3 evidence; they do not certify a newer
artifact's host session or a real multi-member pilot.

## Session acceptance: `resume` from a teammate's branch (0.2.0, 2026-10-18)

A synthetic project committed the Codex and Claude skill copies (members install
nothing). Alice prepared `pr:8`, verified, handed off, committed the task
directory, then made one more commit, so her evidence no longer matched the
code. Each host started a fresh, read-only, non-interactive session in its own
`git clone -b alice/subtract` with no `.team-workflow/local/`, and got the same
prompt: report the previous handoff's next step, which acceptance criteria are
open and why, and the first thing to do.

| Host | Command | Result |
| --- | --- | --- |
| Claude Code 2.1.296 | `claude -p`, tools limited to the skill CLI plus Read/Glob/Grep | `PASS`: loaded the project skill, ran `resume` first (6 turns) |
| Codex 0.163.0 | `codex exec --sandbox read-only --ephemeral` | `PASS`: read `SKILL.md`, ran `resume` and the `verify` preview |
| Pi 1.1.0 | `pi -p --no-session --tools read,bash` | `PASS`: read `SKILL.md`, ran `resume` and the `verify` preview |

All three quoted the handoff's next step, reported AC-1 as pending because the
evidence was recorded for older code (not a failed test), AC-2 as needing human
review, and named `verify: unit` as the first step. No clone was modified.
Artifact: `team-workflow-craft-0.2.0.zip`, SHA-256
`1e9fe3d4b8f6aaa656d221113334324e684c94643466ed32cc3b8c9d2e9430ea`, macOS 27 arm64.

The first round failed in all three hosts: `base_ref = "main"` did not resolve in
a branch-only clone that has `origin/main` but no local `main`. The models worked
around it, but the tool was wrong. `resolve_base` now falls back to the single
remote-tracking branch, reports `base_ref_resolved`, and `doctor --local` checks
it. After the passing round, check states that have records for older code were
renamed from `missing` to `stale` because one model read `missing` as "never
ran"; this changes labels only.

Limits: one synthetic task with synthetic identities and the hosts' default
models. This does not replace a real multi-member pilot with real platform
accounts, PRs and review.

## Discovery acceptance and limits

The native discovery checks dated 2026-10-16 used macOS 27.0.1 arm64, temporary
Git projects, and the same
v0.1.3 ZIP with SHA-256
`665eef181d93c2844cb843075152bbfd977bdc20b8b53168d9ee1d40c745aa65`.
Each installation came from the fixed artifact, not a link to the source tree.
The temporary projects and probe processes were removed after the checks.

The probes exercised the installed host loaders without sending a model task:

- Codex: `codex debug prompt-input '$team-workflow-craft'`. The native catalog
  uses root aliases; resolve the listed skill path through its root mapping and
  compare it with the project installation. The literal user mention alone is
  not discovery evidence. This debug command is specific to the tested version.
- Claude Code: a stream-JSON `initialize` control request returned
  `team-workflow-craft` with a `(project)` description. The probe used an isolated
  config directory, project-only settings, disabled hooks, an empty strict MCP
  configuration, and no user prompt. It did **not** use `--bare`: that mode skips
  normal skill auto-discovery. [Claude Code programmatic usage](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)
- Pi: native RPC `get_commands` returned `skill:team-workflow-craft` with
  `source: skill`, project scope and the installed `SKILL.md` path;
  `get_messages` returned an empty conversation. The probe used isolated agent
  state, offline mode, and disabled extensions/MCP, with no `prompt` request.

These are **metadata discovery** results. These probes alone leave full
Skill-body invocation, model-led `doctor` / `prepare` / `verify` / `handoff`,
real cross-person handoff and other OS/host versions `UNVERIFIED`; the session
acceptance sections above provide their separate, bounded evidence. The probes
do not certify the user's existing sessions or other members' installations.
No paid model task, company code, or company platform credentials were supplied
to these probes. Package runtime checks and real platform API acceptance remain
separate evidence.

Native Windows verification remains intentionally incomplete in v0.2.2: the runner
cannot certify process-tree completion and records
`incomplete / process_tree_completion_unverified` rather than `passed`.
Use a POSIX development/CI environment for the complete verification workflow;
native Windows installation, discovery and process-tree support require a
separate platform acceptance pass. POSIX group checks do not certify commands
that deliberately daemonize or escape their process group.

## What the checked paths mean

OpenAI’s current guidance describes repo-local skills under `.agents/skills/`,
with `SKILL.md` plus optional scripts, references, and assets. It also describes
progressive loading, so a file path is not proof that an already-running Codex
session has discovered the Skill. [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)

Claude Code documents project skills at `.claude/skills/<name>/SKILL.md` and
direct invocation as `/<name>`. Claude Code’s own discovery, configuration, and
session state remain outside this package. [Claude Code: Extend Claude with
skills](https://code.claude.com/docs/en/skills)

Pi documents `.agents/skills/` as a supported project location and
`/skill:name` as the explicit command. It scans locations at startup, so a
real Pi acceptance check must inspect the startup diagnostics or invoke the
skill after installation. [Pi skills documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md)

## Fixed artifact contract

`python3 scripts/build.py --output-dir <directory>` writes only to the
specified directory:

```text
workflow-craft-<VERSION>.zip
workflow-craft-<VERSION>.zip.manifest.json
```

The JSON sidecar is `workflow-craft.artifact.v1`. It records the artifact
filename, artifact SHA-256, archive prefix, version, and SHA-256/size for every
runtime source file. Python bytecode caches are excluded. The ZIP has a fixed entry order, timestamps, permissions, and
compression settings for reproducible builds with the same Python/zlib toolchain.

`python3 scripts/install.py --artifact <zip> --project <project> --host
<codex|claude|pi>` is a dry run unless `--apply` is present. `--target
<skill-path>` is available for an exact non-global target. Installation checks
the ZIP and sidecar, rejects traversal, symlinks, unexpected or missing files,
and only permits a byte-for-byte identical known installation to be reused. A
drifted or unknown target is never overwritten. A known, unchanged older
installation needs both `--allow-upgrade` and `--apply`; the installer stages
the new directory before replacing the known target.

The generated `.twc-install.json` is an installation marker. It identifies the
artifact and manifest digests, but does not claim the artifact was released,
the host loaded it, or a session invoked it.
