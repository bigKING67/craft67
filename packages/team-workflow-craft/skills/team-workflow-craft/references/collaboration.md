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

集成采用人工串行：刷新主分支 → 任务分支包含最新基线 → 必要检查/组合测试 → 核对当前 base/head 和审批 → 授权负责人合并 → 下一个任务刷新。Gitea PR head 检查不证明组合后的产品通过；L2 必须验收整条实际功能和错误/重试路径。

Gitea 的旧审批撤销依据 PR 内容变化，单纯合入最新主分支可能保留原审批。head/base 变化后仍须重新验证组合，并由审查者确认当前 head；不能从平台仍显示 approved 推断新组合已通过。具体语义见 [Gitea 分支保护](https://docs.gitea.com/usage/access-control/protected-branches/)。

服务器分支保护、CI 身份和权限是正式门禁。本地 advisory 不代替它们。生产/协作平台/Runner 部署及账号管理不由 TWC 执行。

CNB 的合并预览、身份和权限差异见 [CNB 接入](cnb.md)。不同平台的检查语义分别核对，不把 Gitea 的旧审批行为套到 CNB。
