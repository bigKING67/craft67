# 发布流程迁移

本页描述 craft67 的发布准备入口与尚未迁移的门禁。2026-10-06 核对时，GitHub Release 列表为空；版本文件存在不表示已发布。具体版本始终读取 catalog 指定的来源，正式发布遵循 [版本与发布](versioning.md)。

## 离线候选构建

根 [Offline candidates 工作流](../.github/workflows/candidate.yml) 只接受手动触发，当前支持 Review Craft、3D Craft、Creative Craft、Whoami、Money Craft 与 Reverse Craft。使用各包已有候选门禁，不取代它们：

- Review Craft：运行完整 `scripts/release_gate.py`，保留经过隔离安装、doctor 与工程 E2E 的同一份 tarball 和回执。
- Creative Craft：运行原 `scripts/build_release.py`，保留 lint、schema、host package smoke、exact-package smoke、校验文件与原构建回执。host package smoke 是离线安装合同，不等于真实宿主模型调用。
- Money Craft：先运行 catalog 中的源码与测试门禁，再对实际保留的 tarball 执行原 `package_smoke.py`，覆盖隔离原子安装、自测、禁用 Provider 的研究工作区与财报流水线。
- Reverse Craft：先运行 `check:all`，再对实际 tarball 核对源码允许清单与逐字节一致性；在临时目录运行解包后的隔离 Python CLI，验证路由、案例、证据、发现、路径、报告与封存流程。npm 仍为 private。
- Whoami：运行源码检查和原 `pack-skill.mjs` 精简导出器，将 ZIP 解包后只安装生产依赖，验证 CLI 帮助及合成样例计算与源码一致。CI 固定 Node 24.18.0；这不证明命理现实预测有效。
- 3D Craft：运行 `scripts/release_gate.py`，两次构建 ZIP 比较 SHA-256，验证独立解包副本、glTF 校验器与 doctor，保留原候选证明。

根封装额外要求干净源码、构建前后 SHA 不变，记录包版本、完整源码 SHA、包路径与各产物 SHA-256。产物存于 runner 临时目录，通过 Actions 附件保留 7 天；独立下载任务重新核对身份、完整文件集合与校验值，校验不符直接失败。校验值用于发现文件变化，不构成独立签名或供应链认证。

本地已准备对应包依赖后，也可以构建到仓库外不存在的目录。Money 的源码门禁还要求初始化其固定 AI Berkshire 上游（候选工作流会执行该步骤）：

```sh
git submodule update --init --recursive -- packages/money-craft/upstreams/ai-berkshire
```

构建与复核示例：

```sh
python3 scripts/candidate.py build --package review-craft --directory /tmp/review-craft-candidate
python3 scripts/candidate.py verify --package review-craft --directory /tmp/review-craft-candidate --expected-sha <完整源码SHA>
```

验证下载包时，本地必须检出其绑定的 SHA；不覆盖已有产物，不安装到全局，不创建 tag、GitHub Release 或 npm 发布。该入口只证明 Ubuntu 离线候选构建及下载完整性，不代表模型质量、真实宿主、浏览器、跨平台或视觉验收。3D 原回执中的 `release_eligible` 仅表达其原门禁的源码条件；根候选仍不是正式 Release。

## 各包迁移范围

| 包 | 已有入口 | 下一步需要完成的发布准备 |
| --- | --- | --- |
| design-craft | 包内 `release-certify.yml`、`release-publish.yml` | 成套迁移 native/benchmark/认证/发布依赖；适配子目录、命名空间标签和远端 run/artifact 身份，保持认证证据绑定 |
| creative-craft | 根 Offline candidates → 原 `scripts/build_release.py` | 已接入离线候选；真实宿主模型调用和创意质量证据仍需独立验收 |
| review-craft | 根 Offline candidates → 原 `scripts/release_gate.py` | 本轮接入 Ubuntu 候选；旧包 CI 的同一 tarball 跨平台复验尚未迁入，真实宿主声明仍需单独验收 |
| money-craft | 根 Offline candidates → 原包检查与 `scripts/package_smoke.py` | 已接入实际打包和隔离 smoke；数据源 live 与研究质量证据仍需独立验收 |
| whoami | 根 Offline candidates → 原 `pack-skill.mjs` | 已接入精简导出、解包后生产依赖安装和 CLI 样例验证；宿主解读与真实行为证据仍需独立验收 |
| browser67 | `npm run release:ready` | 迁移旧跨平台、remote-CDP 与覆盖率 CI；按发布目标完成真实 TMWD/live 门禁，之后才准备新版本标签 |
| commerce-growth-os | `scripts/build_release.sh <quality-evidence>` | 绑定有效质量回归证据，保留八 bundle 安装校验与 archive verifier；不以普通 validate 替代质量证据 |
| 3d-craft | 根 Offline candidates → 原 `scripts/release_gate.py` | 本轮接入离线候选；Blender、实际宿主与视觉声明仍按目标验收 |
| reverse-craft | 根 Offline candidates → `check:all` 与 exact-package smoke | 已接入源码字节核对及解包后 CLI 流程；真实宿主、browser67 和目标环境验收仍需独立执行 |
| write-craft | `scripts/release_check.py` | 先通过当前 Skill/用例摘要绑定的真实行为基线、评审器校准与真人阅读证据，再接入候选构建 |

包内旧 `.github/workflows/` 是历史参考，不会被 GitHub 自动执行。根 `check.yml` 当前是 Ubuntu 包级离线矩阵；不能据此声称旧多平台、native、benchmark 或发布工作流已经迁移。本页列出的是实际入口及缺口，不是所有门禁已通过的声明。
