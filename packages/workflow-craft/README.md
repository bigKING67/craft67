# Workflow Craft

个人或团队共用的任务、验证与接续流程。正式包名和 Skill 调用名为 `workflow-craft`（原 `team-workflow-craft`）。已有 `.team-workflow/` 数据、`TWC_*` 环境变量和 `twc.py` 命令路径保留兼容。

面向个人或团队、Claude Code / Codex / Pi 混用的软件工作流 Skill：统一任务契约、验证证据与交接，让任务换人、换 Agent 后仍能接续。

本版明确与项目 `AGENTS.md` / `CLAUDE.md` 分工：项目约定继续生效，Workflow Craft 只补任务接续、验证证据与交接，不自动改写规则文件。详细命令按需加载；关键功能先复用已有测试和操作说明，再补真实覆盖缺口，见 [功能验证路径](skills/workflow-craft/references/feature-verification.md) 与 [本包验证索引](docs/verification-paths.md)。

产品目标包含独立承接个人和团队的完整任务循环。0.5.0 已实现最小本地任务树、生命周期与会话绑定；针对已有 Trellis 项目的 [替代与退役验收方案](docs/trellis-retirement.md) 和只读盘点工具继续适用。AIOS 隔离副本已完成局部真实修复及 Windows/Claude → Mac 接续；完整真人平台协作与原项目迁移尚未验收，当前不能退役 AIOS 的 Trellis。

可选 [模式状态栏](skills/workflow-craft/references/statusline.md) 支持 Claude Code 和 Pi，显示 `Workflow: solo` / `Workflow: team`；配置缺失或错误会如实显示。适配器随固定产物提供，须显式启用并保留原状态栏；Codex 继续用接续开场提示。显示模式不代表检查或审批通过。

## 解决什么问题

同一个任务会跨越多个会话，也可能在不同成员、Claude Code / Codex / Pi 之间流转。容易出问题的不是写代码本身，而是这三件事：

1. **任务说的是同一件事**：目标、范围、验收和公共接口来自项目契约，平台任务关联 Issue 和引用规格，不靠聊天记录转述。
2. **"测过了"有据可查**：验证证据绑定当时的 base/head、未提交内容、命令和策略；代码或基线一变，旧证据自动失效。
3. **接手的人能直接继续**：交接写清做完了什么、还剩什么、有哪些未知和阻塞，接手者用自己的身份重新核对。

这些事实保存在随任务分支提交的 `.team-workflow/tasks/<task>/` 目录：契约、本地执行进度、证据摘要和最新交接都在里面。平台任务的分配、评审、合并留在 CNB/Gitea 和 Git；模型、Agent 进程和聊天上下文留在各宿主。并行尝试使用普通分支、独立 clone 或 `git worktree`，工具检查整个 Git 根并保留 WIP 边界。

**当前为源码 v0.7.1，非正式 Release。** 本版修复原生 Windows 新生成任务、证据和交接文件的换行：统一写 UTF-8/LF，保留历史记录原字节。0.7.0 新增了显式全局安装和项目固定版本引导。全局入口负责首次接入；已有项目继续使用自己的固定运行时，全局升级不会改动项目模式、规则、锁或历史。0.6.3 的配置字节保护修复已完成真实 Windows→Mac 接续及六组平台 CI；各版本的独立验证范围见 [兼容性记录](docs/compatibility.md)。

模式按项目首次明确选择，后续复用并可显式切换；见 [开发模式](skills/workflow-craft/references/development-modes.md)。协议仍为 3，升级项目需匹配固定安装和工具链锁；全局安装不自动升级项目。写入锁和验证进程管理支持 POSIX 与原生 Windows。历史候选的宿主结果不代表当前版本的自动发现或模型行为已验收。

0.4.1 收敛了流程触发、重验时机与集成边界：多文件修改不自动建任务；接续时按需要安排检查，部分通过不掩盖其他过期证据；项目原有合并队列/CI 继续生效。本版通过 163 项离线测试，以及三个使用固定安装副本的 Codex 规则兼容场景。它们验证了上述行为，没有证明所有宿主或任意规则组合都能兼容；见 [本轮验收](docs/compatibility.md#041-project-rule-cooperation-acceptance-2026-10-30)。

此前 0.4.0 通过 162 项离线包测试、版本与 Skill 静态检查；固定产物独立重建一致。Pi 1.4.0 已通过原生扩展加载、RPC 模式切换和终端状态栏显示验收，未调用模型。Claude Code 已验证 stdin 命令合同，原生界面显示及现有状态栏组合尚未验收；该轮未进行新的 Skill 模型行为评估。完整范围见 [宿主兼容性](docs/compatibility.md#040-workflow-references-and-optional-status-adapters-2026-10-30)。

此前 0.3.1 通过 151 项包测试、23 项根元数据测试，以及固定 0.3.0 安装副本的改名迁移与重验；任务、模式、署名和证据保留。此前 0.3.0 的 Codex 受控只读新会话已验证主动询问个人/团队、复用名字、不索要邮箱、不擅自初始化；该会话不代表新名称的宿主加载。这些历史样本未覆盖自动发现、全局安装与独立成员验收，具体版本与范围见 [宿主兼容性](docs/compatibility.md)。

历史 0.2.2 CNB 合成试点覆盖同机双账号接手、负责人评审普通合并及 main 全新 clone 的 9 项测试。2026-10-28 补测中，Claude Code 2.1.308 与 Pi 1.4.0 均完成受控只读接手；Pi 复验明确限制只使用当前仓库资料。Pi 的模型适配修复、原生重试恢复的连接错误和建议措辞限制见 [宿主兼容性](docs/compatibility.md)。独立真人与跨机器仍待验收。0.6.0 在 Windows 使用 Job Object 管理普通子进程；作业创建/分配失败、超时、取消或残留进程均不能通过。历史宿主结果保留各自日期与版本。

核心 CLI、CNB/Gitea 只读客户端已经验证。AIOS 已在 Trellis 托管模式下接入，检查登记为 `npm run verify:quick`，随 AIOS 4.1.106 发布。更早的平台证据见 [CNB 首轮演练](docs/cnb-pilot.md) 和 [分支保护验收](docs/gitea-policy-probe.md)。

## 使用边界

- 是否建立任务取决于持久接续/交接需求；当次可完成的多文件修改也可直接按项目规范完成，不要求新 Issue、文档、子 Agent 或 CLI。
- 复用项目已有目标、范围、验收与接手信息，只补接续缺口；多人改变接口时才增加分工、共享契约和集成负责人。
- 风险与人数分开。一个人修鉴权仍需高强度验证；多人改普通界面不自动启动完整审计。
- 不需要 Trellis，默认就是独立模式。项目已经在用 Trellis 时只选一个流程控制者：TWC 只提供检查、证据和交接，不维护另一套任务状态；团队里没装 Trellis 的成员照样可以用 TWC。
- 不调用模型、不管理模型 Key/Agent 进程、不启动常驻服务、不自动提交/推送/合并/部署。

## 快速开始

依赖 Python 3.11+、Git；无 Python 第三方运行依赖。以下从本包目录执行。源码入口是 `skills/workflow-craft/scripts/twc.py`；独立安装后替换成实际安装路径。

成员拿到安装副本后，先做只读的本机预检。它在 `init` 之前也可运行，不联网、不执行项目检查，缺项时退出 1 并给出 `next_steps`：

```sh
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product doctor --local
```

项目尚未配置时，Agent 先询问个人或团队；推荐个人不等于自动选择。个人模式在已有提交的 Git 仓库中直接预览并应用：

```sh
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product init --mode personal
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product init --mode personal --apply
```

个人任务使用 `local:export-orders` 这样的标识，无需 remote、Issue 或 Token。后续可用 `mode --set team` 预览切换，按用户授权及返回策略哈希应用。团队如需平台，预览最小配置：

```sh
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product init --mode team --dry-run \
  --provider cnb --base-url https://cnb.cool --repository company/product --base-ref origin/main
```

核对预览后用 `--apply` 替代 `--dry-run`。只在 `.team-workflow/` 内创建 `config.toml`、`toolchain.lock.json`、忽略 `local/` 的 `.gitignore`，以及保护配置原始字节的 `.gitattributes`；初始化统一写 UTF-8/LF，提交配置时一并提交该属性文件。不改根 `.gitattributes`、AGENTS.md/CLAUDE.md、宿主账号或配置。现有 `.team-workflow` 会拒绝覆盖。base_ref 必须在本地可解析；不会隐式 fetch。已有项目的换行保护见[跨平台接续](skills/workflow-craft/references/development-modes.md#跨平台配置与已有项目)。

把项目已批准检查写入配置（命令需匹配真实项目）：

```toml
[checks.unit]
argv = ["python3", "-m", "unittest", "discover", "-s", "tests"]
cwd = "."
timeout_seconds = 300
```

```sh
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product doctor
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product prepare --task local:export-orders --contract docs/export-orders.json
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product resume
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product verify
```

`prepare` 把契约记到 `.team-workflow/tasks/issue-42/task.json`，验收条件自动编号为 AC-1、AC-2…。这个目录随任务分支提交，之后的证据摘要和交接也写在这里。`resume` 是接续已有 TWC 任务时的开场命令：只读，列出每条验收条件的状态、证据是否仍对应当前代码、上次交接的下一步和 `next_actions`。

联网时通过公司批准的秘密管理工具提供 `TWC_CNB_TOKEN` 和 `TWC_CNB_IDENTITY_TOKEN`（Gitea 使用 `TWC_GITEA_TOKEN`），只使用所需的只读权限。CNB 的端点、权限与检查边界见 [CNB 接入](skills/workflow-craft/references/cnb.md)；Gitea 沿用 [Gitea 接入](skills/workflow-craft/references/gitea.md)，初始化显式用 `--provider gitea`。不要把 Token 放命令行、配置或 URL。`doctor --online` 检查身份、仓库及可用版本信息；CNB SaaS 版本为 unsupported；`prepare --offline` 可在网络不可用时保留未知状态。

`verify` 默认仅预览。已有授权覆盖当前检查和副作用后，用预览的策略哈希执行：

```sh
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product verify \
  --execute --approved-policy <policy_sha256> --online
```

命令记录真实时间、退出码、base/head、代码内容哈希、策略、契约版本及工具版本。完整记录留在本地 ignored 目录，任务目录里另写一份可提交的摘要。配置哈希只是把执行绑定到已审阅命令，不构成批准来源；输出只存摘要哈希和字节数，避免把潜在凭据日志写入交接。未运行/失败/超时/内容漂移不会通过。

首次接入只需名字或团队称呼：`doctor --local` 和 `resume` 复用已有 Git `user.name`，缺失时提示提供名字，不要求邮箱。任务、验证和交接分别保留当时的称呼，离线也能显示，并标明平台身份未核验。实际 Git 提交、平台正式交接时再核对相应的完整身份；个人本地接续无需邮箱或平台账号。任务负责人、Git 作者、验证者、交接者和合并者分别追踪；换人不会沿用旧身份，离线也不会猜测账号。接入步骤见 [成员身份](skills/workflow-craft/references/identity.md)。

契约按 [任务模板](skills/workflow-craft/assets/templates/task-contract.json) 填写，`prepare --contract <repo-relative.json>` 引用；已有规格（包括 Trellis 的 prd.md）放进 `contracts` 引用，不复制。验收条件写成 `{"text": "…", "checks": ["unit"]}` 时，所列检查在当前代码上都通过才算 verified；纯文字的验收条件留给人判断。不要填第二份 owner/status。

```sh
python3 skills/workflow-craft/scripts/twc.py --project /path/to/product handoff --draft --online \
  --done "已实现并验证接口" --next "集成负责人核对组合测试和审批"
git add -- .team-workflow/tasks/issue-42
git commit -m "twc: hand off issue-42" -- .team-workflow/tasks/issue-42
```

交接写入任务目录的 `handoff.json/md`，未验证的验收条件自动列入 remaining，占位文本会被拒绝。平台交接未刷新时 `unknown`，本地任务不要求平台刷新；未提交工作、陈旧证据等为 `not_ready`；`--online` 可重新读 PR。`advisory_ready` 只表示对应 `readiness_scope` 的材料可供本地接续或平台人工审查，永远不是合并授权。提交任务目录并推送分支后，接手者 clone、切到该分支、运行 `resume` 即可继续，不需要对方的任何本地文件。提交一律带 pathspec，避免把别的会话暂存的文件带进来。

## 命令

| 命令 | 行为 |
| --- | --- |
| `entry --host codex/claude/pi [--apply]` | 只读选择项目固定副本；仅在明确接入时为新项目固定运行时，不初始化模式或升级已有项目 |
| `task list/create/start/pause/finish/complete/reopen/archive` | 只读列出或显式管理本地执行；写入要求会话 ID；不回写平台，Trellis 托管项目拒绝生命周期写入 |
| `mode [--set personal/team]` | 查看项目模式或预览切换；显式应用后保留记录，策略变化需要重验 |
| `doctor [--local/--online]` | `--local` 为 init 前可用的本机预检；默认检查整个 Git 根、配置/版本锁、项目安装入口；`--online` 追加只读平台诊断 |
| `init [--dry-run/--apply]` | 预览或创建最小配置，不覆盖已有配置 |
| `prepare --task local:<slug>/issue:N/pr:N` | 记录契约和绑定；本地任务不读平台，平台任务获取快照；契约变化需 `--update-contract`；不认领/回写任务 |
| `resume` | 只读开场视图：验收条件状态、证据新鲜度、上次交接、之后的提交和 `next_actions` |
| `workspace inspect/create` | 全根 WIP 检查；并行尝试时预览并创建指定路径/分支的 worktree |
| `verify` | 默认计划；显式执行项目已批准命令，产出绑定代码内容的证据，并在任务目录写可提交摘要 |
| `handoff --draft` | 在任务目录写交接与建议状态；`--publish` 不支持 |
| `check` | 确定性检查已提交的任务目录，适合放进 CI |

## 固定构建与项目安装

唯一安装产品为 `skills/workflow-craft/`，外层开发工具不参与运行。不会自动安装本仓库里的全部 Craft，也不会自动升级 latest。

```sh
python3 scripts/build.py --output-dir /path/to/approved-artifacts
python3 scripts/install.py --artifact /path/to/approved-artifacts/workflow-craft-0.7.1.zip \
  --project /path/to/product --host codex
# 核对目标、产物和来源后加 --apply；Claude 用 --host claude，Pi 用 --host pi。
```

安装器校验 ZIP/文件哈希，拒绝未知、漂移或 symlink 目标；固定版本重复安装幂等。项目与全局安装都必须明确目标，正常升级需要检查旧安装无漂移并显式 `--allow-upgrade --apply`。ZIP 与清单必须来自批准来源：攻击者同时换掉二者时，本地哈希无法验证真实性。

全局启用用同一固定产物，先预览，再在授权范围内加 `--apply`：

```sh
python3 scripts/install.py --artifact /path/to/approved-artifacts/workflow-craft-0.7.1.zip --global --host codex
```

Codex 与 Pi 共用 `~/.agents/skills/workflow-craft/`，Claude 写入 `~/.claude/skills/workflow-craft/`。检测到已知 Codex/Pi 另一条全局发现路径中的同名或旧名副本时，先核对迁移，不再增加重复安装。只安装选定入口，不改全局 AGENTS、CLAUDE、宿主配置或状态栏。已有同名未知/漂移安装拒绝覆盖；固定版本升级仍需 `--allow-upgrade`。宿主需重新发现 Skill，新会话可显式调用。进入具体项目后按 [全局入口与项目固定版本](skills/workflow-craft/references/development-modes.md#全局入口与项目固定版本) 选择副本，不用全局运行时直接管理项目任务。

Claude Code 在个人与项目目录存在同名 Skill 时优先加载个人副本，这是[宿主的名称解析规则](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name)。先加载全局 Skill 不等于已经使用项目固定版本：全局入口须先执行只读 `entry --host claude`，后续按返回的项目 `skill` / `cli` 工作。项目如维护入口指针，应区分 Claude 的 `.claude` 与 Codex/Pi 的 `.agents`；共用编码规则仍保留在原 AGENTS/CLAUDE 中。AIOS 的[原生接续演练](docs/aios-migration-rehearsal.md)保留了错误选路和修正后的实际样本，不能仅凭 Skill 名称或安装文件判断加载成功。

升级保留项目的旧工具链锁。先让所有项目宿主入口安装同一批准产物，再从新安装副本运行 `doctor --local`：安装完整性应为 `matched`，旧锁会显示 `mismatch`。核对批准的 ZIP SHA-256 与安装清单后，在已授权升级范围内，将 `.team-workflow/toolchain.lock.json` 的 `version`、`protocol_version`、`runtime_tree_sha256` 更新为本次诊断的 `runtime` 值，保留锁的其余字段；再次运行 `doctor --local`，确认所有入口与锁都匹配。不同内容需独立版本，不能用同版本覆盖绕过保护。历史任务和证据保留，涉及工具链变更的旧通过需重新验证。

Codex/Pi 使用 `.agents/skills/workflow-craft/`；Claude 使用 `.claude/skills/workflow-craft/`。调用分别为 `$workflow-craft`、`/skill:workflow-craft`、`/workflow-craft`。

从旧名迁移时仍使用新包安装器的 `--project ... --host ... --allow-upgrade` 先预览，再按授权加 `--apply`。它验证同目录旧安装清单和全部文件，迁移到新名称，并移除已核验的旧 Skill 副本，避免双重加载；漂移、未知副本、符号链接或新旧名称并存会拒绝。项目 `.team-workflow/`、AGENTS.md、CLAUDE.md 和其他 Skill 不变；旧锁需按上文另行核对升级，`skill` 标识可同步更新为 `workflow-craft`。现有用户安装不会随源码改名自动迁移。

**推荐：负责人装一次，提交进仓库。** 负责人分别用 `--host codex` 和 `--host claude` 安装，然后把这两个目录和 `.team-workflow/` 一起提交。成员 clone 后即可使用，只需要 Python 3.11+ 和 Git，不用另装 TWC，也不需要 Trellis。`doctor --local` 会核对 clone 下来的副本是否与安装清单一致。升级时由负责人完成上述安装、工具链锁核对与更新后提交，成员 pull 后再做本地预检。项目若忽略了 `.claude/`，需要为 `.claude/skills/workflow-craft/` 加一条例外规则。宿主规则尽量共用 AGENTS.md，Claude 如需 `CLAUDE.md` 导入由项目显式配置。工具不修改它们。三宿主发现路径、实际加载和独立包证据见 [兼容性](docs/compatibility.md)。

## 开发与验收

```sh
python3 scripts/check.py
# craft67 根：
python3 scripts/check.py --package workflow-craft
```

门禁覆盖临时 Git 工作区、受控 CNB/Gitea HTTP 模拟器、失败/漂移、安装保护及真实运行时独立包测试；不使用公司账号或付费模型。根 catalog 接入离线 CI，不能替代受控 CI、宿主或目标平台实测。

进一步说明：[架构与数据合同](docs/architecture.md)、[成员接入](docs/member-onboarding.md)、[试点与运维验收](docs/operations.md)、[隔离分支保护验收](docs/gitea-policy-probe.md)、[来源与许可](docs/upstreams.md)、[版本变更](CHANGELOG.md)。AIOS 的 CNB 接入方案和已停用的 Gitea 自托管方案已迁到 AIOS 仓库（`docs/CNB_TEAM_ADOPTION.md`、`docs/archive/gitea-vps/`）。MIT；未复制 Trellis/OpenSpec 的代码或模板。
