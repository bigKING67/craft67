# craft67

## 作用域与目录

- `catalog.json` 登记维护的包、Skill 入口、版本来源和包级检查命令；数量与名称以 catalog 为准。
- 日常实现、依赖和测试在 `packages/<name>/` 内；改动前读取该包及更近目录的 `AGENTS.md`。包级规则继续适用，不把不同 Craft 的工作流混为一套。
- craft67 是唯一主仓库 Git 根。包目录不是独立仓库；Git 状态、提交、标签和根工作流都属于 craft67。先查状态，仅 scoped add/commit，保留其他包与并行任务的 WIP。
- 保留包边界、Skill 名称、许可证、独立安装能力和测试合同。日常任务只修改授权范围；跨包改动先识别真实调用方和共同验证范围。
- 固定版本的 upstream submodule 是只读参考；不要直接编辑其内容或在普通检查中更新 pin。包内 `.github/` 是历史流程参考，只有根 `.github/workflows/` 会运行。

## 版本与发布

- 各包独立版本，不为整合或其他包改动统一涨号；craft67 集合快照由 Git commit SHA 标识。规则见 `docs/versioning.md`。
- `catalog.json` 只登记版本来源，不复制版本值。改版本时同步该包已有的 VERSION、package/lock、Python 等镜像和变更说明，并运行 `python3 scripts/versions.py --check`。
- 新标签采用 `<catalog 包名>/v<版本>`；不可跨包解析“最新 Release”，不可覆盖旧标签。包内工具需要裸 `vX.Y.Z` 时按该工具合同传入，不因此改变远端标签命名。
- 版本号、源码提交、GitHub Release、已安装文件及运行中的宿主是不同状态。迁移来源 `docs/migration-sources.json` 和旧验收只是历史证据，不能当作新版本发布或运行态证明。
- 发布前执行该包的发布门禁；根离线 CI 不能代替 live、目标平台或真实安装验收。未迁移的旧仓库下载入口不得作为可用入口推荐。

## 验证与交付

- `python3 scripts/versions.py` 查看版本；`--check` 检查版本来源与现有镜像一致。
- `python3 scripts/check.py --list` 查看命令；`python3 scripts/check.py --package <name>` 先检查版本，再在包目录运行离线检查。多个受影响包可重复传 `--package`；不传则运行全部包。
- 修改 catalog、根检查器或 CI 时检查所有包元数据，并运行 `python3 -m unittest discover -s scripts -p 'test_*.py'`；修改包内容时跑对应包门禁。只有新增风险、失败或既定门禁需要时扩大验证。
- 需要检查 submodule 工作树时先按 README 初始化，再运行 `python3 scripts/verify-layout.py`；缺失 checkout 不能当作 pin 已核验。
- 源码、离线测试、安装一致性、宿主加载、live/平台验收和远端发布分别报告。指令文件静态检查不等于新会话行为已验证。

## 安装、数据与授权

- 包内 Skill 和代码是维护源；`~/.agents/skills`、`~/.codex/skills` 等是宿主安装入口。源码修改不自动授权全局安装或刷新正在运行的宿主。
- Commerce 使用自己的构建/安装器装配共享合同；Browser67 的 Skill 与 CLI/MCP/扩展安装分开；其余沿用各包入口，不批量复制全局 Skill 或宿主配置。
- 凭据、本地执行配置、个人资料、依赖目录、缓存和运行输出不纳入源码；本次临时产物放既有忽略目录或系统临时目录，不新建永久备份。
- 安装、commit、push、tag/Release、发布和旧目录清理分别核对已有授权；授权已覆盖的步骤不重复确认。包门禁通过不自动授予外部动作权限。
