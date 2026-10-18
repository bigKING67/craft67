# Team Workflow Craft

面向多人、Claude Code / Codex / Pi 混用的软件协作 Skill：统一任务契约、验证证据与交接，让任务换人、换 Agent 后仍能接续。

## 解决什么问题

同一个任务会在不同成员、Claude Code / Codex / Pi 之间流转。容易出问题的不是写代码本身，而是这三件事：

1. **任务说的是同一件事**：目标、范围、验收和公共接口来自平台 Issue 和仓库内的版本化契约，不靠聊天记录转述。
2. **"测过了"有据可查**：验证证据绑定当时的 base/head、未提交内容、命令和策略；代码或基线一变，旧证据自动失效。
3. **接手的人能直接继续**：交接写清做完了什么、还剩什么、有哪些未知和阻塞，接手者用自己的身份重新核对。

TWC 只做这三件事的确定性检查，载体是随任务分支提交的 `.team-workflow/tasks/<task>/` 目录：契约、证据摘要和最新交接都在里面，推送分支就是交接。任务分配、评审、合并留在 CNB/Gitea 和 Git；模型、Agent 进程和聊天上下文留在各宿主。并行尝试使用普通分支、独立 clone 或 `git worktree`，TWC 只负责检查整个 Git 根，提醒 WIP 互相覆盖。

**当前为源码 v0.2.0，非正式 Release。** 核心 CLI、CNB/Gitea 只读客户端和三宿主的项目内 Skill 发现已经验证；真实多人试点、已有 Issue/PR 的成功读取路径和模型任务尚未验收。Windows 原生进程树完成性不支持，返回 incomplete。各轮验收记录见 [试点与运维验收](docs/operations.md)、[宿主兼容性](docs/compatibility.md)、[CNB 首轮演练](docs/cnb-pilot.md) 和 [分支保护验收](docs/gitea-policy-probe.md)。

## 使用边界

- 小任务直接按项目规范完成，不要求新 Issue、文档、子 Agent 或 CLI。
- 普通协作记录目标、范围、验收与接手信息；多人改变接口时才增加分工、共享契约和集成负责人。
- 风险与人数分开。一个人修鉴权仍需高强度验证；多人改普通界面不自动启动完整审计。
- 不需要 Trellis，默认就是独立模式。项目已经在用 Trellis 时只选一个流程控制者：TWC 只提供检查、证据和交接，不维护另一套任务状态；团队里没装 Trellis 的成员照样可以用 TWC。
- 不调用模型、不管理模型 Key/Agent 进程、不启动常驻服务、不自动提交/推送/合并/部署。

## 快速开始

依赖 Python 3.11+、Git；无 Python 第三方运行依赖。以下从本包目录执行。源码入口是 `skills/team-workflow-craft/scripts/twc.py`；独立安装后替换成实际安装路径。

成员拿到安装副本后，先做只读的本机预检。它在 `init` 之前也可运行，不联网、不执行项目检查，缺项时退出 1 并给出 `next_steps`：

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product doctor --local
```

项目还没有配置时，检查已有 Git 仓库与批准的协作平台，预览最小配置：

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product init --dry-run \
  --provider cnb --base-url https://cnb.cool --repository company/product --base-ref origin/main
```

核对预览后用 `--apply` 替代 `--dry-run`。只创建 `.team-workflow/config.toml`、`toolchain.lock.json` 和忽略 `local/` 的 `.gitignore`，不改 AGENTS.md/CLAUDE.md、宿主账号或配置。现有 `.team-workflow` 会拒绝覆盖。base_ref 必须在本地可解析；不会隐式 fetch。

把项目已批准检查写入配置（命令需匹配真实项目）：

```toml
[checks.unit]
argv = ["python3", "-m", "unittest", "discover", "-s", "tests"]
cwd = "."
timeout_seconds = 300
```

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product doctor
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product prepare --task issue:42 --contract docs/task-42.json
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product resume
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product verify
```

`prepare` 把契约记到 `.team-workflow/tasks/issue-42/task.json`，验收条件自动编号为 AC-1、AC-2…。这个目录随任务分支提交，之后的证据摘要和交接也写在这里。`resume` 是每个会话的开场命令：只读，列出每条验收条件的状态、证据是否仍对应当前代码、上次交接的下一步和 `next_actions`。

联网时通过公司批准的秘密管理工具提供 `TWC_CNB_TOKEN` 和 `TWC_CNB_IDENTITY_TOKEN`（Gitea 使用 `TWC_GITEA_TOKEN`），只使用所需的只读权限。CNB 的端点、权限与检查边界见 [CNB 接入](skills/team-workflow-craft/references/cnb.md)；Gitea 沿用 [Gitea 接入](skills/team-workflow-craft/references/gitea.md)，初始化显式用 `--provider gitea`。不要把 Token 放命令行、配置或 URL。`doctor --online` 检查身份、仓库及可用版本信息；CNB SaaS 版本为 unsupported；`prepare --offline` 可在网络不可用时保留未知状态。

`verify` 默认仅预览。已有授权覆盖当前检查和副作用后，用预览的策略哈希执行：

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product verify \
  --execute --approved-policy <policy_sha256> --online
```

命令记录真实时间、退出码、base/head、代码内容哈希、策略、契约版本及工具版本。完整记录留在本地 ignored 目录，任务目录里另写一份可提交的摘要。配置哈希只是把执行绑定到已审阅命令，不构成批准来源；输出只存摘要哈希和字节数，避免把潜在凭据日志写入交接。未运行/失败/超时/内容漂移不会通过。

每人首次配置个人 Git 姓名/邮箱和个人平台凭据，随后自动记录执行者。任务负责人、Git 作者、验证者、交接者和合并者分别追踪；换人不会沿用旧身份，离线也不会猜测账号。接入步骤见 [成员身份](skills/team-workflow-craft/references/identity.md)。

契约按 [任务模板](skills/team-workflow-craft/assets/templates/task-contract.json) 填写，`prepare --contract <repo-relative.json>` 引用；已有规格（包括 Trellis 的 prd.md）放进 `contracts` 引用，不复制。验收条件写成 `{"text": "…", "checks": ["unit"]}` 时，所列检查在当前代码上都通过才算 verified；纯文字的验收条件留给人判断。不要填第二份 owner/status。

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product handoff --draft --online \
  --done "已实现并验证接口" --next "集成负责人核对组合测试和审批"
git add -- .team-workflow/tasks/issue-42
git commit -m "twc: hand off issue-42" -- .team-workflow/tasks/issue-42
```

交接写入任务目录的 `handoff.json/md`，未验证的验收条件自动列入 remaining，占位文本会被拒绝。平台未刷新时 `unknown`，未提交工作、陈旧证据等为 `not_ready`；`--online` 可重新读 PR。`advisory_ready` 仅表示材料可供人工集成审查，永远不是合并授权。提交任务目录并推送分支后，接手者 clone、切到该分支、运行 `resume` 即可继续，不需要对方的任何本地文件。提交一律带 pathspec，避免把别的会话暂存的文件带进来。

## 命令

| 命令 | 行为 |
| --- | --- |
| `doctor [--local/--online]` | `--local` 为 init 前可用的本机预检；默认检查整个 Git 根、配置/版本锁、项目安装入口；`--online` 追加只读平台诊断 |
| `init [--dry-run/--apply]` | 预览或创建最小配置，不覆盖已有配置 |
| `prepare --task issue:N/pr:N` | 记录契约到任务目录、获取本地平台快照、绑定当前工作区；契约变化需 `--update-contract`；不认领/回写任务 |
| `resume` | 只读开场视图：验收条件状态、证据新鲜度、上次交接、之后的提交和 `next_actions` |
| `workspace inspect/create` | 全根 WIP 检查；并行尝试时预览并创建指定路径/分支的 worktree |
| `verify` | 默认计划；显式执行项目已批准命令，产出绑定代码内容的证据，并在任务目录写可提交摘要 |
| `handoff --draft` | 在任务目录写交接与建议状态；`--publish` 不支持 |
| `check` | 确定性检查已提交的任务目录，适合放进 CI |

## 固定构建与项目安装

唯一安装产品为 `skills/team-workflow-craft/`，外层开发工具不参与运行。不会自动安装本仓库里的全部 Craft，也不会自动升级 latest。

```sh
python3 scripts/build.py --output-dir /path/to/approved-artifacts
python3 scripts/install.py --artifact /path/to/approved-artifacts/team-workflow-craft-0.2.0.zip \
  --project /path/to/product --host codex
# 核对目标、产物和来源后加 --apply；Claude 用 --host claude，Pi 用 --host pi。
```

安装器校验 ZIP/文件哈希，拒绝未知、漂移或 symlink 目标；固定版本重复安装幂等。只支持明确项目目标，正常升级需要检查旧安装无漂移并显式 `--allow-upgrade --apply`。ZIP 与清单必须来自批准来源：攻击者同时换掉二者时，本地哈希无法验证真实性。

Codex/Pi 使用 `.agents/skills/team-workflow-craft/`；Claude 使用 `.claude/skills/team-workflow-craft/`。

**推荐：负责人装一次，提交进仓库。** 负责人分别用 `--host codex` 和 `--host claude` 安装，然后把这两个目录和 `.team-workflow/` 一起提交。成员 clone 后即可使用，只需要 Python 3.11+ 和 Git，不用另装 TWC，也不需要 Trellis。`doctor --local` 会核对 clone 下来的副本是否与安装清单一致。升级时由负责人 `--allow-upgrade --apply` 后提交，成员 pull 即可。项目若忽略了 `.claude/`，需要为 `.claude/skills/team-workflow-craft/` 加一条例外规则。宿主规则尽量共用 AGENTS.md，Claude 如需 `CLAUDE.md` 导入由项目显式配置。工具不修改它们。三宿主发现路径、实际加载和独立包证据见 [兼容性](docs/compatibility.md)。

## 开发与验收

```sh
python3 scripts/check.py
# craft67 根：
python3 scripts/check.py --package team-workflow-craft
```

门禁覆盖临时 Git 工作区、受控 CNB/Gitea HTTP 模拟器、失败/漂移、安装保护及真实运行时独立包测试；不使用公司账号或付费模型。根 catalog 接入离线 CI，不能替代受控 CI、宿主或目标平台实测。

进一步说明：[架构与数据合同](docs/architecture.md)、[成员接入](docs/member-onboarding.md)、[试点与运维验收](docs/operations.md)、[隔离分支保护验收](docs/gitea-policy-probe.md)、[可选 Gitea 部署方案（AIOS 已停用）](docs/gitea-vps.md)、[AIOS 接入与发布来源切换建议](docs/aios-adoption.md)、[来源与许可](docs/upstreams.md)、[版本变更](CHANGELOG.md)。MIT；未复制 Trellis/OpenSpec 的代码或模板。
