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
- `python3 scripts/verify-layout.py` 检查当前 catalog、目录与 Git index 中的 submodule 注册；`--matrix` 生成 CI 矩阵。实际 checkout 校验须先初始化，再加 `--check-checkouts`。`scripts/verify-migration.py` 仅核对历史导入快照，不作日常结构门禁；缺失 checkout 不能当作工作树 pin 已核验。
- 源码、离线测试、安装一致性、宿主加载、live/平台验收和远端发布分别报告。指令文件静态检查不等于新会话行为已验证。

## 安装、数据与授权

- 包内 Skill 和代码是维护源；`~/.agents/skills`、`~/.codex/skills` 等是宿主安装入口。维护任务涉及 Skill 安装内容变更时，默认同步其已知本机安装，先核对目标与现有差异、保留合理回退手段并验证一致性；刷新正在运行的宿主仍须相应授权。
- Commerce 使用自己的构建/安装器装配共享合同；Browser67 的 Skill 与 CLI/MCP/扩展安装分开；其余沿用各包入口，不批量复制全局 Skill 或宿主配置。
- 凭据、本地执行配置、个人资料、依赖目录、缓存和运行输出不纳入源码；本次临时产物放既有忽略目录或系统临时目录，不新建永久备份。
- 常规维护默认授权范围内实现、必要验证、scoped commit 和向已配置目标的普通 push；只读请求及用户明确限制优先，不逐项请示。
- 自动核对任务文件、暂存差异、待推提交、远端/分支和副作用，保留无关 WIP；推送若触发生产部署，先核对该流程是否已有授权。
- tag/Release、正式发布/部署、破坏性 Git 和旧目录清理仍核对相应授权；已有授权覆盖时直接执行。源码、提交、推送、CI、安装与宿主加载分别核验，不以默认授权或包门禁冒充完成证据。
- 本节规定维护代理的交付授权；包内工具的只读、不自动提交/推送/合并等产品合同继续适用。
