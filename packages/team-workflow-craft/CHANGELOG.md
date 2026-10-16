# Changelog

## 0.1.3 — Unreleased

- 根据 CNB 真实最小权限验收，拆分仓库 Token 与仅账户信息 Token；指定仓库 Token 保存后不含 account-profile 权限，不能靠放开全部私有仓库绕过。
- CNB 配置支持 identity_token_env，分别调用账户与仓库端点；检查子进程移除两套凭据，缺账户 Token 不回退或猜测身份。
- 记录独立账户 Token 无法证明仓库/推送使用同一身份的边界；保持本地身份观察而非认证声明。
- 补充固定 v0.1.3 产物在 macOS 上的 Codex 0.162.1、Claude Code 2.1.296、Pi 1.1.0 原生发现证据；未调用模型，正文调用与完整协作仍待验收。运行时产物未变化。
- 新增安装产物跨三份 clone 的 CLI 验收，覆盖身份交接、主分支/接口漂移、各自通过但组合失败、修复重验及保留原工作区 WIP。仅使用合成代码和本地 Git，包级门禁共 89 项。

## 0.1.2 — Unreleased

- 增加 CNB SaaS 只读适配、显式 `init --provider cnb`、真实端点/分页/字符串身份合同；保留 Gitea 兼容性。
- 共用有界 GET 传输，拒绝重定向和令牌泄漏；CNB API origin 固定，服务器版本未知保持 unsupported。
- PR 快照直接读取 PR，跨 provider 的任务和 actor 不混用；commit statuses 不冒充合并预览或完整服务器门禁。
- 成员和 AIOS 接入说明改为 CNB 主平台，保留 Gitea 方案作为可选历史实现。源码、构建、安装、API live 与多人验收仍分别报告。

## 0.1.1 — Unreleased

- 为 doctor、任务快照、验证和交接增加当前操作者的 Gitea 账号与有效 Git author/committer 观察；保留准备者、各证据执行者和当前交接者，不从任务负责人或分支名冒充身份。
- verify 增加显式 `--online`，离线/缺身份的证据保持未知归属；检查期间 Git 身份变化记 incomplete。缺 actor 的旧 v1 数据仍可读，不自动补名。
- 成员指南明确个人账号与一次性 Git 身份配置；AIOS 使用成员任务分支、sixseven 集成合并。服务端权限、生产来源及个人 Git 配置未因此自动修改。
- 单独构建新的固定候选版本，避免覆盖先前的 0.1.0 产物；未正式发布或安装到真实成员宿主。

## 0.1.0 — Unreleased

- 新增按协作复杂度/风险分别处理的轻量 Skill，支持独立或 Trellis 托管流程。
- 新增 Gitea 只读任务/PR/reviews/commit statuses、权限与失败分类。
- 新增整个 Git 根检查、显式 worktree 创建、任务快照和工作区绑定。
- 新增命令预览/策略绑定执行、内容与基线漂移检测、JSON/Markdown 交接草稿。
- 新增固定 ZIP/清单、项目级三宿主安装入口与离线合同门禁。
- 新增独立 Gitea/ PostgreSQL 的 VPS 伴随配置、固定镜像 digest、资源上限及备份/回滚方案；不进入 Skill 运行时，也不自动部署。
- 伴随配置已通过本机真实 Gitea API 实测及授权的 VPS 空实例 HTTPS 部署验收，证据边界见部署文档。
- 完成 VPS 一致性快照、Mac 加密异机保存和隔离恢复，回读账号、组织、空仓库及分支保护；正式 HTTPS 的 TWC 身份/仓库读取通过，临时 Token 撤销后拒绝访问。
- 增加显式选择的隔离 Gitea 行为探针及环境拒绝测试；17 项合成 Git/REST 场景通过，覆盖 main 拦截、审批、串行集成与只读适配器。补充成员指南及基线同步可保留内容审批的真实语义；测试工具不进入 Skill 运行时。
- 未发布；评论发布、真实宿主/Windows/多人集成和有项目内容的恢复仍未验收；Skill 不提供服务器部署命令。
