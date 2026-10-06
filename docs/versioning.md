# 独立包版本与发布

craft67 是集合仓库，10 个包继续独立使用语义化版本。根仓库不另设与各包竞争的产品版本；整体源码快照用完整 commit SHA 标识。18 个 Skill 随各自所属包分发：Commerce 的八个 Skill 随一个 pack 版本，browser67 与 js-reverse 随 browser67 包版本，不另造重复版本。

## 版本来源

`catalog.json` 的 `version_source` 登记现有权威文件，版本值只在包内维护：

| 包 | 版本来源 |
| --- | --- |
| design-craft、creative-craft、review-craft、money-craft、3d-craft、reverse-craft、write-craft | 包根 `VERSION` |
| whoami、browser67 | 包根 `package.json` 的 `version` |
| commerce-growth-os | `skill-pack.json` 的 `pack_version` |

```sh
python3 scripts/versions.py
python3 scripts/versions.py --check
python3 scripts/versions.py --check --package browser67
```

命令只读，不改版本、不访问网络、不安装、不创建标签。它比较包根现有 package.json、package-lock.json（含根包条目）和 pyproject.toml 的产品版本；不把嵌套工具包、schema_version 或 Commerce 的 minimum_installer_version 当作同一版本。`check.py` 和包级 CI 会先运行相同的一致性校验。

## 什么时候升版

- patch：兼容性修复、文档和验证修正；是否形成发布由具体包的发布要求决定。
- minor：新增向后兼容的能力或工作流。
- major：不兼容的公开接口、安装合同或核心行为变更；0.x 包的破坏性变更遵循其现有包级合同并明确说明。
- 只改根索引、根 AGENTS 或其他包时，不连带升级未变更包。

版本来源、已有镜像和该包变更说明应在同一变更中更新。镜像必须一致，但不强行统一包内原有发布工具；Commerce installer 的最低兼容版本独立管理。迁移不抹掉版本历史，也不把已有源码版本自动标成新仓库已发布。已发布版本之后有内容改动时，下一次正式分发须采用新版本，不能重用旧版本冒充相同产物。

## 标签与交付

新仓库使用 `<包名>/v<版本>`，例如 `browser67/v0.11.5`、`design-craft/v0.7.1`；这些只是命名示例，不代表已经发布。包名来自 catalog，使用小写 `3d-craft`。所有包共用一个 Git 历史，但各自筛选自己的标签、Release 和资产。

发布顺序：确定包和版本 → 同步元数据与变更说明 → 运行包级检查和发布/live 门禁 → scoped commit/push → 核对精确 SHA → 在授权范围内创建不可覆盖的 annotated tag、Release 和包产物 → 回读验证。提交、推送、GitHub 发布、npm 发布和本机安装各自核对授权，不推断为同一步。

Release 说明绑定完整源码 SHA、包目录、验证范围以及真实产物的校验值；不以整个 monorepo 的源码压缩包冒充单包安装包。包内旧工作流不会自动执行；逐包迁移真实发布流程后才能启用对应入口，不能只加标签就宣称安装可用。遗留工具若接收裸版本标签，可在本地门禁中传裸版本；远端标签仍使用命名空间。
