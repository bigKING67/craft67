# 迁移历史记录（阶段快照）

日期：2026-10-06。

> 本页保留不同迁移阶段的原始记录，后文“未 push”“原目录仍保留”“CI 尚未远程执行”等均是当时状态，不代表当前状态。源码已统一到 `packages/`，统一 CI 已运行，旧目录与旧远端的后续处置见 [退役记录](remote-retirement.md)。使用入口以 [根 README](../README.md) 为准，版本规则见 [版本与发布](versioning.md)，最新 CI 以对应提交的 [Actions](https://github.com/bigKING67/craft67/actions/workflows/check.yml) 为准。
>
> 当前结构门禁为 `scripts/verify-layout.py`；原迁移快照核对保留为 `scripts/verify-migration.py`，需初始化上游 checkout，旧源目录已删除时不能重做原目录逐文件比较。历史 pin 不约束后续正常升级。

## 安装切换更新

以下为本地导入阶段之后的更新；后文“未 push”“6 个差异”等描述保留为当时的阶段记录，仅用于还原该阶段。

- GitHub main 已推送，提交 `bd923f5` 的统一 CI 10/10 通过（run `37440612021`）。
- Creative 的 6 个安装差异已审阅并从新源码原子更新，保留原安装备份；Design、Money 的安装来源记录已更新到 craft67。
- Creative/Money 安装器已改用 craft67 仓库及准确 Skill 子目录记录来源。Reverse 独立安装的 browser67 查找先尝试新 monorepo 位置，显式环境变量仍优先、旧位置作为兼容回退。
- Reverse 安装已原子切换并备份；从安装副本执行路径选择，实际选中 craft67/packages/browser67。
- 18 个 Skill 安装内容一致：10 个普通入口逐文件比较，8 个商业营销入口通过原生 bundle 校验。
- 新 Codex 启动上下文在 developer Skill catalog 中发现全部 18 个入口，别名展开后对应文件均存在。新的只读 Codex 会话实际通过文件工具读取了 design-craft、creative-craft、money-craft、reverse-craft、whoami 五个入口，命令均成功。此为显式入口读取验收，不等于所有 Skill 的自然语言路由或领域执行验收。
- 回归：Creative 安装器测试 7/7、Money 合同测试 13/13、Reverse check:all 通过。
- 安装回退路径、一致性、新会话工具读取证据保留于 gitignored `.migration-local/`。原项目目录仍保留，未做清理。


## 已完成

- 从 10 个原仓库的本地 HEAD 对应受控文件导入 3,645 个文件，原始内容合计 29,436,172 字节；逐包提交与导入内容摘要见 `migration-sources.json`。
- 统一源码位置为 `craft67/packages/<name>`；`3D-Craft` 映射为 `packages/3d-craft`。登记 18 个唯一 Skill。
- craft67 已初始化为 main，origin 配置为 `https://github.com/bigKING67/craft67.git`。已创建本地导入提交 `f3268b2f25f2dd034a2acbc1901ebfedf547c5af`；未执行 push、tag 或发布。
- 9 个上游参考保留固定提交、独立 Git 对象和根 `.gitmodules` 注册；10 个主包没有嵌套 `.git`。包内旧 `.gitmodules` 保留供原包合同校验，Git 的有效注册位于仓库根。
- 原仓库、原历史和未跟踪资料保持原位。未导入原 `.git` 历史、node_modules、个人资料、运行缓存或未跟踪文件。
- 原已跟踪 `.codex/config.toml` 也从公开源码导入中排除，排除清单逐包记录。原文件保持不动。
- 统一检查入口为 `scripts/check.py`；结构与上游锁定检查入口为 `scripts/verify-layout.py`。

## 迁移适配

- browser67：变更统计和按变更选测限定到当前包，路径转换为包相对路径；加入带兄弟文件、非默认 Git status 配置的真实嵌套仓库回归。
- design-craft：历史证据读取支持包相对 Git 路径；安装来源区分包根与 Git 根；Git 快照使用真实 Git 根。隐私门禁在 craft67 扫描整个包历史（包括首次导入），原独立仓库仍使用原基线；缺失 HEAD 仍失败。回归验证已删除的敏感路径仍能从历史检出、兄弟包不混入本包检查。
- reverse-craft：源码必需文件列表不再要求本地 `.codex/config.toml`。所有功能、场景、路由、安全与包边界门禁保留。
- 各包 Skill 正文和运行功能未因迁移改写。源码移入不等于重发已有版本。

## 验证结果

| 包 | 结果及范围 |
| --- | --- |
| design-craft | PASS：正式导入提交 `f3268b2`，25 个 portable 门禁，包括源码测试、安装回退合同与新增隐私历史回归 |
| creative-craft | PASS：源码验证、185 个测试、包检查 |
| review-craft | PASS：本地 release_gate 命令，243 个测试、lint、源码检查、87 文件包及隔离安装 E2E；不代表正式发布 |
| money-craft | PASS：源码检查、558 个测试（29 skipped）、包检查 |
| whoami | PASS：typecheck、252 个测试、build；切换后安装链接下 CLI --help 成功 |
| browser67 | PASS：正式导入提交 `f3268b2`，check tier 50 步；不代表新安装运行态、真实浏览器或其他操作系统验收 |
| commerce-growth-os | PASS：原生 deterministic 门禁、8 个自包含 bundle、原生已安装 parity |
| 3d-craft | PASS：源码验证、44 个 Python 测试、3 个 Node 测试、viewer typecheck/build；未做 Blender 或视觉验收 |
| reverse-craft | PASS：check:all（源码、单测、264 路由、11 场景） |
| write-craft | PASS：源码验证、61 个测试、包检查 |

首次提交前，`design-craft` 和 `browser67` 在临时已提交副本中通过检查。随后已在正式仓库的导入提交 `f3268b2f25f2dd034a2acbc1901ebfedf547c5af` 上重新运行：design-craft 25 个 portable 门禁、browser67 check tier 50 步全部通过，测试后工作区干净。此处的后续记录提交只更新本迁移文档，不改动已验收源码。原项目依赖未改动。

本地日志、安装差异、路径切换回退记录和临时副本位置在 gitignored `.migration-local/`。根 CI 已配置但尚未远程执行；包内旧 CI 与发布工作流作为原工程资料保留，不自动执行。

## 安装与路径

- `~/.codex/skills/whoami` 的原符号链接已改到 `craft67/packages/whoami`。计算核心已在新路径构建。
- `~/.codex/rules/browser.md` 中唯一旧 browser67 集成文档路径已替换为新包路径，其他条款未改。
- 其他普通 Skill 已核对源文件：design/review/money/browser67/js-reverse/3d/reverse/write 文件一致；commerce 使用原生校验器确认 8 个安装包一致。
- creative-craft 的原安装副本与当前源码有 6 个文件差异，保留现有安装，未顺带升级。差异为 `references/image-production.md`、`references/video-production.md`、`schemas/image-job-v2.schema.json`、`schemas/image-job.schema.json`、`scripts/creative_craft_video.py`、`scripts/creative_craft_contracts.py`。
- browser67 全局 CLI 是独立安装包，未链接原源码目录，因此未重装 CLI、MCP 或扩展。
- reverse-craft 源码的相邻 browser67 推导在新 packages 结构下仍成立；已安装独立副本的开发机 fallback 仍可能引用旧 browser67 目录，旧目录清理前需随安装切换复核。安装来源元数据也不因源码复制而自动刷新。
- 未开展新模型会话的 Skill 加载验收；文件一致、CLI 成功与实际宿主加载分别成立。

## 剩余限制与后续

- 原项目保留用于回退，后续主要开发应进入 craft67。清理旧目录需再次确认确切范围及安装/运行依赖。
- 本地首次 commit 已获授权并执行；push 和 release 未授权、未执行。旧仓库发布链接、独立版本及历史证据保留原含义；首次发布前需单独设计发布工作流和新安装链接。
- 初始导入 diff 的 whitespace 检查发现原文件已有 CRLF/尾空格等问题；本次不为迁移批量改写原内容。迁移适配的增量 diff whitespace 检查通过。
- 按已有锁文件安装依赖时，npm 报 browser67 3 项漏洞（1 moderate、2 high），3d-craft 2 项 high；此次未升级依赖，不能视为依赖安全审计通过。
- 有限凭据模式扫描未发现候选，但不替代公开发布前的内容和许可证审查。根仓库不统一重新许可各包。
