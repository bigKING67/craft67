# 任务与上下文

本地任务用 `local:<slug>` 和项目配置中的稳定 project_id 标识；平台任务由 provider、平台 URL、repository、`issue:N` 或 `pr:N` 组成。同 slug 跨项目、同编号跨平台实例/仓库不是同一任务。下面展示平台任务，本地任务换成 `local:<slug>`，目录为 `local-<slug>`，不读取平台。

```sh
python3 <skill>/scripts/twc.py --project <repo> prepare --task issue:42 --contract docs/task-42.json
python3 <skill>/scripts/twc.py --project <repo> resume
```

`prepare` 做三件事：

- 把契约记录到 `.team-workflow/tasks/issue-42/task.json`，这个文件随任务分支提交；
- 把平台快照写进 ignored 的 `.team-workflow/local/packets/`，平台正文只供宿主理解，不进仓库；
- 绑定当前工作区，并记录准备时的 Git 分支。

离线加 `--offline`，平台事实记为未知。已有不同的本地绑定会被拒绝；确定切换任务时才用 `--rebind`，它只改本地绑定，绝不认领平台任务。

## 从目标到最小可用交付

已决定使用本工具记录 L1/L2 任务、需要准备契约时，先从用户目标、项目规格或平台 Issue 明确目标用户、当前问题、期望结果和必要约束。已有背景直接引用；只补问影响范围、验收、成本或不可逆后果的关键缺口，常规实现细节由 Agent 现场判断。L0 沿用原项目流程，不为填写模板另建任务。

把大目标拆成能独立验收的用户结果；以一条可用流程为首版，界面、接口等分工共同服务这个结果。代码行数不决定任务大小或风险。动手前简述本次修改范围、受影响行为、验证方式及适用的回滚限制；已有授权覆盖时继续执行。未被需求覆盖的新功能、配置或跨模块行为先说明影响并确认范围，不把内部实现选择逐项交给用户。

例如，客服希望减少每周手工整理退款订单的工作：

- `goal`：客服能按日期导出退款明细，用于每周核对。
- `non_goals`：本次不做定时发送、新配置页面或其他订单流程改造。
- `scope`：读代码后列出实际导出逻辑、界面和对应测试路径；这里限定文件范围，产品边界由目标与非目标表达。
- `acceptance`：日期边界符合已有业务口径；导出条目与金额和选定数据一致；无记录时有明确结果；无权限用户无法获得数据；客服能在实际界面完成操作。

背景和日期口径留在原规格，需要绑定时用 `contracts` 引用。以上是任务写法示例，不是所有项目都要实现退款导出。复制 [任务模板](../assets/templates/task-contract.json) 后替换示例文字、路径和检查名；不要直接把模板当成已确认需求。

验收先写可观察行为，再关联能覆盖它的项目检查。复用已有检查，只补真实覆盖缺口；模板中的 `unit` 只是检查名示例，不能据此认定单元测试覆盖权限、界面或整条流程。无法自动判断的体验和人工操作保留为文字 AC。已确认缺陷应留下能再次发现它的回归验证；主观反馈按情况用操作案例或人工验收。工具只核对证据是否新鲜、所列检查是否通过，覆盖是否充分仍需审阅。

## 契约字段

若验收涉及真实用户流程，开工前用 [功能验证路径](feature-verification.md) 定位现有入口、操作、预期结果与证据；已有说明直接引用，缺失时只补受影响的关键路径。

`assets/templates/task-contract.json` 提供模板，字段为 goal/non_goals/scope/dependencies/acceptance/integrator/contracts/complexity/risk。owner/status 不得另行维护。

- `integrator`：个人模式的新本地任务可省略；团队或平台任务必须指定。模式切换不删除已有任务的集成要求。
- `scope`：相对目录或文件路径，不是 glob。
- `contracts`：仓库内的具体文件，工具记录其哈希。Trellis 项目在这里引用 `.trellis/tasks/<t>/prd.md`，不复制 PRD。
- `dependencies`：权威任务或规格 URL，只存引用，不宣称依赖已完成。
- `acceptance`：每项是字符串，或 `{"id": "AC-1", "text": "…", "checks": ["unit"]}`；`id` 缺省时按顺序编号为 AC-1、AC-2…，并跳过已显式使用的编号；以后可能插入或调整顺序的条目请写显式 `id`，否则修订后编号会变。`checks` 列出项目配置里的检查名。
  - 列了检查的 AC，在所列检查都有新鲜的通过证据时为 `verified`；有失败为 `failed`；其余为 `pending`。
  - 字符串或 `checks` 为空的 AC 是 `needs_review`，由人判断，工具不会自动判定通过。

## 契约变化

`task.json` 保存契约、所引用文件的哈希和 `contract_sha256`。契约文件或引用文件变化后，再次 `prepare` 会拒绝执行。审阅变化后加 `--update-contract`：revision 加一，旧版本进入 `history`，之前的证据因契约哈希不同而失效。直接手改 `task.json` 会被 `prepare`、`resume` 和 `check` 识别为绕过记录的修改。

未提供契约时仍会记录任务（`contract=null`），可以阅读和开发，但交接会报 `task_contract_missing`。既有规格不适合 JSON 时，按相同字段写一份简短的契约并在 `contracts` 引用原规格，不强迫创建第二份长文档。

## 当前任务

`resume`、`verify`、`handoff` 按以下顺序确定当前任务：

1. 显式 `--task`；
2. 本地绑定；
3. 仅未选择会话的旧契约流程：本分支自离开 base 以来改动过的唯一任务目录，包括未提交的改动。

选择 `--session`/`TWC_SESSION_ID` 后只读取该会话绑定，不继承旧 binding.json，也不按分支猜测当前任务。生命周期的 start/finish、父子关系和完成边界见 [任务循环](task-loop.md)。新会话可显式 resume --task 只读核对，再在授权范围内 task start --task 绑定，不重建契约。

本地绑定与当前分支冲突、或绑定的任务记录在当前分支不存在时，命令会先拒绝并提示 `prepare --rebind`；审阅实际任务后再重新绑定。旧 v2 绑定可从其本地 packet 读取分支，无法取得准备时分支的旧绑定也需显式 `--rebind`；该恢复动作不依赖旧 packet 可解析。

第 3 条让接手者 clone 之后不需要任何对方的本地文件。分支改动过多个任务目录时，必须显式 `--task`。

先遵循当前作用域规则，再用 `resume` 核对已有任务目标、验收与证据，按需读取直接依赖的接口和相关代码/测试。不要加载全仓、整个 Craft 库或完整聊天记录。核对实际提交和契约漂移；仅新任务、绑定缺失/冲突或审阅后的契约变化需要在授权内 `prepare`，不因新会话重跑。平台任务按当前读取授权核对分配，不能用旧快照覆盖平台。
