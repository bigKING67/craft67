# AIOS Codex 入口归档与回退试点

2026-10-31。本轮继续使用 Workflow Craft 0.5.1 固定安装包，只验证隔离 AIOS 副本中的 `local:aios-pilot-*`；原 AIOS、其他任务和其他宿主没有被接管。

## 为什么调整入口

在 Codex 0.166.0 上，使用无凭据的独立配置目录做了四组原生 `config/read` / `skills/list` 对照。无禁用配置时测试 Skill 启用；可信项目中的相对路径和绝对路径禁用项均能读到，但目录仍报启用；同一绝对路径放在隔离用户配置中才报禁用。这里只报告当前版本的观察，不推断所有版本或宿主的实现。官方 [Skill 禁用文档](https://developers.openai.com/codex/skills/#enable-or-disable-local-codex-skills)明确给出的是用户级配置。

因此本次试点采用项目内入口归档，而不要求每位成员配置个人绝对路径。归档只适用于明确批准的切换范围，不成为通用 Skill 的自动行为。

## 变更与原有约束

- 从上一轮冻结副本 `ec4aecc6207b6365eb7fe4adf67b52eabb208fd2` 建立新的独立 clone，无远端。12 个 Trellis Skill 目录与 3 个 Codex Agent 定义，共 49 个文件移入 `docs/workflow-pilot/legacy-codex/{skills,agents}`。该位置不包含新的 `.agents/skills` 发现根；文件内容与冻结 Git blob 逐一一致。
- Workflow Craft 和原有的两个非 Trellis 项目 Skill 保留原位；移除试点添加的旧 Skill 禁用项，项目 Trellis Hook 注册继续为空。原 `.trellis`、Claude/Pi 文件、业务代码与测试保持不变。
- 原 `agent-workflow` 保留全部检查，仅将旧 Codex Skill 的门禁读路径映射到归档，并明确输出这属于历史合同审计。它不认证当前活动入口；新的 `workflow-pilot` 负责检查试点所有者、基线、安装、任务结构、归档完整性和旧入口未重新启用。
- 根 AGENTS 的原项目规则保留，只调整已有的试点例外。试点之外的 Codex 任务尚未迁移，不能因本轮通过就从原项目移除全部 Trellis。

独立只读核对发现，Pi 有自己的扩展与 prompts；Claude 导入根 AGENTS，但这个冻结副本没有完整的旧 Claude Skill 安装，无法据此证明 Claude 原生行为不受影响。保持文件一致与完成宿主验收分别报告。三轮有界审阅中修正了“禁止所有项目 Agent”的过宽约束，并验证允许无关的项目 Agent 与 Skill 配置。

## 确定性验证

- 项目根目录与 ETL 子目录各启动全新原生 app-server：Workflow Craft 和另外两个项目 Skill 可发现，12 个 Trellis Skill 不再出现，目录无错误。没有 Skill 禁用参数或信任覆盖，没有模型调用。
- 14 个负向检查拒绝归档缺失/篡改/额外文件、旧 Skill 原路径/别名/符号链接恢复、旧 Agent 别名和配置注册、共享规则/Hook/门禁变更，以及重新登记启用或禁用的归档 Skill。一个正向对照确认其他合法 Agent 与 Skill 配置仍允许；恢复后门禁通过。
- fixture-only 迁移工具先核对所有源、目标和编辑基线；5 个迁移与 3 个回退异常场景通过，覆盖漂移、目标占用、中途移动或写入失败。失败后对应文件快照恢复一致。该工具没有进入 Workflow Craft 安装包，也不是通用生产迁移器。

## 不使用入口覆盖参数的原生会话

最终入口候选冻结于临时仓库提交 `d247e8861296f28d3992cc2f3f676be25fbcaa87`。模型仍为 `gpt-6.1-sol` / `max`，主会话上限 300 秒；使用标准 `codex exec --ephemeral --json --sandbox workspace-write`，没有 `-c`、Skill 禁用或信任覆盖参数，提示也未显式点名 Skill。进程使用现有宿主配置和身份，不复制凭据。

主会话在 **184.09 秒**正常结束，退出 0。事件确认模型自行读取项目 Workflow Craft，完成 revision 3 的两项验证（包括 9 项既有业务测试）、完成、交接与会话结束。最终 `completed/current`，会话查询为 `no_task`；handoff 仍为 `unknown`、`merge_authorized=false`。只写本任务和 ignored local，没有执行 Trellis 运行时、Git 提交/推送或业务外部操作。一条查询因隔离分支没有 upstream 返回 128，记录保留，没有凭空创建或连接远端。

主会话事件 SHA-256：`a2b80789d30a472638e41b47f183e1796f891a37bd38e3cf26df01fb0a9814d0`。另保留了审阅修正前主动中止的样本：35.79 秒、退出 -15、没有项目文件写入，不计为验收通过。

本轮还观察到宿主副作用：首次原生 CLI 启动时自动新增了该隔离项目的全局信任条目。未传信任参数不等于没有配置写入；精确移除该条目后，配置哈希恢复验收前值。第二个原生会话在用户明确批准临时信任后执行。因此本轮不能表述为“不需要项目信任”或“宿主配置从未改变”。

## 新会话只读接手与最终回退

另一全新原生会话从 `etl/groland_postgres` 子目录启动，提示仍不显式点名 Skill，180 秒上限。它在 **119.96 秒**正常结束，退出 0，自行读取 Workflow Craft 并只读 `resume`，准确识别 revision 3 的 `completed/current`、两项有效检查以及未获得合并授权；没有重跑验证、建立绑定或写入项目文件。中途读取不存在的 `config.json` 的尝试保留在事件中，随后根据实际配置与 CLI 完成核对。只读会话事件 SHA-256：`b01e5663a9aa8de2b2772ab16feba7b17f483c5debaf625d5a6fc4887fa17bdd`。

会话结束后仅移除本次获准的信任条目，全局 Codex 配置 SHA-256 恢复为验收前的 `7c8a0a9b63cae3a48b798fe44d967ee812d3edc5d7998f02a34db97daf4beea9`。没有保留全局 Skill 禁用项。

随后完成入口回退演练：恢复 12 个旧 Skill 与 3 个 Agent 定义及四个编辑文件，原生目录重新发现 12 个 Trellis Skill，原门禁通过；本轮新增的任务、交接、证据及本地会话共 33 个工作流文件逐一保持不变。历史完成仍保留，但规则/代码回退使完成依据正确变为 `stale`。重新应用完全相同的入口候选后，新门禁通过，完成依据恢复 `current`；没有追加失败验证或抹除失败历史。这只验收入口回退，不等同于完整 Trellis 任务数据迁移的回滚。

## 结论与未覆盖项

指定试点任务已在不使用 Skill 禁用或 `-c` 入口覆盖参数的 Codex 原生会话完成，并由子目录中的新会话只读接手。配置/文件检查、原生发现、实际模型使用和回退各有独立证据；这些结果推进 M3 的 Codex 子项，不能宣称整个 AIOS 已迁移或已经超过 Trellis。

原 AIOS 的 HEAD、同参数 Git 状态摘要与选定的 23 个文件保持一致。Workflow Craft 安装候选仍是此前固定的 0.5.1 ZIP；本轮项目改动只存在隔离副本，craft67 仅保存验收说明，不发布通用自动迁移器。验收期间另有并行 Skill 正文改动，本轮未纳入、未同步安装，也未把它算作固定候选的一致性证据。

离线包门禁在已提交的 `21cfc62` 源码加本轮验收文档的独立快照上运行：193 项通过，无跳过；39 个安装文件与固定 ZIP 一致。该结果与并行提交的 Skill 正文修订分开，不把旧固定产物的原生行为当作新正文已验收。验收结果补录后另核对文档链接。

下一阶段仍需真正业务改动、真人同事接手、Claude/Pi 原生验收、完整历史数据承接，以及同模型/任务/验收口径的 Trellis 对照。原 AIOS 继续保留 Trellis，正式切换与清理分别核对授权。
