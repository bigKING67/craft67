# 工作区和集成

不同成员各自 clone。同机并行任务或多个 Agent 尝试不同方案时，每个尝试用独立 worktree 和分支，结果按普通 PR 评审；已独立的工作区无需再套一层。检查始终覆盖真实 Git 根：branch/base/head、暂存/未暂存/未跟踪、其他包 WIP、现有任务绑定。路径预警不代表锁或独占授权。

```sh
python3 <skill>/scripts/twc.py --project <repo> workspace inspect --scope packages/example
python3 <skill>/scripts/twc.py --project <repo> workspace create --path <new-sibling-directory> --branch task/42
# 查看目标和基线，已有授权覆盖后在同一命令加 --apply
```

多个 Agent 会话共用一个 clone 时，暂存区可能有别的会话的文件。提交一律带 pathspec（`git add -- <paths>` 后 `git commit -m … -- <paths>`），提交前看一眼 `git diff --cached --name-only`；`resume` 和 `workspace inspect` 会列出 `staged_outside_scope`。

只创建新路径和新分支，不 stash/reset/clean/覆盖现有工作目录。worktree 使用当前配置的本地 base_ref；不会自动 fetch，输出 `remote_freshness=unverified`。先按项目授权刷新基线。worktree 创建属于 Git 元数据写入，工具会说明影响。

工作树不隔离端口、数据库、Redis、对象存储、Docker 项目和输出目录。涉及这些资源时，先确定任务命名空间（如 team-product-issue42）、测试数据和清理范围，再执行检查；不能把“路径不同”当成可安全并发测试。

L2 在修改前确定接口版本、分工路径、依赖顺序和集成负责人。公共接口、迁移、根锁文件/catalog/CI 由负责人协调；同时修改质量规则需要可信审批，不能由执行者降低规则后自证通过。

## 审查与收敛

独立复核按项目要求和风险选择，不为每个小任务增加 Agent。需要独立审查时，提供目标、当前 diff、约束和验证证据，让审查者自行判断；作者的解释不能替代复核。角色由负责人或宿主安排，TWC 不启动 Agent 或维护另一套审查状态。

项目未约定时，以三轮 review-and-fix 为重新评估点：一轮指审查发现问题、实施修复并复核，不是同一命令的重试次数。问题解决且证据充分即可结束；第二轮起聚焦修复、新增变化、未决发现及受影响的调用方和行为。发现回归或范围扩大时补查相关路径，不能只看新增代码行，也不无理由重审已确认且未受影响的部分。

达到约定轮次仍不收敛时，保留未决问题、已尝试修复及证据，交由负责人裁决范围、方案或补充验证；独立授权且不依赖这些问题的工作可继续。轮次用尽不构成通过或合并许可，不得通过删除发现、弱化测试或改写验收来结束审查。裁决前保持真实的未完成/未知状态；后续重验仍绑定裁决后的契约和代码。

## 组合验证与合并

集成采用人工串行：刷新主分支 → 任务分支包含最新基线 → 必要检查/组合测试 → 核对当前 base/head 和审批 → 授权负责人合并 → 下一个任务刷新。Gitea PR head 检查不证明组合后的产品通过；L2 必须验收整条实际功能和错误/重试路径。

Gitea 的旧审批撤销依据 PR 内容变化，单纯合入最新主分支可能保留原审批。head/base 变化后仍须重新验证组合，并由审查者确认当前 head；不能从平台仍显示 approved 推断新组合已通过。具体语义见 [Gitea 分支保护](https://docs.gitea.com/usage/access-control/protected-branches/)。

服务器分支保护、CI 身份和权限是正式门禁。本地 advisory 不代替它们。生产/协作平台/Runner 部署及账号管理不由 TWC 执行。

CNB 的合并预览、身份和权限差异见 [CNB 接入](cnb.md)。不同平台的检查语义分别核对，不把 Gitea 的旧审批行为套到 CNB。
