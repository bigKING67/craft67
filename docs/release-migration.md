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
| design-craft | 根 `native-runtime.yml`、`benchmark.yml`、`release-certify.yml` | 已接入手动采集、operational candidate 和认证入口；认证成功证据、native 标签触发及正式发布仍待完成 |
| creative-craft | 根 Offline candidates → 原 `scripts/build_release.py` | 已接入离线候选；真实宿主模型调用和创意质量证据仍需独立验收 |
| review-craft | 根 Offline candidates → 原 `scripts/release_gate.py` | 本轮接入 Ubuntu 候选；旧包 CI 的同一 tarball 跨平台复验尚未迁入，真实宿主声明仍需单独验收 |
| money-craft | 根 Offline candidates → 原包检查与 `scripts/package_smoke.py` | 已接入实际打包和隔离 smoke；数据源 live 与研究质量证据仍需独立验收 |
| whoami | 根 Offline candidates → 原 `pack-skill.mjs` | 已接入精简导出、解包后生产依赖安装和 CLI 样例验证；宿主解读与真实行为证据仍需独立验收 |
| browser67 | 根 `browser67-platform.yml`；原 `npm run release:ready` | 已接入手动跨平台、remote-CDP 与覆盖率工作流；运行结果按精确 SHA 核对。真实 TMWD/live 发布门禁仍需完成 |
| commerce-growth-os | `scripts/build_release.sh <quality-evidence>` | 绑定有效质量回归证据，保留八 bundle 安装校验与 archive verifier；不以普通 validate 替代质量证据 |
| 3d-craft | 根 Offline candidates → 原 `scripts/release_gate.py` | 本轮接入离线候选；Blender、实际宿主与视觉声明仍按目标验收 |
| reverse-craft | 根 Offline candidates → `check:all` 与 exact-package smoke | 已接入源码字节核对及解包后 CLI 流程；真实宿主、browser67 和目标环境验收仍需独立执行 |
| write-craft | `scripts/release_check.py` | 先通过当前 Skill/用例摘要绑定的真实行为基线、评审器校准与真人阅读证据，再接入候选构建 |

包内旧 `.github/workflows/` 是历史参考，不会被 GitHub 自动执行。根 `check.yml` 当前是 Ubuntu 包级离线矩阵；不能据此声称旧多平台、native、benchmark 或发布工作流已经迁移。本页列出的是实际入口及缺口，不是所有门禁已通过的声明。

## 剩余四包的证据核对（2026-10-06）

- **Write Craft：发布检查失败（2026-10-06）；2026-10-09 起 0.3.0 已通过。** 当日在 `a15cc0c` 上 Skill 摘要、用例 digest 与旧基线不一致，缺完整 PASS、探索披露、评审器校准与真人阅读摘要。之后重新采集了证据：冻结的 0.3.0 Skill 在 Sonnet 5.5 生成、火山方舟 DeepSeek Flash 评审下 21 条回归用例全部通过，评审器校准 35/35，3 份真实文档真人验收的记录以 sha256 绑定（`packages/write-craft/evals/baselines/pi-v0.3.0.json`）。没有复制旧 PASS、改摘要或放宽门禁。2026-10-10 起 0.3.1 通过：31 条用例首次运行全部 PASS、无重评，评审器校准 35/35（同版本首次为 34/35），3 份真实文档真人验收记录以 sha256 绑定（`packages/write-craft/evals/baselines/pi-v0.3.1.json`）。
- **Commerce：证据输入待准备。** `tooling/build/package_release.py` 明确要求 quality-regression 通过、干净当前 HEAD、完整选择/执行/评审/校准层、活跃安装一致性，以及同一个显式指定模型。当前未提供符合新 HEAD 的质量证据包；未执行正式打包或触发付费模型评测。仓库中的评测用例不是通过证据。
- **Design：认证链迁移尚未完成。** operational/certified 产物构建需要 native observation、benchmark observation/result、证据目录及后续标签绑定校验。根手动认证入口已迁移，但尚未取得完整 tag-bound 认证成功证据，正式发布工作流仍在包内。本轮没有运行或宣称这些认证通过。
- **Browser67：先恢复平台验证入口。** 根 [Browser67 platform checks](../.github/workflows/browser67-platform.yml) 保留旧四格系统/Node 矩阵、Ubuntu 隔离 Chrome remote-CDP、覆盖率附件；只手动触发。它不访问用户浏览器配置，不运行真实 TMWD/Profile 验收，不代替 `release:ready` 中的 live、上游当前性与截图稳定性条件，因此暂不加入离线候选支持名单。

剩余缺口是实际验收和工作流迁移工作，不是缺少版本号。六个已接入包的候选入口继续独立可用。

## Design 证据采集入口

根 [Native runtime evidence](../.github/workflows/native-runtime.yml) 与 [Performance benchmark](../.github/workflows/benchmark.yml) 均只手动触发。前者复用原 iOS Simulator/Android Emulator 脚本、固定工具版本和证据格式；后者的 `mode=capture` 复用原性能测试命令，支持 smoke/full，默认 full；新增 `mode=operational-candidate`，详见下节。运行目录指向 `packages/design-craft`，第三方 emulator action 的脚本路径则从 Git 根显式定位。

这两个入口用于验证迁移后的采集能力。main 上的手动运行不是 tag-push native 证据，不满足最终认证要求。只有审阅实际完成的 run、产物和源码绑定后，才能引用其中通过的单项证据；性能采集不是匹配 baseline 的回归验收，模拟器不是物理设备或跨 Agent 产品质量证明。

认证迁移状态与剩余条件：

1. 已迁移本地 tag-bound observation、metadata、assets、native bundle 和 certification 校验：仅接受当前版本的 `design-craft/v<version>`，拒绝裸标签及其他包标签；旧标签与旧证据保留为历史，不作为当前认证输入。认证附件采用 `release-certification-design-craft-v<version>-<run_id>`，避免标签中的斜杠进入附件名。远端检查器已改为查询根 `check.yml` 与 `native-runtime.yml`；包内历史工作流仍不能直接作为新仓库入口。
2. 根手动认证工作流已适配 main checkout、包 cwd、artifact 路径和命名空间标签；保留精确 SHA、确认输入及已有 Release 拒绝条件。正式发布工作流尚未迁移。
3. native tag-push、对应 benchmark 与认证 run 的精确 SHA、事件、workflow、attempt 和产物 digest 绑定。
4. certified 等级所需的真实物理设备与各宿主证据；本轮不触发 self-hosted 物理设备流程，不执行会写本机安装目录的 `publish-local`。

在上述合同迁移和验证完成之前，不启用根自动 tag 触发或发布工作流，不将 Design 加入离线候选列表。

## Design 手动候选与认证

`benchmark.yml` 默认 `mode=capture`，不进行安装或认证。选择 `mode=operational-candidate` 时：

- 必须从当前版本的 annotated `design-craft/v<版本>` 标签运行，标签目标必须等于运行 SHA；不接受 main、裸标签、其他包标签或 lightweight tag。
- `native_run_id` 必须对应同一 SHA、同一 Design 标签的成功 native push run；使用原 observation 校验器核对 workflow、事件、attempt 与最新运行，不以名称相同或旧运行成功替代。
- `benchmark_baseline` 是包内 `benchmarks/baselines/` 下已提交的文件；需要通过原 runner/指标合同及性能回归检查，不自动刷新旧 baseline。
- 在 GitHub 临时 runner 中执行原 `release-readiness-operational`，包括源码门禁、隔离安装和 operational 证据要求；不改用户本机安装。
- 附件 `operational-candidate-<run_id>` 保留 native observation、`benchmark-result-full.json` 和 `dist/evidence/operational-95-candidate.json`。附件存在不等于成功，消费者还必须验证对应 run 成功及 SHA 绑定。

根 [Release certification](../.github/workflows/release-certify.yml) 只在 main 手动运行，输入现有 annotated Design 标签、native/benchmark run ID、包内 baseline 路径和 `certify-<完整标签>`。它重新观察指定运行、下载证据、执行 final 门禁、构建并验证认证包。源码 main、运行 SHA 和标签目标必须相同；不创建标签、不发布 Release、不授予 contents 写权限。附件采用不含斜杠的名称 `release-certification-design-craft-v<版本>-<run_id>`，工作流上传路径从仓库根指向包内产物。

**尚未完成真实认证运行。** native 标签 push 触发仍未启用，现有 main 手动采集不能用作最终认证输入；需要后续在已确认的版本提交上取得合格 native、baseline 和宿主证据。`certified_100` 还要求 physical-device observation 和四宿主证据，根物理设备工作流尚未迁移，该等级目前不可完成。新增入口不改变这些门禁，也不代表十个包均已可正式发布。

当前认证证据的现场结果、真实评测调用清单和执行顺序见 [Design 认证证据核验与执行清单](design-certification-checklist.md)。
