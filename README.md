[English](README.en.md) · 简体中文

# craft67

集中维护 Craft 工程与 Agent Skills 的源码仓库：设计、创意、工程审查、投资研究、商业经营、浏览器操作等能力在同一处维护，各包保留独立版本、依赖、测试与许可证。目前包含 10 个项目、18 个 Skill；准确入口和检查命令以 [catalog.json](catalog.json) 为准。

## 选择能力

| 项目与使用说明 | 用途与产出 | Skill |
| --- | --- | --- |
| [Design Craft](packages/design-craft/README.md) | Web、桌面与原生界面设计、实现和视觉验证 | design-craft |
| [Creative Craft](packages/creative-craft/README.md) | 广告概念、文案、艺术指导、图像 Brief 与视频方案 | creative-craft |
| [Review Craft](packages/review-craft/README.md) | 有覆盖范围和证据的工程审查、整改与验收 | review-craft |
| [Money Craft](packages/money-craft/README.md) | 投资研究、财报、估值与组合分析 | money-craft |
| [Whoami](packages/whoami/README.md) | 八字、紫微排盘计算与有依据的解读 | whoami |
| [Browser67](packages/browser67/README.md) | 真实浏览器操作及授权范围内的前端 JS 逆向；含 CLI、MCP 和扩展 | browser67、js-reverse |
| [Commerce Growth OS](packages/commerce-growth-os/README.md) | 商业策略、营销、平台运营与经营分析 | 4 个商业 Skill、4 个营销 Skill |
| [3D Craft](packages/3d-craft/README.md) | Blender 产品道具、GLB 与 Web3D 查看器的制作和验证 | 3d-craft |
| [Reverse Craft](packages/reverse-craft/README.md) | 授权范围内的逆向、CTF、DFIR、协议与威胁证据分析 | reverse-craft |
| [Write Craft](packages/write-craft/README.md) | 将复杂方案、进展与工程说明整理为读者可判断、可行动的文档，并审查改写项目 README | write-craft |

## 使用 Skill

1. 从上表选择所需能力，阅读对应包的 README，按包内说明安装或构建。
2. 在宿主中启用相应 Skill；按需加载，不必一次安装全部能力。
3. 源码更新后按对应安装器同步，并在新会话验证加载。文件一致不等于正在运行的会话已加载新版本。

获取维护源：

```sh
git clone https://github.com/bigKING67/craft67.git
cd craft67
```

各包的安装方式不同：Design / Creative / Money / 3D 使用现有安装器及目标目录参数；Commerce 必须通过包内 `scripts/install.sh` 构建或安装，装配八个独立 bundle 所需的共享合同；Whoami 先安装依赖并构建，独立分发使用 `npm run pack:skill -- <不存在的目标目录>`；Browser67 的 Skill 与 CLI/MCP/扩展分别安装。Review / Reverse / Write 沿用包内分发入口。

`packages/` 是维护源，`~/.agents/skills` 等目录是宿主安装副本。旧的 10 个 GitHub 仓库已删除，历史下载链接不可作为安装入口；新发布以 [craft67 Releases](https://github.com/bigKING67/craft67/releases) 中对应包的实际状态为准。

## 开发与验证

日常开发在 `packages/<name>/` 内进行，Git 操作属于 craft67 根仓库。改动前读取根及包内 `AGENTS.md`。

根检查器使用 Python 3.12+ 和 Git。JavaScript 包的统一 CI 使用 Node 24；Whoami 的固定验收证据绑定 **Node 24.18.0**。Review Craft 还需要 uv；其他依赖和平台要求见各包 README。检查器不代替依赖安装。

```sh
# 查看版本、检查命令与当前目录/注册关系
python3 scripts/versions.py
python3 scripts/check.py --list
python3 scripts/verify-layout.py

# 根元数据与检查器回归
python3 scripts/versions.py --check
python3 -m unittest discover -s scripts -p 'test_*.py'

# 示例：准备 Whoami 依赖后运行其门禁
cd packages/whoami
npm ci --ignore-scripts
cd ../..
python3 scripts/check.py --package whoami
```

多个受影响包可重复传入 `--package`；不传则检查全部包，须先准备所有包的依赖。检查命令不自动全局安装、提交或发布。

需要上游参考内容或校验实际 submodule checkout 时：

```sh
git submodule update --init --recursive
python3 scripts/verify-layout.py --check-checkouts
```

默认结构检查核对 catalog、目录、根 `.gitmodules` 和当前 Git index 的 pin；不会把未初始化的 checkout 当作已验证。历史迁移审计独立保留在 `scripts/verify-migration.py`，不用于日常开发门禁。

## CI 与版本

[根统一工作流](.github/workflows/check.yml) 先验证结构和版本元数据，再从 catalog 生成所有包的检查矩阵；同一事件与分支的新运行会取消尚未完成的旧运行。Browser67 另有手动触发的 [多平台与隔离浏览器检查](.github/workflows/browser67-platform.yml)。Design 的 [native 证据](.github/workflows/native-runtime.yml)、[性能采集/候选验证](.github/workflows/benchmark.yml)和[认证入口](.github/workflows/release-certify.yml)也采用手动触发；入口存在不代表认证通过，具体前提见发布迁移文档。结果见 [Actions](https://github.com/bigKING67/craft67/actions/workflows/check.yml)。包内 `.github/` 保留原工程合同和发布参考，不会被 GitHub 自动作为根工作流执行。

各包独立版本，标签采用 `<包名>/v<版本>`；craft67 整体快照由 commit SHA 标识。版本来源、镜像同步和发布约束见 [版本与发布](docs/versioning.md)。源码版本、CI 通过、正式 Release、已安装文件和宿主运行态是不同状态；离线 CI 不替代真实浏览器、目标平台或正式安装验收。原发布工作流尚未全部切换到本仓库；候选构建入口与逐包缺口见 [发布流程迁移](docs/release-migration.md)。

## 迁移记录与许可

本仓库采用源码快照导入，不包含完整旧仓库历史。来源提交和导入摘要见 [migration-sources.json](docs/migration-sources.json)，阶段验收见 [迁移历史记录](docs/migration.md)，旧目录与旧远端的后续处置见 [退役记录](docs/remote-retirement.md)。历史记录中的阶段状态不代表当前安装或发布状态。

根仓库不重新许可各包，许可证和第三方声明随原路径保留。凭据、本地执行配置、个人资料、依赖目录、缓存和运行输出不属于公开源码。
