# CNB 首轮演练入口

本页记录 2026-10-16 的接入验收快照；任务、PR、构建和权限的当前状态以 CNB 为准。演练仅使用合成代码，不代表 AIOS 已导入或生产已切换。

- 私有仓库：[bql_huayue/twc-pilot](https://cnb.cool/bql_huayue/twc-pilot)。
- 成员任务：[Issue #1：校验空白标签并完成 PR 交接](https://cnb.cool/bql_huayue/twc-pilot/-/issues/1)，当前未分配，人选尚未确定。
- CI 变更：[PR #2](https://cnb.cool/bql_huayue/twc-pilot/-/pulls/2)，分支 `chore/sixseven/pilot-ci`，保持待审，未合并。
- 固定 TWC v0.1.3 候选包和项目安装入口在演练仓库 `tools/`；产物来源为 craft67 提交 `40044be`，不是正式 Release。宿主发现的证据与限制见 [兼容性记录](compatibility.md)。

## 已取得的真实平台证据

[首个 CNB 构建](https://cnb.cool/bql_huayue/twc-pilot/-/build/logs/cnb-33k-1k51diqce) 的 `pilot-unit / unit-tests` 实际运行了 3 项测试，退出码 0。构建总用时 15.8 秒，测试任务约 0.6 秒，Python 3.12.15。配置使用 1 核 amd64 节点、按摘要固定的 Python 官方镜像和 60 秒测试任务超时；没有部署或定时任务。

该构建的源分支与实际 checkout SHA 为 `3fe98ec00a6c7e498a3a0d904135ba98523c9f53`，目标基线为 `1a84e110e908922e613e3ca228270d3c4a3d6d95`。源分支直接基于这条 main，因此本次不证明分叉后的组合冲突处理已经验收。

PR 页面显示状态检查 1/1 通过，仍因管理员评审 0/1 阻止合并；API 同时返回 `blocked_on=waiting_review`、`is_merged=false`。`mergeable_state=mergeable` 只表达代码可组合，不能据此越过审批。没有降低保护规则或作者自批。

检查脚本另在本地临时仓库验证了失败、零测试、全部跳过三条路径均返回非零。这些是本地回归证据，不宣称 CNB 已实测全部失败场景。

## API 与交接的边界

同一次实测中，PR 页面和构建日志显示成功，但 CNB 公共 API 的 head commit statuses 返回 `[]`，PR 的 `statuses` 返回 `{}`。不要据此把 TWC 的空检查列表解释为成功，也不要把 PR 的代码可合并状态解释为服务器门禁通过。当前适配器保留未知符合其覆盖范围；参见 [CNB 接入合同](../skills/team-workflow-craft/references/cnb.md)。

正式交接应附 PR 和构建日志链接，并核对当前 head/base、实际 checkout、检查策略与独立审批。离线或空 API 结果不覆盖平台的后续变化，也不替代真实日志。日志中的 `CNB_COMMIT` 在 PR 事件下表示源分支，不能仅凭这个变量声称已绑定预合并版本；需同时读取实际工作区 Git 信息。[CNB 构建变量](https://docs.cnb.cool/zh/build/build-in-env.html)

## 成员确定后的第一步

由 sixseven 按实际 CNB 用户名添加成员并分配 Issue #1。成员用个人账号、Git 身份和独立 clone，安装仓库中的固定候选包，再按仓库 `docs/pilot.md` 开自己的分支、完成测试和 PR 交接。不要复用 AIOS 专用 Token 或负责人凭据。

CI PR 自身需要另一位合适成员独立审查；首轮还需验收普通成员的 main 直推/强推拒绝、指定合并者权限、跨人接手与三种 Agent 的完整执行。当前单账号的审批阻断不能替代这些检查。AIOS 旧凭据失效状态未确认时，继续保留空仓库，不导入历史。
