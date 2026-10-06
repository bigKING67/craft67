# craft67

- 本仓库集中维护 `catalog.json` 登记的 10 个项目、18 个 Skill。各包内部的 AGENTS.md 继续适用。
- 在对应 `packages/<name>/` 内执行包级命令，不能假设包目录就是 Git 根目录。
- 唯一主仓库 Git 根是 craft67；上游参考仍是固定版本的 submodule。不要编辑上游内容。
- 迁移来源见 `docs/migration-sources.json`。原仓库提交与旧验收是历史来源，不是新仓库的发布或当前运行态证据。
- 保留各 Skill 名称、包边界、许可证、独立安装能力和测试合同。仅对已经证实的迁移问题做最小修复。
- `python3 scripts/check.py --package <name>` 执行包的离线检查；实际宿主加载、浏览器验证、发布门禁分别报告。
- 本地配置、凭据、个人资料、缓存和运行输出不纳入源码。不要批量复制全局 Skill 或宿主配置。
- 安装、commit、push、发布和旧目录清理分别核对用户授权。提交只做 scoped add/commit。
