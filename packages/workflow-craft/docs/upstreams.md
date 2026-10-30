# 依据与许可

本包首版按用户给出的 Workflow Craft 设计 v0.2 落地为源码 v0.1.0；当前版本见包根 VERSION。未取得其 sandbox 附件，实施以本次消息中的完整方案为依据，不声称已读取 ZIP。未复制 Trellis/OpenSpec/Superpowers 代码或模板；本包新增内容 MIT，包根 LICENSE 随安装产物分发。

实现核对的权威资料（2026-10-15；不等于公司实例已验收）：

- [Gitea API Usage](https://docs.gitea.com/development/api-usage/)：认证、分页、实例 OpenAPI。
- [Gitea Actions FAQ](https://docs.gitea.com/usage/actions/faq/)：PR head 检查及默认 Actions 来源。
- [Git worktree](https://git-scm.com/docs/git-worktree)：独立工作目录和分支边界。
- [Claude Code Skills](https://code.claude.com/docs/en/skills)：项目 Skill 与显式调用。
- [Pi Skills](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md)：项目发现和 `/skill:`。
- Codex 路径依据与宿主实测限制见 [compatibility.md](compatibility.md)。

这些来源说明能力合同，不能替代目标版本和目标主机行为证据。Gitea 的早期 VPS/隔离实测属于历史证据，该 VPS 实例已停用；CNB 的离线合同、真实登录页面与 Token API 实测分别记录，不能相互替代。

- [CNB OpenAPI](https://docs.cnb.cool/zh/develops/openapi.html) 与 [Swagger](https://api.cnb.cool/swagger.json)：只读端点、权限、字符串 ID 和分页。
- [CNB 角色权限](https://docs.cnb.cool/zh/guide/role-permissions.html)、[构建触发规则](https://docs.cnb.cool/zh/build/trigger-rule.html)：开发者合并权限与合并预览语义。
