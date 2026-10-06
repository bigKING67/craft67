# craft67

集中维护 Craft 工程与 Agent Skills 的源码仓库。10 个项目、18 个独立 Skill，保留各自的运行代码、测试、依赖与许可证。

## 项目与入口

| 项目目录 | Skill |
| --- | --- |
| [design-craft](packages/design-craft) | design-craft |
| [creative-craft](packages/creative-craft) | creative-craft |
| [review-craft](packages/review-craft) | review-craft |
| [money-craft](packages/money-craft) | money-craft |
| [whoami](packages/whoami) | whoami，含 TypeScript 计算核心 |
| [browser67](packages/browser67) | browser67、js-reverse，含 CLI、MCP 与浏览器扩展 |
| [commerce-growth-os](packages/commerce-growth-os) | 4 个商业 Skill、4 个营销 Skill |
| [3d-craft](packages/3d-craft) | 3d-craft |
| [reverse-craft](packages/reverse-craft) | reverse-craft |
| [write-craft](packages/write-craft) | write-craft |

`catalog.json` 登记确切入口和包级验证命令。日常开发在对应包目录进行；Git 操作属于 craft67 主仓库。上游参考仍通过固定版本 submodule 管理。

## 开发与验证

```sh
git submodule update --init --recursive
python3 scripts/check.py --list
python3 scripts/check.py --package whoami
```

先在有 `package-lock.json` 的对应包目录运行 `npm ci --ignore-scripts`。Python 门禁使用 Python 3.12+；Review Craft 还需要 uv，并按包内锁文件准备环境。检查脚本不自动安装到全局，不提交，不发布。

根 `.github/workflows/check.yml` 是统一的包检查入口。包内 `.github/` 保留原工程合同和发布参考，不会被 GitHub 自动作为根工作流执行。原发布工作流尚未切换到本仓库，独立包的版本与发布状态保持原语义。

## 使用与安装

按需使用一个或多个 Skill，不必全部加载。包内 `SKILL.md` 及随附代码是维护源；`~/.agents/skills` 等位置是宿主安装入口。

- Design / Creative / Money / 3D：使用各包已有安装器及其目标目录参数，保留校验、备份和回退机制。
- Commerce：必须通过 `packages/commerce-growth-os/scripts/install.sh` 构建或安装，确保共享合同被装入八个独立 bundle。
- Whoami：本地开发可链接到 `packages/whoami`，先安装依赖并构建；独立分发使用包内 `npm run pack:skill -- <不存在的目标目录>`。
- Browser67：Skill 安装与 CLI/MCP/扩展安装分开，按包内 README 操作。
- Review / Reverse / Write：使用包内现有独立 Skill 或包分发入口。

包内指向旧仓库的发布链接及安装命令代表既有发布来源，不能据此假定 craft67 已发布。新仓库源码入口以本页和 catalog 为准。安装文件一致不代表已打开的宿主会话加载了新版本。

## 迁移与许可

来源提交、文件计数与导入摘要见 [migration-sources.json](docs/migration-sources.json)，验收及待办见 [migration.md](docs/migration.md)。本次采用源码快照导入；原仓库历史留在原目录，未改写或删除。根仓库不重新许可各包，许可证和第三方声明随原路径保留。

凭据、本地执行配置、个人资料、依赖目录、缓存和运行输出不属于公开源码。原目录清理、正式提交、推送、发布均需分别核对授权。
