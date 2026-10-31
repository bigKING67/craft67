# 项目开发模式

个人与团队共用契约、验证和接续链路。模式决定新任务的协作要求，不改变当前用户权限、项目保护规则或历史任务。一个人使用多个 Agent 可以选择个人；团队仓库里一个人执行任务仍沿用团队配置。

## 全局入口与项目固定版本

全局 Skill 用来发现项目；执行任务和保存证据使用项目内固定副本。全局升级不自动升级项目。宿主加载全局 Skill 后，先执行（`<global-skill>` 是本次加载的目录）：

```sh
python3 <global-skill>/scripts/twc.py --project <repo-or-child> entry --host codex
```

Claude 用 `--host claude`，Pi 用 `--host pi`。返回 `use_project_runtime` 时，后续仅使用返回的 `cli` 和 `skill`；它可以是旧版本，只要完整性、项目各入口及工具链锁一致。该命令不执行项目代码；选定路径仍须遵循宿主的项目信任及执行授权。未知/漂移副本、旧新名并存、宿主副本不一致或锁失配时先恢复批准的固定安装，不用全局版本绕过。

返回 `pin_project_runtime` 时，项目尚未接入。可先用全局 `doctor --local` 读取名字和模式提示；先按下一节确认模式，再在接入授权范围内执行：

```sh
python3 <global-skill>/scripts/twc.py --project <repo> entry --host codex --apply
python3 <returned-project-cli> --project <repo> init --mode personal --apply
```

`entry --apply` 只创建当前宿主的项目 Skill，不初始化模式、不安装其他宿主、不写用户规则或宿主设置。团队模式替换为已选择的 `team`；另一宿主可直接使用已有的项目 CLI，需要原生发现时再按安装说明安装同一批准版本。安装副本与 `.team-workflow/` 应按项目约定一同提交。已有 `.team-workflow/` 却没有项目副本时，需恢复锁中固定的产物，不能当新项目初始化。

全局目录与宿主发现由宿主管理。打开文件夹本身不会执行提醒；仅在宿主实际选择/显式调用 Skill 时开始上述流程，不安装 Hook 或每轮注入。已有项目的原生入口优先级仍须按宿主实测，CLI 选择结果不等于宿主已加载。

## 首次选择

`doctor --local` 或尚未初始化时的 `resume` 返回 `development_mode.status=selection_required`。询问一次个人/团队，个人只是推荐，不是默认授权。用户没有回答时只读工作可以继续，init 不能写配置。已有明确意图时直接采用，已有名字时不重问。新项目单独选择，Git 根下的子目录共用；新 clone 从版本化配置恢复选择。非 Git 或没有任何提交的目录需先说明前置条件，不自行 git init/commit。

用户确认个人开发后：

```sh
python3 <skill>/scripts/twc.py --project <repo> init --mode personal
python3 <skill>/scripts/twc.py --project <repo> init --mode personal --apply
```

默认把当前提交固定为本地基线，不需要 remote、平台或 Token。使用长期集成分支时显式传 `--base-ref main` 等已存在引用。个人契约沿用 goal/non_goals/scope/dependencies/acceptance/contracts/complexity/risk，可省略 integrator。按现有 [契约规则](context.md) 说明验收并配置真实检查，然后创建 `local:<slug>` 任务（小写字母、数字、下划线和连字符）：

```sh
python3 <skill>/scripts/twc.py --project <repo> prepare --task local:export-orders --contract docs/export-orders.json
python3 <skill>/scripts/twc.py --project <repo> resume
python3 <skill>/scripts/twc.py --project <repo> verify
```

本地 prepare 写任务和绑定，默认不联网。后续验证仍需执行授权及准确策略哈希。`handoff --draft` 可供下一会话接续：本地任务的 `readiness_scope=local_task`，即使 advisory_ready 也不证明平台审批或授予提交/发布权限。未提交改动仍报告不可移植；同一工作树可继续，跨机器分享须按项目规则提交。名字足以记录本地执行，正式 Git 提交仍使用用户自己的提交身份。

## 团队接入

团队模式用 `init --mode team`。没有平台时也可使用 local 任务，但新契约必须指定 integrator；此类交接报告 `task_integrator_review_required`，工具不伪造独立评审。连接已有 CNB/Gitea 时显式传 provider/base-url/repository/base-ref，并读取 [身份与交接](identity.md) 及对应 [CNB](cnb.md)/[Gitea](gitea.md) 引用。

```sh
python3 <skill>/scripts/twc.py --project <repo> init --mode team \
  --provider cnb --base-url https://cnb.cool --repository company/product --base-ref origin/main
```

按授权加 `--apply`。平台 issue/pr 的默认联网行为保持不变；`prepare --offline` 不写平台，但仍写本地记录。已有 Trellis 时沿用 `--workflow-owner trellis`，引用原规格，不建立另一套负责人/任务状态。模式没有“自动运行子 Agent”含义。

## 跨平台配置与已有项目

策略批准和证据绑定 `config.toml` 的原始字节。0.6.3 起，`init` 在 `.team-workflow/.gitattributes` 中写入 `/config.toml -text`，避免 Windows Git 自动换行改变策略哈希；新文件统一写 UTF-8/LF。应把该属性文件与配置一同提交。已有根属性和用户规则不改写；实际编辑配置仍会改变策略哈希，旧批准与证据照常失效。

升级 Skill 不自动迁移已有项目。项目出现仅换行造成的跨 clone `stale` 时，先核对 Git blob、工作区字节及本地改动；在已授权修复范围内，将同一规则合入现有的 `.team-workflow/.gitattributes`（没有时创建），不覆盖其余规则，并以已核对的版本化配置统一字节。旧记录保持原样，按正常流程记录所需的新验证；不手改旧策略哈希。跨机器复验需同时检查配置字节、策略哈希和 `resume`，不能仅以测试通过或安装完整性代替。

## 后续切换

```sh
python3 <skill>/scripts/twc.py --project <repo> mode
python3 <skill>/scripts/twc.py --project <repo> mode --set team
python3 <skill>/scripts/twc.py --project <repo> mode --set team --apply --approved-policy <返回的policy_sha256>
```

用户已授权本次切换时，Agent 核对预览后直接应用，不重复索要同一授权。个人使用 `--set personal`。切换仅重写项目 config，保留解析后的其他设置；格式和注释可能变化，预览包含完整拟写入内容。应用校验当前策略哈希，防止覆盖期间的配置修改。

预览列出当前任务、集成人和最近交接的未完成项；绑定异常先处理，不隐式解绑。旧任务、历史署名、验证记录和平台连接保持原样，原有平台或 integrator 要求继续生效；修改配置使旧验证过期，需在新策略下重验。已有平台不能通过 mode 命令替换；尚未接入的平台可用 `--provider ... --base-url ... --repository ...` 一次补齐，调用不联网。

旧 schema v1 配置只读时识别为团队；显式切换时升级到 v2，新增稳定 project_id，既有平台任务身份不变。v2 缺失或非法模式是配置错误，不能自动退回个人。工具链协议升级到 2，旧锁须单独核对升级；模式切换不更新锁或代替升级授权。
