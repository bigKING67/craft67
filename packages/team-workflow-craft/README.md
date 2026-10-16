# Team Workflow Craft

面向多人、Claude Code / Codex / Pi 混用的软件协作 Skill。CNB 或 Gitea 保存任务、分配与 PR；成员在自己的开发环境执行；TWC 帮助统一任务契约、工作区检查、验证证据与交接。

**当前为源码 v0.1.3，非正式 Release。** 已实现可离线验证的核心与 CNB/Gitea 只读客户端，早期 Gitea 曾完成 HTTPS 实例读取、独立 VPS 部署及加密异机备份的隔离恢复；该试点实例现已停用，AIOS 改用 CNB 私有空仓库。恢复范围包括账号、组织、空仓库及保护规则；项目代码、Issue/PR/附件恢复和真实多人协作仍待验收。完整验证执行先面向 POSIX 开发环境；Windows 原生进程树完成性尚不支持，明确返回 incomplete。

另在一次性恢复副本中通过 17 项真实 Git/REST 场景，覆盖 main 保护、独立审批、最新基线和只读适配器。使用合成代码与临时账号，不等于真实团队试点；仅更新基线时平台可保留旧内容审批，集成仍须重新验证并确认当前 head。

CNB v0.1.3 已用最小权限凭据完成真实账号、私有仓库及打包后 `doctor --online` 读取；账号专用 Token 读取私有仓库被拒绝。仓库仍为空，不存在资源的 404 分类已验证，但已有 Issue/PR/review/status 的成功路径和双账号合并权限尚未验收。包级 89 项检查与独立资料包安装通过；这些结果不代表 AIOS 代码已迁入或生产来源已切换。

2026-10-16 在 macOS 27.0.1 arm64 临时项目中，同一 v0.1.3 产物通过 Codex 0.162.1、Claude Code 2.1.296、Pi 1.1.0 的原生 Skill 发现检查。此次没有模型任务，只证明宿主识别了项目入口；正文调用和完整协作流程仍待实测。方法、产物哈希和边界见 [兼容性记录](docs/compatibility.md)。

另通过三份独立 clone 的完整 CLI 验收：换人后分别记录历史验证者与当前操作者；主分支前进时拒绝复用旧证据；两边各自通过但组合失败时记录失败，修复后重新验证再由集成者更新本地测试远端。该用例使用合成代码、模拟成员身份和本地 Git，不调用宿主模型或公司平台，不能替代真实多人试点。

## 使用边界

- 小任务直接按项目规范完成，不要求新 Issue、文档、子 Agent 或 CLI。
- 普通协作记录目标、范围、验收与接手信息；多人改变接口时才增加分工、共享契约和集成负责人。
- 风险与人数分开。一个人修鉴权仍需高强度验证；多人改普通界面不自动启动完整审计。
- 已有 Trellis 时只选一个流程控制者。TWC 可只提供检查、证据和交接，不维护另一套任务状态。
- 不调用模型、不管理模型 Key/Agent 进程、不启动常驻服务、不自动提交/推送/合并/部署。

## 快速开始

依赖 Python 3.11+、Git；无 Python 第三方运行依赖。以下从本包目录执行。源码入口是 `skills/team-workflow-craft/scripts/twc.py`；独立安装后替换成实际安装路径。

先检查已有 Git 仓库与批准的协作平台，预览最小配置：

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
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product workspace inspect
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product prepare --task issue:42
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product verify
```

联网时通过公司批准的秘密管理工具提供 `TWC_CNB_TOKEN` 和 `TWC_CNB_IDENTITY_TOKEN`（Gitea 使用 `TWC_GITEA_TOKEN`），只使用所需的只读权限。CNB 的端点、权限与检查边界见 [CNB 接入](skills/team-workflow-craft/references/cnb.md)；Gitea 沿用 [Gitea 接入](skills/team-workflow-craft/references/gitea.md)，初始化显式用 `--provider gitea`。不要把 Token 放命令行、配置或 URL。`doctor --online` 检查身份、仓库及可用版本信息；CNB SaaS 版本为 unsupported；`prepare --offline` 可在网络不可用时保留未知状态。

`verify` 默认仅预览。已有授权覆盖当前检查和副作用后，用预览的策略哈希执行：

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product verify \
  --execute --approved-policy <policy_sha256> --online
```

命令记录真实时间、退出码、base/head、dirty 内容指纹、策略及工具版本。配置哈希只是把执行绑定到已审阅命令，不构成批准来源；输出只存摘要哈希和字节数，避免把潜在凭据日志写入交接。未运行/失败/超时/内容漂移不会通过。

每人首次配置个人 Git 姓名/邮箱和个人平台凭据，随后自动记录执行者。任务负责人、Git 作者、验证者、交接者和合并者分别追踪；换人不会沿用旧身份，离线也不会猜测账号。接入步骤见 [成员身份](skills/team-workflow-craft/references/identity.md)。

普通任务可用已有规格；需要结构化检查时把 [任务模板](skills/team-workflow-craft/assets/templates/task-contract.json) 按真实任务填好，`prepare --contract <repo-relative.json>` 引用。不要填第二份 owner/status。

```sh
python3 skills/team-workflow-craft/scripts/twc.py --project /path/to/product handoff --draft --online \
  --packet .team-workflow/local/packets/<run_id>.json \
  --evidence .team-workflow/local/evidence/<run_id>.json \
  --done "已实现并验证接口" --next "集成负责人核对组合测试和审批"
```

交接默认本地 JSON/Markdown 草稿。平台未刷新时 `unknown`，未提交工作/陈旧证据等为 `not_ready`；`--online` 可重新读 PR。`advisory_ready` 仅表示材料可供人工集成审查，永远不是合并授权。真正跨人接手须由获授权成员推送分支、发布去敏材料，并用平台可访问 URL 替换本地引用。

## 六组入口

| 命令 | 行为 |
| --- | --- |
| `doctor [--online]` | 依赖、整个 Git 根、配置/版本锁、项目安装入口；可选只读平台诊断 |
| `init [--dry-run/--apply]` | 预览或创建最小配置，不覆盖已有配置 |
| `prepare --task issue:N/pr:N` | 获取任务快照、引用契约、绑定当前工作区；不认领/回写任务 |
| `workspace inspect/create` | 全根 WIP 检查，或明确新路径/分支的 worktree 预览与创建 |
| `verify` | 默认计划；显式执行项目已批准命令，产出版本绑定证据 |
| `handoff --draft` | 草稿与建议状态；`--publish` 在本版本拒绝执行 |

## 固定构建与项目安装

唯一安装产品为 `skills/team-workflow-craft/`，外层开发工具不参与运行。不会自动安装本仓库里的全部 Craft，也不会自动升级 latest。

```sh
python3 scripts/build.py --output-dir /path/to/approved-artifacts
python3 scripts/install.py --artifact /path/to/approved-artifacts/team-workflow-craft-0.1.3.zip \
  --project /path/to/product --host codex
# 核对目标、产物和来源后加 --apply；Claude 用 --host claude，Pi 用 --host pi。
```

安装器校验 ZIP/文件哈希，拒绝未知、漂移或 symlink 目标；固定版本重复安装幂等。只支持明确项目目标，正常升级需要检查旧安装无漂移并显式 `--allow-upgrade --apply`。ZIP 与清单必须来自批准来源：攻击者同时换掉二者时，本地哈希无法验证真实性。

Codex/Pi 使用 `.agents/skills/team-workflow-craft/`；Claude 使用 `.claude/skills/team-workflow-craft/`。宿主规则尽量共用 AGENTS.md，Claude 如需 `CLAUDE.md` 导入由项目显式配置。工具不修改它们。三宿主发现路径、实际加载和独立包证据见 [兼容性](docs/compatibility.md)。

## 开发与验收

```sh
python3 scripts/check.py
# craft67 根：
python3 scripts/check.py --package team-workflow-craft
```

门禁覆盖临时 Git 工作区、受控 CNB/Gitea HTTP 模拟器、失败/漂移、安装保护及真实运行时独立包测试；不使用公司账号或付费模型。根 catalog 接入离线 CI，不能替代受控 CI、宿主或目标平台实测。

进一步说明：[架构与数据合同](docs/architecture.md)、[成员接入](docs/member-onboarding.md)、[试点与运维验收](docs/operations.md)、[隔离分支保护验收](docs/gitea-policy-probe.md)、[可选 Gitea 部署方案（AIOS 已停用）](docs/gitea-vps.md)、[AIOS 接入与发布来源切换建议](docs/aios-adoption.md)、[来源与许可](docs/upstreams.md)、[版本变更](CHANGELOG.md)。MIT；未复制 Trellis/OpenSpec 的代码或模板。
