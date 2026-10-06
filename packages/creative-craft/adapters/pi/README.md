# Pi adapter

Pi is a Tier 1 host. `package.json.pi.skills` points to the canonical runtime;
the adapter does not copy or fork core rules.

Install the immutable GitHub release globally or for one project:

```bash
pi install git:github.com/bigKING67/creative-craft@v0.3.0
pi install -l git:github.com/bigKING67/creative-craft@v0.3.0
```

These commands remain pinned to the latest published immutable tag. Pi package
discovery and installed-runtime behavior are covered by the release gates.

Validate discovery with `pi list`, then run the installed
`skills/creative-craft/scripts/creative_craft.py self-test --json` command when
diagnosing a package copy. No npm registry package is published.

## Work from this source checkout

The repository's `.pi/settings.json` declares `../skills/creative-craft` as a
project resource. Pi resolves that path from `.pi/`, so it selects the canonical
source Skill without copying it into a user directory. Start Pi from the
repository root and trust this checkout for the run:

```bash
pi --approve
```

No `--skill` flag is needed. The project resource takes precedence over a
same-named user Skill; ignoring project resources with `--no-approve` leaves
the user resource layer responsible for selection. Project settings apply to Pi's working
directory, so this declaration does not activate the checkout in other projects.
It does not change the user's provider, model, packages or shared Skill files.

Use `/skill:creative-craft` to invoke it explicitly, or ask for the matching
creative task in natural language. For a discovery diagnosis, RPC
`get_commands` reports the actual `skill:creative-craft` source path and scope;
`pi list` reports packages and is not evidence of which same-named Skill won.
Viewing exported PNGs requires a model that accepts image input.

The optional image executor lives in `integrations/image-production/`, outside
the released Skill package. Install its dependencies and bind a supported font
according to its README before using editable image projects. The Agent uses
Pi's existing file/Bash tools to call that CLI; there are no new registered
extension tools or additional Agent loop. Keep package discovery, source
discovery, a real model session and packaged Desktop acceptance separate.

For cross-project use, an explicitly authorized user configuration can add the
absolute checkout Skill directory to `~/.pi/agent/settings.json`'s `skills`
array. Pi then discovers it as a user resource outside this repository; keep
the checkout available at that path. This selects development source and does
not update a shared Skill directory or install the optional executor. Preserve
all other settings and keep a settings backup before applying that delta.

On 2026-10-04 this exact delta was authorized and applied locally. A real Pi
RPC probe from a temporary working directory outside the checkout, with project
resources ignored and no `--skill`, selected the source Skill at user scope.
The existing default model and all unrelated configuration/shared files stayed
unchanged. Evidence:
`dist/image-global-activation-2026-10-04-6c060829/activation-receipt.json` and
`global-discovery-report.json`. This zero-model-call discovery probe does not
cover a full extension set or packaged Desktop execution.

A subsequent real-user-settings model session edited a copied product project
outside the repository, with project resources ignored and no explicit Skill
or executor path in the task. Pi located the source tools, moved two text
objects in one batch, inspected three actual PNGs, undid the edit and completed
the handoff. Pixel, source, configuration and relocated reopen checks passed.
Evidence: `dist/image-pi-cross-workspace-2026-10-04-8021ff3a/acceptance-report.json`.
Unrelated extensions/context/themes stayed disabled for this bounded sample;
complete daily extension and Desktop behavior remain separate acceptance work.

The shared Skill was subsequently upgraded under separate explicit
authorization: eight files updated, seven added, all 90 content files equal to
source, with a complete old-directory backup and passing installed self-test.
An external-cwd Pi CLI 1.0.0 RPC probe with isolated empty agent resource
settings automatically discovered `~/.agents/skills/creative-craft/SKILL.md`
as auto/user/top-level. A separate probe using the real user settings continued
to select the configured development source as local/user/top-level; the
default model and five protected Pi/Codex configuration/auth files stayed
unchanged. Neither probe supplied `--skill` or submitted a model task. Evidence:
`dist/shared-skill-upgrade-2026-10-04-5bda3972/host-discovery-report.json`.
The controlled RPC processes were terminated after their responses; exit 143
is that termination, not a failed creative task. Shared discovery does not
bundle the optional image executor or replace a model-session/complete-extension
acceptance. This local installation is an unreleased candidate.

The current enabled extension configuration was also exercised on 2026-10-04,
without the earlier resource-disable flags. The invocation kept memory
read-only and used only existing read/Bash/write tools on a copied product
project outside the checkout. Native RPC registered 28 extension commands and
selected the configured source Skill. A bounded edit/undo model session then
passed pixel, project, relocated reopen and all five configuration/auth guards
plus shared-tree parity in 233.986 seconds, with three actual image reads and
normal handoff. Evidence:
`dist/image-pi-daily-2026-10-04-e32f1850/acceptance-report.json`.

Keep the previous attempt under
`dist/image-pi-daily-2026-10-04-f4c86e31/`: its image checks passed, but Codex
configuration drift failed the preservation gate and remains unattributed.
Four existing package dependency-declaration startup warnings remain in both
samples; warning classification does not remove them or turn the first sample
into a pass. The repeat is image-workflow acceptance under the current enabled
resources, not individual extension-tool or memory-write acceptance. Packaged
Desktop inspection stopped at a Computer Use native-pipe failure; CLI success
does not establish Desktop/AIOS/Windows execution. See the [host record](../../docs/content-production-architecture.md#当前启用扩展的图片操作与-desktop-阻塞).
Closeout observed a separate source branch/HEAD change and one newly different
video reference in the shared installation. The image entrypoint/reference
still match the observed session; do not infer full-current-source install
parity from the earlier install receipt. See the repeat's
`source-drift-closeout.json` before any later replacement.

On 2026-10-05 the new `create-photo` entry was exercised with the actual daily
default `deepseek/deepseek-flash`, thinking `high`, outside the checkout and
without Skill, executor or model flags. Pi read the source Skill/guide, created
a project, changed only its headline, undid that edit and viewed all three PNGs.
Each export preserved the entire 1,572,516-pixel photo; relocation/re-rendering
and configuration/source guards passed. The passing repeat used an invocation-only
macOS write sandbox and task-local TMPDIR; native settings/auth lock paths were
allowed while configuration and credential files remained read-only. This
restriction is not installed into daily Pi. The first unrestricted attempt had
correct images but wrote temporary logs outside the task directory and remains
partial. Evidence and exact limits: photo-entry host acceptance (local evidence, not in repo: `../../dist/image-pi-photo-entry-2026-10-05-5f0d8a76/README.md`).

Historical image export was also exercised on 2026-10-05 with the configured
`deepseek/deepseek-flash`, without executor commands or revision numbers in the
task. Pi inspected history, selected the latest locked square and 9:16 layouts,
exported full images and previews, and viewed both full PNGs. Independent checks
matched saved PNG bytes, all 1,572,516 photo pixels and the selected receipts;
the copied/original project trees, source, shared Skill and five global
configuration/auth files stayed unchanged. Current revision remained 12.
Image delivery passed, but the clean-host gate remains **PARTIAL**: two sandbox
shell errors and one initially masked Sharp import error were recovered during
the run. Preserve those observations; subsequent script guidance is not a
second successful Pi run. No global runtime was changed. See the
history-export host record (local evidence, not in repo: `../../dist/image-pi-history-export-2026-10-05/README.md`).

A second bounded invocation used the same task, model, thinking and limits after
the guide update. It completed in 53.066 seconds with 18 turns and 22 tool calls;
the three earlier process errors did not recur. Image output, receipt bindings,
pixel fidelity and project/configuration preservation passed again. This is not
an unrestricted or fully clean-host certification: a temporary JSON reserialization
hash mismatch was corrected, and an executor search traversed the repository
without excluding old `dist` artifacts. Image delivery is PASS; the strict read
scope remains PARTIAL. The original partial run is retained. See the
repeat and manual scope review (local evidence, not in repo: `../../dist/image-pi-history-export-repeat-2026-10-05/README.md`).
