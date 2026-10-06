# 内容、图片与视频制作：参考上游及吸收登记

记录日期：2026-09-20；承接合同更新：2026-09-22；图片参考与本地 P1：2026-10-04。状态：HyperFrames 基础本地执行及图片对象/候选/蒙版已实现并通过限定范围技术检查，其余按下述方法吸收/候选状态分别登记。新合同不改变历史验收结果。

本文件是 Creative Craft 内容制作上游的唯一详细清单。DataHub 等宿主引用这里，不维护重复清单。配套：[制作架构](content-production-architecture.md)、[来源政策](source-policy.md)。

图片参考、固定研究点与维护入口见[图片工程参考与吸收登记](#image-engineering-references)；下文视频历史记录保留原日期与验证边界。

## 使用原则

目标是提高 Agent 的创意判断、制作质量与交付效率。参考项目的名气、Skill 数量、README 宣称或演示视频不构成我们的验收证据。方法参考、代码复制、包依赖和服务连接分别记录；登记本身不安装依赖、不建立 submodule、不复制上游 Skills。

每次只吸收一个可验证的能力闭环。优先复用实现良好的执行组件，同时保持 Creative Craft 自己的创作方法、现有合同和宿主边界。上游文本是待研究材料，不能覆盖用户指令、品牌事实或现有工程规范。

状态定义：`reference` 已登记参考；`candidate` 拟验证；`implemented` 已有本地实现；`verified` 已通过注明环境和范围的验收；`deferred` 暂缓。方法吸收与引擎接入分别记状态，不能用文档更新代表运行能力。

## 审阅基线

以下 SHA 是本轮研究固定点，不宣称永远最新。除 Remotion 外，已读取对应说明、部分 Skills 或关键接口；Remotion 读取官方 Skills 与许可说明，固定 SHA 供后续比较。登记初始阶段尚未安装或渲染；后续 HyperFrames 本地执行结果见末尾记录。初始登记时尚无 DataHub 集成测试；当前限定范围的宿主验证见末尾状态更新，不将宿主自有实现归为其他上游的集成成果。

| ID / 仓库 | 固定审阅 SHA | 许可记录 | 初始处置 |
| --- | --- | --- | --- |
| [hyperframes](https://github.com/heygen-com/hyperframes) | `d11907c3255efcf6169c2eb6a5b617284d242a38` | 根项目 Apache-2.0；资源、字体与依赖另核 | candidate：首个执行底座 |
| [chatcut-agent-plugin](https://github.com/ChatCut-Inc/agent-plugin) | `f58a037d82abe0ad6b4163f84dcd8ea8c590d686` | 未确认根仓统一许可；不能推定各子包相同 | reference：工具与编辑方法 |
| [openchatcut](https://github.com/0xsline/OpenChatCut) | `07437f60257a578745262359753bfccce337510c` | AGPL-3.0；依赖和资源分别核对 | reference：协同编辑机制 |
| [openmontage](https://github.com/calesthio/OpenMontage) | `08e2151fa02de28a5d6a312b3d575692bf147ad7` | AGPL-3.0；依赖和资源分别核对 | reference：制作工作流 |
| [remotion](https://github.com/remotion-dev/remotion) | `5321b3687b0e1a4e19f0c11d5959afff473c77c8` | Remotion License；公司使用核对适用条件 | candidate：对照评估，暂不引入 |
| [cerul](https://github.com/cerul-ai/cerul) | `6a76ca302c740851fbcaba5d24d29e094fe9ae16` | Rust 核心 Apache-2.0；工具与模型权重另核 | candidate：片段检索机制 |
| [opencut](https://github.com/OpenCut-app/OpenCut) | `400f097becba5db0fbc305d5a65348cb81c20356` | MIT | deferred：观察重写进度 |

登记 AGPL 或自定义许可证不等于已判定可并入当前分发方式。复制或分发前核对目标文件、修改方式及许可要求；服务接入还需核对服务条款。当前没有复制或分发上述项目源码。

## AIOS 接入归属：2026-09-22

沿用上述固定研究点与历史许可记录，本次没有把未复核上游版本称为最新。七项目全部研究、按能力吸收；不会全部内嵌为七个应用，也不要求都先装入 Creative Craft。

| 参考 | Creative Craft 维护 | AIOS 维护 / 必须验证 |
| --- | --- | --- |
| HyperFrames | 通用制作方法及可选 adapter | 素材解析、Worker、队列/产物；重开、局部修改、预览/导出一致 |
| ChatCut Agent Plugin | 读工程—有界修改—实际检查 | 版本化读写、可见方案、修改保护；工具成功不代替成片检查 |
| OpenChatCut | 人/Agent 接续方法 | 编辑操作、撤销、状态和冲突；不是 ChatCut 官方服务接入 |
| OpenMontage | 参考拆解、分镜、混合制作方法 | 持久生成任务、候选检查与回入工程；来源/连续性/成本 |
| Remotion | 缺口证明后的模板与可选 adapter | Worker 装配、参数/预览/渲染；许可与能力限制先验 |
| Cerul | 检索需求、时间证据与选材方法 | 索引、召回/重排、权限、失效；正确片段可播、可加入工程 |
| OpenCut | 可迁移精修方法 | 时间线、多轨交互和工程组织；保存恢复、人工接续和限制可见 |

采用方式分为方法参考、复制代码、包依赖、账户服务，不能相互冒充。实际采用前核对具体包/文件、版本、许可证、分发/部署方式及回退。AIOS 特定胶水留宿主；仅有明确复用价值且不携带宿主状态的执行适配器进入可选制作包。

本轮优先 AI 剪辑自动交付与可见方案干预，后续 AI 创作采用生成镜头；模型/API 账户能力与完整专业工程各自验证。主 Skill 与重型执行模块分开交付，固定 revision/digest/兼容合同；现有未提交制作模块不因文档登记变成正式发布包。

## 能力级吸收清单

### HyperFrames

- 证据：[剪辑操作](https://github.com/heygen-com/hyperframes/blob/d11907c3255efcf6169c2eb6a5b617284d242a38/skills/hyperframes-core/references/creator-editing-recipes.md)、[播放器](https://github.com/heygen-com/hyperframes/blob/d11907c3255efcf6169c2eb6a5b617284d242a38/packages/player/README.md)、[制作执行接口](https://github.com/heygen-com/hyperframes/blob/d11907c3255efcf6169c2eb6a5b617284d242a38/packages/producer/README.md)、[编辑 SDK](https://github.com/heygen-com/hyperframes/blob/d11907c3255efcf6169c2eb6a5b617284d242a38/packages/sdk/src/index.ts)。
- 吸收目标：源片段选区、重排、音画分轨、图形包装、可嵌入预览、渲染进度、版本固定及输出检查。
- 承接位置：通用剪辑方法、可选 HyperFrames 集成；DataHub 负责项目界面与素材解析。
- 不采用：整套 Skill 全量常驻、自动追随上游升级、默认本地 Whisper 或默认云服务配置。复用宿主转写与既定云端 ASR。
- 能力边界：`talking-head-recut` 当前主要做保持原片的图形包装；删停顿和镜头重排须走实际剪辑路径，不能按 Skill 名推断。
- 验证：中文口播复剪、实拍加生成镜头、图形包装三类项目；重新打开、局部修改、音画同步、预览与成片一致性。

### ChatCut Agent Plugin

- 证据：[项目与编辑模型](https://github.com/ChatCut-Inc/agent-plugin/blob/f58a037d82abe0ad6b4163f84dcd8ea8c590d686/codex/skills/chatcut-plugin-basics/SKILL.md)、[结果验证](https://github.com/ChatCut-Inc/agent-plugin/blob/f58a037d82abe0ad6b4163f84dcd8ea8c590d686/codex/skills/verification/SKILL.md)。
- 吸收目标：先读取当前工程，再执行有界修改，最后重新读取结构并检查合成画面；区分源素材和时间线实例。
- 承接位置：Creative Craft 编辑与检查工作流；项目工具的行为约束。
- 不采用：将插件视作完整开源引擎、推定嵌入编辑器能力、未经验证依赖托管账户服务。
- 验证：用户手动移动镜头后 Agent 继续修改，不覆盖新状态；工具成功不能替代画面检查。托管接入另做账户与接口验证。

### OpenChatCut

- 证据：[固定版本说明](https://github.com/0xsline/OpenChatCut/blob/07437f60257a578745262359753bfccce337510c/README.md)、[许可证](https://github.com/0xsline/OpenChatCut/blob/07437f60257a578745262359753bfccce337510c/LICENSE)。它是独立项目，不是 ChatCut 官方开源版。
- 吸收目标：内置 Agent、MCP 与人工共用编辑操作，工程保存、撤销、任务状态和多轨语义。
- 承接位置：通用工程状态与编辑接口；DataHub 项目编辑交互。
- 不采用：整体搬入本地优先应用、重建账户设置、直接并入 AGPL 源码或默认引入 Remotion。
- 验证：重开工程、撤销、Agent 与人工交替修改、冲突可见；宿主权限与远程素材单独验证。

### OpenMontage

- 证据：[固定版本制作流程](https://github.com/calesthio/OpenMontage/blob/08e2151fa02de28a5d6a312b3d575692bf147ad7/README.md)、[许可证](https://github.com/calesthio/OpenMontage/blob/08e2151fa02de28a5d6a312b3d575692bf147ad7/LICENSE)。
- 吸收目标：参考片拆解、差异化概念、分镜与阶段产物、实拍和生成混合制作、成本可见与成片检查。
- 承接位置：Creative Craft 按需制作工作流与质量评估。
- 不采用：全部工具或 Skill 常驻、每一步强制用户确认、默认下载本地模型、默认开通全部 Provider。
- 验证：由参考片提取可迁移表达方法，使用自有素材形成不同成片；记录重试成本和人工修改量，不复刻参考片独有表达。

### Remotion

- 证据：[官方 Agent Skills](https://www.remotion.dev/docs/ai/skills)、[固定版本许可证](https://github.com/remotion-dev/remotion/blob/5321b3687b0e1a4e19f0c11d5959afff473c77c8/LICENSE.md)。
- 吸收目标：React 参数化合成、帧级时序与程序化渲染的对照方法。
- 承接位置：执行引擎对照评估；仅出现首选引擎无法满足的真实需求时考虑第二适配器。
- 不采用：因前端使用 React 就默认选择、未经对照引入双引擎、将源码可见理解为无限制免费商用。
- 验证：相同素材和脚本的文字排版、字幕、音画同步、修改成本及渲染资源对照；采用前明确许可证条件。

### Cerul

- 证据：[固定版本设计](https://github.com/cerul-ai/cerul/blob/6a76ca302c740851fbcaba5d24d29e094fe9ae16/DESIGN.md)。
- 吸收目标：画面、ASR、OCR 多路召回；保留时间范围与原始证据；模型空间隔离、分阶段缓存与可重建索引。
- 承接位置：Creative Craft 片段请求与证据使用方法；DataHub 负责索引、权限、检索运行和资产身份。
- 不采用：把通用索引窗口当精确镜头边界、把相关分数当概率、假定已有重排、整体复制本地文件库与机器人数据集功能。
- 验证：中文画面/口播/OCR 查询、按使用条件过滤、时间定位、重叠去重、索引重建；旧内容理解不能复用成新投放诊断。

### OpenCut

- 证据：[固定版本状态](https://github.com/OpenCut-app/OpenCut/blob/400f097becba5db0fbc305d5a65348cb81c20356/README.md)。主仓说明正在重写，现有 classic 与新架构应分别评估。
- 吸收目标：后续编辑器交互、插件边界与无界面制作接口。
- 承接位置：未来编辑交互评估，不进入首期依赖闭包。
- 不采用：将计划中的 Editor API、MCP、headless 能力当作现成工具。
- 重评触发：相关能力发布可运行版本，并通过实际导入、编辑、保存、导出测试。

## 吸收与更新记录

每次后续吸收在本文件追加有界记录：能力 ID、问题与预期收益、上游固定路径/版本、许可处理、承接文件、实现 revision、执行环境、测试素材与场景、真实结果、剩余限制、回退方式。只在对应证据完成后升级状态。

运行依赖采用实际验证过的版本；登记的研究 SHA 不自动成为依赖版本。升级、接口变化、回归失败或明确的新任务触发重新比较，不自动 merge/pull 上游。

2026-09-20 初始登记快照：完成以上七项文档登记与定向源码/说明研究；当时所有能力保持 reference/candidate/deferred，尚无集成或真实成片验收。后续实现与验收以以下更新为准。

## HyperFrames 本地执行 MVP：2026-09-20（初始验收快照）

- 能力 ID：`hyperframes-local-edit-render`；状态 `implemented`，合成媒体技术检查 `verified`；真实业务素材及宿主接入未验收。
- 承接：[可选本地模块](../integrations/local-production/README.md)。依赖 `@hyperframes/producer@0.8.53`、`gsap@3.13.0`，锁文件固定实际依赖闭包；没有复制上游 Skill 或引擎源码。未提交源码，无实现 commit 可引用。
- 实测修正：producer 安装包的执行签名与 README 不同；宽高由 composition 定义控制；捕获层 stdout 日志需在 CLI 入口转向 stderr。
- 验证：Node 24/macOS、独立 Chrome 渲染进程、FFmpeg；版本化工程、源时间字幕、重排/裁切、640×360 预览及 1280×720 导出。合成媒体取样验证画面与音频源区间；中文抽帧可读。
- 证据：本地 `dist/local-production/2026-09-20T04-50-43-468Z/` 的工程、回执、成片、signal-checks.json；运行 `npm run smoke` 可重建等价技术样例。回执不宣称人工听检或创意质量验收。
- 剩余限制：尚无自然语言规划器、业务素材质量验收、复杂多轨/转场、长时长性能、隔离 worker 或 DataHub 集成；本模块不进入根 Skill 发布包。回退停用该可选模块即可，旧核心合同和原媒体不变。


## 宿主验证状态更新：2026-09-20

本节更新上述初始快照；固定审阅 SHA 和许可记录未重新审阅，不据此宣称上游最新状态。核对对象为本地源码、DataHub 验收记录与已落盘回执；未重新运行测试，也没有可引用的本次实现提交。登记七个项目不等于七个项目都已接入。

| 能力 / 所属实现 | 当前证据 | 仍未证明 |
| --- | --- | --- |
| HyperFrames / Creative Craft 可选模块 | DataHub 实际 HTTP、身份、工程版本、队列、worker、真实缓存原片渲染及签名产物读取通过本地隔离联调；回执固定 producer 0.8.53 | 云端 TOS、生产部署、完整人工音画及创意质量验收 |
| 台词分镜 / DataHub | 已有选择素材范围、台词检索、模型候选校验和可编辑时间线；实际模型客户端通过本地模拟服务验证 | 真实模型创意质量；不是 ChatCut 服务接入或通用编辑 Agent 验收 |
| 镜头目录 / DataHub | 原片剪切候选、代表帧、目录导入和站内提取队列已有隔离验证；绑定原片 hash、时间与权限 | 剪切候选不等于准确识别所有镜头；不是 Cerul 引擎接入 |
| 代表帧语义与检索 / DataHub | 有限镜头选择、语义任务、取消、证据绑定及目录范围关键词检索已实现；本地 Ark 模拟 HTTP 服务及浏览器接口夹具分别验收 | 未进行真实付费视觉模型调用；单帧不证明动作、声音、完整多模态召回或识别准确率 |
| Seedance 混合制作 / 后续方向 | 分镜可列出缺失镜头需求 | 尚无生成任务、产物回入工程和真实混合成片闭环 |

证据定位（DataHub 仓库内，不复制业务素材、内部地址或原始日志到本仓库）：

- 行为、配置与限制：`docs/CONTENT_PRODUCTION_LOCAL.md`。
- 分阶段验收：`.trellis/tasks/09-20-content-production-workbench/verification.md`，重点为 catalog import、shot extraction queue、station semantic jobs/search 三节；任务归档后以宿主文档指向的归档记录为准。
- 宿主本地回执：`.cache/content-production-acceptance/catalog-real-http-e2e/receipt.json`、`semantic-jobs-http-e2e-verified/acceptance.json`；这些忽略目录不是可分发或永久公开证据。
- 最后核对的前后端综合检查记录为 295 项通过，其中 246 项缓存命中；浏览器使用接口夹具，与真实 HTTP/worker 隔离测试是不同证据层，均不等于生产验收。

上述宿主能力不自动成为共享 Skill 或可选模块的公共 API，也不证明已安装、提交或发布。源码仓库、安装版 Skill、宿主本地实现和生产运行分别核验。

## 下一批吸收与验收（计划，尚未完成）

| 优先级 / 参考方向 | Creative Craft 应沉淀的通用能力 | DataHub 承接 | 完成条件 |
| --- | --- | --- | --- |
| P1 / ChatCut、OpenChatCut | 读取当前工程 → 有界修改 → 重读结构 → 检查结果；明确素材与时间线实例 | 版本化编辑接口、人工编辑和冲突展示 | 人工先移动片段，Agent 重读后继续编辑；陈旧版本拒绝写入；检查实际成片。现有版本冲突检查只能算其中一项 |
| P1 / Cerul | 选片理由与证据引用，区分台词、代表帧观察、时序推断和复用建议 | 语义索引、权限过滤、源身份与时间定位 | 按中文画面/台词查询，结果可追溯到原片；变化来源失效，建议不冒充观察。当前关键词检索只覆盖部分条件 |
| P2 / OpenMontage | 参考拆解、缺口镜头 Brief、已有与生成镜头的连续性约束和成片检查 | Provider 任务、预算、产物入库与时间线替换 | 用已有素材加一个新生成镜头完成成片；局部替换保留工程其余内容，记录来源、成本和人工修改 |
| 持续 / HyperFrames | 已支持编辑操作的稳定编译、预览、导出与检查 | 固定模块、执行隔离及产物访问 | 相同工程可重开再修改；预览/导出时序一致；真实中文字幕、音画和失败恢复均有证据 |
| 条件触发 / Remotion、OpenCut | 保留对照与重评入口 | 只有当前执行器遇到具体限制时评估 | 先记录缺口，再用同一素材/脚本比较，不默认引入第二引擎 |

成熟方法按需沉淀到已有 video-production、iteration-and-versioning 等参考模块；只有现有模块无法承接时再拆新文件。SKILL.md 保留入口与路由，不把这些计划写成已可调用的运行能力。

### 方法沉淀更新：2026-09-20

ChatCut / OpenChatCut 参考方向已形成通用的
[读取工程、限定修改与检查结果方法](../skills/creative-craft/references/video-production.md#editing-an-existing-project)，
以及[共享工程版本处理规则](../skills/creative-craft/references/iteration-and-versioning.md#shared-project-revisions)。
覆盖源素材与时间线实例区分、人工修改保护、版本冲突、结果不明时的重试、局部恢复及实际音画检查。
这是方法文档的吸收，未复制上游实现、增加执行接口或证明接入上游服务；上述 P1 宿主完成条件仍需实际验收。

Cerul 参考方向已补充[片段检索与证据选片方法](../skills/creative-craft/references/video-production.md#evidence-grounded-footage-selection)：
从分镜用途形成检索需求，保留源身份与时间范围，区分 ASR、OCR/代表帧、实际音画观察和复用建议，
处理重叠候选与过期分析，并在回看后确定剪切边界。选片理由应说明可复用的创意机制，不能把检索分数或视觉吸引力当作投放效果。
该更新只沉淀 Agent 使用证据的方法；未接入 Cerul 引擎、增加索引或完成多模态检索验收。

OpenMontage 参考方向已补充[已有素材与生成镜头混合创作方法](../skills/creative-craft/references/video-production.md#mixing-existing-footage-with-generated-shots)：
把分镜映射到可用素材与缺口，明确生成目的、参考职责、前后镜头连续性与验收条件；生成产物先作为候选检查，再按工程版本局部替换并检查拼接结果。
方法同时区分生成 Brief、真实 Provider 任务、候选资产和已检查的成片，保留来源与成本信息。
该更新未增加 Seedance 等 Provider 连接器、执行生成或完成混合成片的宿主验收；表中的 P2 完成条件仍待验证。

本地真实素材的目录与画面抽查进一步暴露了语句跨镜头的验收风险：镜头切换不能证明语句结束，字幕和转写分段也不能替代听审。
已在选片方法中补充镜头范围与语句范围分离、保留完整语义、跨画面连续原声的时序与字幕检查，以及宿主不支持独立音轨时的替代方式。
这是由候选段落检查得到的方法修订；未完成连续听审或新的重剪成片验收，未将私有素材内容写入共享 Skill。

## 证据刷新边界：2026-09-22

AIOS 的本轮只读检查观察到媒体渲染/提取容器已运行，并发现规划/语义开关仍关闭。该宿主当前快照由其 `docs/autonomous-content-production/README.md` 维护；这里不复制客户配置或原始日志。它更新了“尚无任何部署基础”的历史判断，但没有证明完整自主剪辑、真实模型质量、云端全链路或 50 条/日和单条时延通过。

本次仅统一两份架构/参考文档的接入归属和验收，不重跑旧媒体测试、不新增上游依赖、不发布能力包。2026-09-20 各节继续作为当时的证据快照保留。

## 上游复核与方法补充：2026-10-02

触发：为视频剪辑 Agent 设计“读工程—有界修改—检查”与选片检索层而重新比较。固定审阅 SHA 不变，均可解析；本节记录固定点与 2026-10-02 当日 HEAD 的差异，不把 HEAD 视为新的固定点。

| 上游 | 当日 HEAD | 相对固定点 | 已吸收能力是否受影响 |
| --- | --- | --- | --- |
| ChatCut Agent Plugin | `877b9177144f` | 历史被重写，与固定点无共同祖先 | 否：`codex/skills/verification/SKILL.md` 与固定点逐字一致；basics 的数据模型和读取分层仍在。今后用文件级 diff，不能依赖 compare API |
| OpenChatCut | `d03acbd6c7b1` | 多 101 个提交、288 个文件 | 否：`assets/agent/openchatcut-tool-schemas.json` 编辑工具 122 个、只读 ask 工具 23 个，名单不变 |
| Cerul | `e93237887eaa` | 多 5 个提交 | 否：`DESIGN.md` 的 30 s 索引单元、60 s ASR 窗、1 fps OCR 采样及融合公式不变 |
| OpenCut | `e66801077856` | 多 1 个提交（FFmpeg CI） | 否：仍为重写期 Rust 桌面壳与 web 路由占位；Editor API、MCP、headless 只在 README 路线图。classic 版未评估，维持 `deferred` |

本次核对的固定路径（方法参考，未复制源码）：

- ChatCut：`codex/skills/chatcut-plugin-basics/SKILL.md`（Asset/Item 分离、帧单位、同轨不重叠、默认留 gap、ripple 只作用同轨；`read_project`→`preview_timeline`→`inspect_item` 分层读取，省略字段是未知而非空）、`codex/skills/verification/SKILL.md`（重读受影响范围 + 检查合成帧，修改成功不是视觉证据）。
- OpenChatCut：`src/editor/reducerHistory.ts`（整工程快照 undo，上限 100，连续手势合并，batch 为一步）、`src/editor/clipTypes.ts`、`src/editor/trackTypes.ts`、README 的 MCP 节（`begin_edit_session`→隔离草稿→`review_edit_session` manual/auto→原子提交为一步 undo；生成、导出、删除等不可回滚工具不进入草稿会话）、`edit_item{adds,updates,deletes,ripple,validateOnly}`、`verify_export`。AGPL-3.0，只吸收方法。
- Cerul：`DESIGN.md` §5–7、`schemas/search-result.json`、`schemas/fusion-moment.json`（hit 含源时间、score、matched、excerpt、`fusion_recipe`、逐条 `fusion_evidence{track,raw_score,rank,value,contributes}`；过滤先转时间区间再排序；sidecar 为真源，索引可零模型调用重建）。

方法吸收：在[读取工程、限定修改与检查结果方法](../skills/creative-craft/references/video-production.md#editing-an-existing-project)补充分层读取、校验/预览与单批提交、不可回滚操作移出草稿、结构检查清单及“源帧只证明选片、不证明合成”；在[证据选片方法](../skills/creative-craft/references/video-production.md#evidence-grounded-footage-selection)补充按模态保留分数与贡献证据、记录检索方法版本、硬约束先过滤再排序。均为方法文档更新，未增加执行接口，状态不升级。

供 AIOS/DataHub 评估的接口草案（不是 Creative Craft 公共 API，未实现）：

- 编辑操作集 v2（≤15，全部以帧为单位，写操作带 `base_revision` 与 `dry_run`，返回 diff 和新 revision）：读 `read_project`、`preview_timeline`、`inspect_items`、`render_frames`；写 `add_clip`、`remove_clip`、`move_clip`、`trim_clip`（含 slip）、`split_clip`、`replace_media`、`set_clip_props`、`edit_track`、`apply_script`；控制 `commit/undo`（一个事务一步）、`verify`（结构检查 + 合成帧 + 导出质检）。
- 选片检索返回：`{recipe_version, space_id, hits:[{asset_id, source_revision, source_start_ms, source_end_ms, score, matched[], evidence:[{track, raw_score, rank, norm, contributes, excerpt, start_ms, end_ms}], preview_frame, scene_id}], stale_excluded, capability_gaps}`，源时间为半开区间，可直接传给 `add_clip`。

剩余限制：上表 P1 宿主完成条件仍未验收；未运行任何上游代码。下次复查仍按“升级、接口变化、回归失败或新任务”触发，并优先比对上面列出的固定路径。

## 持续吸收机制与当前状态：2026-10-02

### 机器真源与检查

[`upstream-watch.json`](upstream-watch.json) 是固定研究 SHA、监控路径、上游路径到本仓库文件的映射，以及当前吸收状态的机器可读真源。前文「审阅基线」表保留为 2026-09-20 历史快照，后续更新以 watch 文件加本文件的日期记录为准，两者在同一提交中修改。

`make upstream-check`（即 `scripts/upstream_drift.py`）只读运行：对每个监控路径比较固定 SHA 与上游默认分支的文件 blob 或目录清单（不依赖 compare API，ChatCut 这类历史被重写的仓库也适用），并比对 HyperFrames 的 npm 最新版本与 `integrations/local-production/package.json` 中的锁定版本。`--offline` 只校验 watch 文件，并由 `tests/test_upstream_drift.py` 在常规测试中执行，本地文件重命名导致映射失效时会测试失败。脚本需要已登录的 `gh` 和网络，不进入 `validate-all`。

### 复查流程

触发：开始新一期 video harness 工作前、准备发布前、依赖升级或回归失败时；没有触发时可按月运行一次。

1. 运行 `make upstream-check`，只处理标记 `REVIEW` 的项目。
2. 对每个变化路径阅读实际 diff，归入以下一类：无影响（措辞、示例）/ 方法更新（改 `video-production.md` 等参考文档）/ 实现候选（进入 harness 计划，按正常测试与证据验收）/ 许可或边界变化（暂停该项吸收并重新评估）。
3. 在本文件追加日期记录：路径、上游新 SHA、分类、结论与承接文件。文件有变化不等于需要吸收。
4. 只有完成复查后，才把 watch 文件中的 `pinned_sha` 更新为已审阅的上游 SHA；已实现能力的状态只能凭对应提交和测试证据升级。npm 依赖升级另需 `npm test`、`npm run smoke` 与字体集成测试全部通过。
5. AGPL 项目（OpenChatCut、OpenMontage）只吸收方法；Remotion 采用前先复核许可证条款。

### 当前吸收状态（替代 09-20 初始处置）

| 项目 | 状态 | 已承接到 | 方式 |
| --- | --- | --- | --- |
| HyperFrames | implemented | `integrations/local-production`：EditDocument v2 编译、渲染、lint 关卡；依赖固定 `@hyperframes/*@0.8.108` | 包依赖 + 方法 |
| ChatCut Agent Plugin | implemented | 素材与实例分离（edit-document v2）、修改后重读并检查合成帧（render-qa、`qa.mjs`）、`video-production.md` 编辑循环 | 方法 |
| OpenChatCut | implemented | 整批原子编辑、`--dry-run`、批次 `operations_sha256`、锁定轨道（`operations.mjs`、`project.mjs`）；轨道角色与自动闪避留待 P2 | 方法 |
| OpenMontage | implemented | 代码强制阶段关卡、审批、交付承诺实算、先预留后结算的预算台账（`creative_craft_video.py`、production-plan） | 方法 |
| Cerul | implemented | 选片证据按模态记录、保留原始分数和检索方法（production-plan `selection.evidence`）、`video-production.md` 选片方法；未接入索引引擎 | 方法 |
| Remotion | candidate | 无；仅在 HyperFrames 无法满足具体需求且许可证适用时评估为模板引擎 | 对照 |
| OpenCut | deferred | 无；可运行的 Editor API、MCP 或 headless 发布后重评 | 无 |

`implemented` 表示已有本仓库实现与自动化测试，验证范围限于合成素材，不代表真实业务素材、创意质量或宿主生产已验收。上一节「供 AIOS/DataHub 评估的接口草案」现已部分落地为 local-production 编辑批次：操作名和粒度以 [Video Harness v1](content-production-architecture.md#video-harness-v1) 为准，`render_frames`/`verify` 对应 `qa`，`apply_script` 尚未实现。

### 首次运行结果（2026-10-02）

需复查：HyperFrames（编辑配方、CLI skill、lint/inspect 参考、SDK 类型、timeline 命令有变化；npm 最新版与锁定版同为 0.8.108）、ChatCut（basics 一行变化）、OpenChatCut（`reducerActions.ts`、工具 schema）、Remotion（`packages/skills`）、Cerul（`DESIGN.md`）。无变化：OpenMontage；OpenCut 的监控路径不变。

已复查：ChatCut `codex/skills/chatcut-plugin-basics/SKILL.md` 的唯一变化是 `inspect_item` 改为每次最多 10 个 item，归类为无影响；其余项目尚未复查，固定 SHA 保持不变。

### 首次复查结论（2026-10-02）

按上述流程复查了首次运行标记的全部变化，逐文件阅读两版内容。结论：现有实现均无需改动；HyperFrames 与 Remotion 为 P2 提供输入。复查后 watch 文件的固定 SHA 更新为：HyperFrames `70900216f0da`、ChatCut `877b9177144f`、OpenChatCut `d03acbd6c7b1`、Cerul `e93237887eaa`、Remotion `579e314165ce`；OpenMontage 不变；OpenCut 监控路径无变化，保留原固定点。

| 项目 / 路径 | 分类 | 结论 |
| --- | --- | --- |
| HyperFrames `creator-editing-recipes.md` | 实现候选（P2） | 上游默认改为视频自带声音（`data-has-audio="true"`），独立 `<audio>` 只用于 J/L 切、替换音轨、配乐与旁白；转场和闪避的音量写在 `data-automation` volume lane，不与音量补间并用（lint 规则 `audio_volume_double_automation`）；变速 0.1–10 并有 `rate` lane。均已含于锁定的 0.8.108（本地 `core/dist` 中 `MAX_PLAYBACK_RATE = 10` 已核实），P2 无需升级。我们现有“静音视频 + 独立音频”仍有效；若 P2 迁移到视频自带声音，先加 `data-has-audio` 严格取值的回归测试 |
| HyperFrames `hyperframes-cli/SKILL.md` | 方法更新 | 新增 `history`（试行）与 `clean`；我们不经 CLI 驱动，`render.mjs`/`qa.mjs` 不受影响 |
| HyperFrames `lint-validate-inspect.md` | 方法更新 | 新增 `canvas_content_at_edge`（CLI `check`，本地 lint 包不含）；P2 图形模板若用 canvas 绘字需另行检查贴边 |
| HyperFrames `packages/sdk/src/types.ts` | 观察 | `setTiming.linked`、`moveIntoSync`/`slipIntoSync`（`data-link`/`data-sync-origin` 视音链接与失步修复）需 ≥0.8.109，npm 尚未发布；我们不依赖 SDK，暂不吸收 |
| HyperFrames `cli/commands/timeline.ts` | 方法参考 | `--plan` 预演与回执撤销，与我们的 `--dry-run`、原子批次一致；不依赖 CLI |
| HyperFrames 0.8.108 producer | 实现候选（P0 补强） | 新增 `audioLoweredDb`：真峰值限幅压低整段混音时记录（本地 `producer/dist` 已核实）。`qa.mjs` 的真峰值检查可引用它作为限幅证据 |
| ChatCut basics | 无影响 | 仅 `inspect_item` 改为每次最多 10 个 |
| OpenChatCut `reducerActions.ts` | 无影响 | 新增 `durationFps` 与仅空时间线可用的 `tl.setFps`；我们的源时间为秒、fps 为固定枚举 |
| OpenChatCut 工具 schema | 无影响 / deferred | `edit_item`（validateOnly、整批原子）与 `verify_export` 定义及工具名单不变；新增 Fal 生成目录超出范围；`import_timeline`（FCPXML/EDL）记为未来工程交换参考 |
| Cerul `DESIGN.md` | 无影响 | 仅命令清单与 CI 文案；索引单元、采样与融合公式不变 |
| Remotion `packages/skills`（4.0.526→4.0.532） | 方法参考 | `LICENSE.md` blob 不变，维持 candidate。P2 可参考：音量关键帧（淡变、闪避）、带可编辑类型化 props 的独立时间线组合（图形模板）、转场统一提前挂载。监控路径已细化为 `remotion-markup/{transitions,audio,timing-props,connected-compositions}.md` |

<a id="image-engineering-references"></a>

## 图片工程参考与吸收登记：2026-10-04

目标：补齐 Agent 与人共同维护可编辑图片工程的方法与执行层，覆盖产品海报、封面、营销卡片及场景图局部精修。承接 [Image Harness v1](content-production-architecture.md#image-harness-v1)和 [可编辑图片方法](../skills/creative-craft/references/image-production.md#editable-image-projects)。初始登记 17 项参考，P0 实现追加 resvg-js 与 Noto CJK，真实商品 matting 试验再追加 PyMatting，目前共 20 项：19 个 GitHub 仓库加入既有监控，Polotno 按官方文档单独复核；react-konva 是 Konva 的配套入口，不冒充已固定的第二个依赖。Apple Vision 另记为本机平台基线，不作为新的开源项目或正式依赖。

核验范围：2026-10-04 读取 GitHub 默认分支、完整提交 SHA、目录树、根许可、README，以及部分工具协议、工程保存、候选暂存、蒙版/渲染接口片段。固定点可能包含未发布代码；不是采用版本或完整源码审查。初始登记未安装上游工程；随后 P0 仅采用三个发布包和固定字体，验证见后文，未验证实际商品效果。下表许可仅记录所读来源；代码、模型权重、字体、素材、依赖和服务条款分别核对。

### 初始研究基线与取舍

| 项目 / 固定研究入口 | 固定研究 SHA 或文档日期 | 研究定位与吸收目标 | 许可记录 | 执行处置 |
| --- | --- | --- | --- | --- |
| [OpenPencil](https://github.com/open-pencil/open-pencil/tree/aeba9a6bd5a416007e42086db438ffc9c71fb3c9) | `aeba9a6bd5a416007e42086db438ffc9c71fb3c9` | 可编辑工程协议：对象身份、共用工具 Schema、读/写能力与修改元数据 | MIT；资源/依赖另核 | `reference` |
| [InvokeAI](https://github.com/invoke-ai/InvokeAI/tree/1c6c8d02be298390c57bbcbf8a3f934ca70b0af7) | `1c6c8d02be298390c57bbcbf8a3f934ca70b0af7` | 生成与编辑流程：暂存候选、接受/丢弃、画布工程保存与恢复 | Apache-2.0；模型/附带模块另核 | `reference` |
| [Krita AI Diffusion](https://github.com/Acly/krita-ai-diffusion/tree/828b70c33c5c97f326e03170cd693beef798231e) | `828b70c33c5c97f326e03170cd693beef798231e` | 选区、上下文、蒙版与人工精修；生成区域与最终合成区域分离 | GPL-3.0；插件/模型条款分别核 | `reference` |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI/tree/f1072eb0350638a3390ddb6afbcaa8c6b237c6fd) | `f1072eb0350638a3390ddb6afbcaa8c6b237c6fd` | 可选执行后端：提交、队列、进度、取消和产物；复杂工作流按需接入 | GPL-3.0；节点/模型另核 | `reference` |
| [Fabric.js](https://github.com/fabricjs/fabric.js/tree/39471c7a379c08347841f4282dd3940b49ed4c71) | `39471c7a379c08347841f4282dd3940b49ed4c71` | 对象画布候选：对象变换、序列化和导出；与 Konva 对照 | MIT | `candidate` |
| [Satori](https://github.com/vercel/satori/tree/34028689b9e8184b3873eaf9758db5ccdf8f7c6e) | `34028689b9e8184b3873eaf9758db5ccdf8f7c6e` | 模板、精确文案与字体布局，输出 SVG；P0 固定 npm 0.35.0 | MPL-2.0；字体/依赖另核 | `implemented`（P0 包依赖） |
| [Jaaz](https://github.com/11cafe/jaaz/tree/145dd85067be77e36d400637a595e19a7b07c77a) | `145dd85067be77e36d400637a595e19a7b07c77a` | 受限产品参考：对话、画布、素材组织与多轮创作 | Community/Commercial 自定义双许可；团队部署/二开/再分发受限 | `reference` |
| [FiftyOne](https://github.com/voxel51/fiftyone/tree/eaf7f2c9f1ed4a2bcdd028d8af6dfbffec224d07) | `eaf7f2c9f1ed4a2bcdd028d8af6dfbffec224d07` | 素材与质量研究：浏览、标注和相似检索；资产权限/业务索引留宿主 | Apache-2.0；服务/模型另核 | `reference` |
| [Sharp](https://github.com/lovell/sharp/tree/1189cf4943af2b31ea41ee0cdf4f8d8bfb393317) | `1189cf4943af2b31ea41ee0cdf4f8d8bfb393317` | P0 固定 npm 0.35.5：素材方向归正、sRGB/PNG、预览缩放与完整解码检查 | Apache-2.0；libvips/依赖另核 | `implemented`（P0 包依赖） |
| [IOPaint](https://github.com/Sanster/IOPaint/tree/61a759fb3f332bacdce8b2813f4837495c9b86e0) | `61a759fb3f332bacdce8b2813f4837495c9b86e0` | 历史局部擦除/扩图参考；GitHub 已归档，不选作长期主依赖 | Apache-2.0；模型另核 | `deferred` |
| [Penpot](https://github.com/penpot/penpot/tree/7c039231f79022f26b252776817c41fa61476aa3) | `7c039231f79022f26b252776817c41fa61476aa3` | 协议对照：人工与 Agent 操作同一设计文件，MCP/插件边界 | MPL-2.0；具体 MCP 文件另核 | `reference` |
| [Polotno](https://polotno.com/docs/overview) | 官方文档复核：2026-10-04；无仓库 SHA | 营销模板、文字、JSON 工程及批量导出；商业 SDK 的产品/协议参考 | 商业订阅；Schema 包生产使用亦需有效订阅 | `reference` |
| [Konva / react-konva](https://github.com/konvajs/konva/tree/ca62a92ee60095803bf69abae29d92b936ee2eef) | `ca62a92ee60095803bf69abae29d92b936ee2eef` | 对象画布候选：场景树、变换与导出；react-konva 为同一生态补充 | Konva 根许可 MIT；react-konva 采用时另固定 | `candidate` |
| [SAM 2](https://github.com/facebookresearch/sam2/tree/2b90b9f5ceec907a1c18123530e92e794ad901a4) | `2b90b9f5ceec907a1c18123530e92e794ad901a4` | 对象选区工具参考；模型蒙版不等同透明商品的 alpha matte | Apache-2.0（主体）；第三方代码/字体另核 | `reference` |
| [SAM 3](https://github.com/facebookresearch/sam3/tree/2345a4ad109ac29c569da749c91d84f10dc08c40) | `2345a4ad109ac29c569da749c91d84f10dc08c40` | 文本/视觉提示的对象选择；按实际商品样例验证 | SAM License；不能沿用 SAM 2 的许可结论 | `reference` |
| [ViTMatte](https://github.com/hustvl/ViTMatte/tree/8cd7ef068380977c3962c4cb733cb1fe7f2241a5) | `8cd7ef068380977c3962c4cb733cb1fe7f2241a5` | 精细抠图参考：图片+trimap → alpha matte；透明/反射需实测 | MIT（代码）；权重/数据分别核 | `reference` |
| [PyMatting](https://github.com/pymatting/pymatting/tree/6d5c4a6bed0e5672abac0bad078e594423ffe4fd) | `6d5c4a6bed0e5672abac0bad078e594423ffe4fd` | 真实商品候选研究：闭式 alpha 与前景颜色估计分开比较；隔离试验采用发布包 1.1.16 | MIT（根及包许可已读）；依赖分别核 | `candidate`（未成为正式依赖） |
| [resvg](https://github.com/linebender/resvg/tree/1fe3cfe88bc692612f1ccd4403ba3476b2cdd813) | `1fe3cfe88bc692612f1ccd4403ba3476b2cdd813` | 静态 SVG 栅格化候选；对照字体、尺寸、色彩与 SVG 支持范围 | Apache-2.0 OR MIT（当前核心）；字体/依赖另核 | `candidate` |
| [resvg-js](https://github.com/thx/resvg-js/tree/9de8ddd9dd62293006d849dd846a3b91ba992f23) | `9de8ddd9dd62293006d849dd846a3b91ba992f23` | P0 实际 Node 绑定 `@resvg/resvg-js` 2.6.2，SVG → PNG；研究 main SHA 与 npm 包源修订分别看待 | MPL-2.0；附带旧 resvg 核心另核，不能套用当前核心许可 | `implemented`（P0 包依赖） |
| [Noto CJK](https://github.com/notofonts/noto-cjk/tree/f8d157532fbfaeda587e826d4cd5b21a49186f7c) | `f8d157532fbfaeda587e826d4cd5b21a49186f7c` | P0 静态简中 Regular OTF；固定字节与字形，复制到工程供重开 | OFL-1.1（Sans）；许可证入库，字体二进制不入库 | `implemented`（固定资源） |

IOPaint 的 `archived=true` 已由 GitHub 仓库元数据确认；本轮不根据旧摘要推定归档日期。resvg 在本次固定点的核心标注 Apache-2.0 OR MIT，不能把旧版本的 MPL-2.0 记录套用到新版本。Fabric.js 已有 `packages/core` 路径；InvokeAI 同时存在 webv1/webv2，文档里的 `.invk` 版本需与实际前端和采用版本核对。这些路径/版本差异正是后续漂移检查应保留固定点的原因。

### 吸收目标与承接边界

- **核心流程参考：OpenPencil、InvokeAI、Krita AI Diffusion。** 提炼对象身份、共用操作、读取当前状态、候选暂存/接受、生成蒙版与合成蒙版、人工接续与保存恢复。当前只沉淀通用方法，未接入它们的执行器。
- **工程协议对照：Penpot、Polotno。** Penpot 对照 Agent/插件作用范围与目标绑定；Polotno 对照营销模板、文字排版和 JSON 工程。OpenPencil/Penpot 是完整设计平台方向，Polotno 是商业 SDK；产品适合不等于可嵌入或免费复用。
- **P0 实现：Satori、resvg-js、Sharp 与 Noto CJK。** 固定确定性排版/栅格化路线，版本、实际兼容问题及证据见后文。Fabric.js/Konva 保留交互编辑候选，当前新版 resvg 核心仍是升级对照；库的序列化不自动提供业务版本、权限、候选管理或工程互转。
- **条件工具：ComfyUI、SAM 2、SAM 3、ViTMatte。** ComfyUI 仅在本地复杂工作流有真实需求时评估；SAM 提名对象选区，ViTMatte 处理 alpha matting。分割质量、透明瓶身、反射和投影必须在实际素材验证，代码许可不替代权重/数据许可。
- **配套与受限参考：FiftyOne、Jaaz、IOPaint。** FiftyOne 用于资产浏览/标注/相似检索的方法研究，权限与业务索引仍归宿主；Jaaz 仅作受限产品参考，未经适用授权不复用源码或受限制的 UI/UX；IOPaint 保留历史交互研究入口，维持 deferred。

### 固定路径与更新复查

GitHub 监控路径、变化原因及本地承接文件以 [upstream-watch.json](upstream-watch.json) 为机器真源，当前合计 26 个 GitHub 上游（已有视频 7 项 + 图片/字体 19 项）。图片监控共 56 条，包含许可、工具协议、画布候选/保存、对象序列化、蒙版、合成、分割、前景颜色估计、渲染接口和固定字体字节。

```sh
# 全部已登记 GitHub 上游；只读，不安装、不拉取或自动吸收
make upstream-check

# 先复查图片核心流程，按需要追加其他 --only ID
python3 scripts/upstream_drift.py --only openpencil --only invokeai --only krita-ai-diffusion

# 无网络的本地清单/承接文件检查
python3 scripts/upstream_drift.py --offline
```

检查只比较登记路径的 blob/目录身份；它不读取所有 Release 公告，也不检测 Polotno 外部页面、模型权重或服务条款的变化。文件不变只说明这些路径无漂移，不能报告“全部能力/许可未变”。依赖版本提示限于 watch 中显式登记的 npm 依赖；图片 P0 已登记 Satori、resvg-js、Sharp 的实际 package.json 固定版本。

后续每次图片维护、采用依赖/模型、上游相关发布、接口拒绝、回归失败或许可变化时运行检查；没有事件时按月做一次维护复核作为建议。当前未安装定时任务或后台通知，及时性依赖实际执行检查；定时自动化需单独配置。

复查流程沿用视频侧，并补充图片证据：

1. 读取标记 REVIEW 的实际差异；ERROR 先排查路径删除、固定点不可解析或网络失败，不把错误视为无变化。
2. 分类为无影响、方法更新、实现候选或许可/边界变化。对商品保真、文字、字体、颜色、坐标、候选与工程保存的变化先判断行为影响；不按提交数量决定吸收。
3. 方法更新承接到 image-production 等按需参考；执行候选进入 Image Harness 计划，只解决当前验收缺口。模型/依赖升级固定具体版本，采用相关真实样例验收与回退验证。
4. 在本节追加日期、能力 ID、旧/新 SHA、变化路径、许可结论、承接文件、实际验证及剩余限制。完成复查后再更新 pinned_sha；一次文档研究不能升级为 implemented/verified。
5. 验证固定商品素材、中文文案、字体、蒙版和工程修订，覆盖改字/改价、移动/缩放、局部修图、候选接受/撤销、人工接续、重开和多规格导出。分别记录结构检查、真实像素/画面和创意质量证据。

### Polotno 官方文档复查入口

本轮读取 [SDK 概览](https://polotno.com/docs/overview)、[Design Format](https://polotno.com/docs/schema)和[许可协议](https://polotno.com/legal/license)。Design Format 当前文档注明 schemaVersion 4、仍为 pre-1.0；默认 SDK 4.x 的 React 要求属于本轮文档观察，未来采用时重新核对，不把它写成永久兼容保证。Schema 包的公开安装入口也不代表生产免费。

复查 SDK/API/工程格式迁移、字体与导出行为、React/宿主支持、授权/订阅和网络依赖；记录文档日期、具体 SDK 版本与受影响接口，在本节追加结论。此项不纳入 GitHub watcher，不能以 make upstream-check 成功替代；开始实际比较前先确定适用授权。

### 本轮状态

初始登记验证：离线清单校验通过（当时 23 个 GitHub 上游）；现有 upstream_drift 的 8 项离线回归通过；新增 16 个仓库的 46 条路径完成在线固定点/默认分支比较，均 unchanged、无错误。该在线检查仅覆盖新增图片条目，没有刷新此前 7 个视频上游。仓库 doctor、包体边界和本次修改文档的本地文件链接检查通过。Polotno 为上述官方文档人工复核，不计入 GitHub 监控结果。

初始参考登记与通用方法补充完成后，本地 P0 与 P1-A/B 已实现，证据见后文。真实 Provider 连接、人工编辑界面、宿主注册与六场景真实商品验收仍为计划。正式工件 API、现有视频依赖、安装版 Skill 和发布状态未升级。

### P0 实际吸收记录：2026-10-04

| 能力 / 上游 | 采用内容与边界 | 承接文件 | 验证与限制 |
| --- | --- | --- | --- |
| 对象工程 / OpenPencil、视频 Harness 方法 | 稳定对象 ID、读当前修订、共用有界批次、dry-run、锁定、不可变修订、撤销；原创本地实现，不复用编辑器源码 | `integrations/image-production/document.mjs`、`project.mjs`、`cli.mjs` | 结构/冲突/并发/锁定/撤销/保存回归；author 是声明，不是认证；宿主工具注册未验证 |
| 精确排版 / Satori 0.35.0 | 结构化本地对象 → SVG，字形轮廓化；拒绝任意 HTML/SVG、网络素材与缺字，导出前检查排版溢出 | `render-worker.mjs`、`font.mjs` | 真实中文 PNG 与改字区域外像素检查通过；HTML/CSS 子集、Regular 单字体和字符换行，不提供浏览器全量排版 |
| 栅格化 / resvg-js 2.6.2 | 禁止系统字体回退的 SVG → PNG；独立 worker，60 秒上限、取消及失败回执 | `render-worker.mjs`、`render.mjs` | PNG 完整解码/尺寸、超时/取消及不改源工程通过；绑定许可 MPL-2.0 与新版核心许可分开记录 |
| 图片加工 / Sharp 0.35.5 | 保存原素材，另建方向归正/sRGB 的 PNG，预览从同一导出图缩放 | `project.mjs`（P1 共用边界移至 `raster.mjs`）、`render.mjs` | JPEG 方向、三种 fit、动画拒绝、原素材摘要、预览/导出像素一致性通过 |
| 字体 / Noto CJK 固定 OTF | 静态 Regular 16,437,364 字节，SHA-256 `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b`，工程独立绑定 | `fonts/manifest.json`、`fonts/OFL.txt`、`font.mjs` | 现有视频可变 TTF 在 Satori 解析失败，替换静态 OTF 后通过；极窄文本框触发排版卡顿，用字宽预检与进程超时补强；不声称支持可变字体 |

完整 npm 闭包固定在模块 package-lock.json，仅安装于可选模块；根 Skill 包不捆绑渲染器/字体。研究默认分支固定 SHA 不等同 npm 发布包源码；后续分别检查路径漂移、npm 版本与实际行为，不能只更新编号。

本机 macOS / Node 24：15 项图片行为回归与 1 项复用写入工具回归通过；连续海报 smoke 保存 7 修订与 9 次真实 PNG 输出，含三个比例及预览。撤销/重开 PNG 摘要一致，商品源素材与锁定 Logo 对象保持。像素检查发现 Satori 的 break-all 会合并显式换行，已改为独立行块，并以两个独立文字对象的 PNG 相等验证。证据路径 `dist/image-p0-2026-10-04-1ccd3d5a/`；已查看三个比例的最终 PNG，检查该夹具的中文、层级与裁切，记录于 `visual-inspection.json`。合成素材没有证明真实商品保真、品牌创意质量或 Provider 能力；正式 Image Receipt/Inspection 桥接仍待实现。新增 Ubuntu CI 任务尚未有远端执行证据。

最终维护检查：离线清单 25 个 GitHub 上游通过，原有 7 个视频条目与 HEAD 完全相同。实际采用的 Satori/resvg-js/Sharp 与字体共 4 仓库、12 条路径在线检查 unchanged、无错误；3 个 npm 固定版本与所查 latest 一致。结果保存于同目录 `image-upstream-check.json`；这次在线检查未重复刷新其余参考条目。根 `scripts/validate.py` 的 177 项回归通过，包体边界通过（98 项，649,885 字节解包），可选图片模块与字体不进入 Skill 包。

### P1-A/B 本地方法吸收记录：2026-10-04

| 能力 / 上游研究点 | 实际吸收与边界 | 承接文件 | 实际验证 |
| --- | --- | --- | --- |
| 候选暂存与决定 / InvokeAI 固定 SHA `1c6c8d02be298390c57bbcbf8a3f934ca70b0af7` | 将候选与接受修订分离；绑定来源、基础修订、目标素材，完整海报对比后决定；接受/丢弃互斥，拒绝陈旧结果 | `integrations/image-production/candidates.mjs`、`candidate-store.mjs`、`project.mjs`、`render.mjs` | 暂存/对比不改工程；CLI、并发、人工改价、禁止静默变基、撤销消费记录回归 |
| 上下文与合成范围 / Krita AI Diffusion 固定 SHA `828b70c33c5c97f326e03170cd693beef798231e` | 显式上下文、生成/保护/合成蒙版；本地灰度格式与 Provider 格式分开；保留原像素并验证实际范围 | `integrations/image-production/composite.mjs`、`candidates.mjs`、`raster.mjs`；源 Skill `image-production.md` | 软边预乘 alpha、保护透明像素、蒙版非法范围/对齐/格式拒绝、全图提案仍只改允许区域 |

两项均为基于研究目标的原创本地实现，未复制 InvokeAI/Krita 源码、加载其执行器或新增依赖；仓库状态仍为 `reference`，adoption 字段说明已实现的方法。监控路径映射到上述实际代码，未来漂移可定位回归范围；此处不声称逐项兼容上游。2026-10-04 再查两仓库共 6 条既有路径全部 unchanged，无错误，固定 SHA 无需变更。报告位于 `dist/image-agent-2347063a/image-upstream-check.json`。

本机 macOS / Node 24：29 项图片行为回归通过，候选 smoke 完成 5 修订，保护区 197,840 像素、保护区/有效合成区外改变均为 0，撤销/重开 PNG 字节一致。证据 `dist/image-p1-2026-10-04-c98d7c25/smoke-report.json`。P0 smoke 重新通过，产物 `dist/image-p0-2026-10-04-186d03c8/` 的三个规格摘要与前轮相同。

当前 Codex 会话另读中文任务、用实际 CLI 操作并在决定前查看候选/局部结果，验证暖色选择、人工 ¥149、旧候选拒绝、局部清理、撤销与重开；报告及视觉检查在 `dist/image-agent-2347063a/`。这仅证明本会话工具操作可用，独立 Agent、Skill 自动发现/注入、Pi/AIOS 宿主、真实 Provider/费用、真实商品/透明反射与 Owner 批准均未验证。技术回执继续保留 `visual_quality=UNVERIFIED`，外置视觉记录只针对该合成夹具。Ubuntu CI 增加候选 smoke，尚无远端运行结果；安装版 Skill 和发布状态未变。

本轮最终维护门禁：根 validate 177 项回归通过，漂移工具 8 项离线回归与共享内容写入 1 项回归通过；25 个上游离线清单、38 个本地文档文件链接与 git diff --check 通过，原有 7 个视频条目与 HEAD 相同。skill-creator quick_validate 在临时隔离的 PyYAML 环境通过；根包边界为 98 项、649,873 字节解包、152,049 字节打包，图片执行模块/字体未进入 Skill 包。未提交、推送或发布。

### P1-C Provider 方法落地：2026-10-04

承接 P1-A/B 的候选/蒙版边界，新增 `integrations/image-production/provider.mjs`、`provider-config.mjs`、`provider-contracts.py`、`provider-store.mjs`、`provider-normalize.mjs` 和模块内 GPT Image 2.5 profiles。原创 Adapter 不复制上游执行器；同一候选流程绑定实际任务/回执/源图，编辑时把本地白色可改转换为 API 的 alpha=0，最终合成仍保留保护原像素。上述行为已在模拟服务回归，真实蒙版编辑仍未验证。原有上游固定 SHA 和视频条目不变。

Provider 官方资料与 GitHub 参考分别维护。2026-10-04 实际读取[图像提示词指南](https://developers.openai.com/api/docs/guides/image-prompting)、[生成/编辑 API 指南](https://developers.openai.com/api/docs/guides/image-generation)、[Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)与[Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)型号页。Flare 偏速度的小模型，Sunburst 偏质量的基础模型；两者支持生成/编辑。重核时同步模块 profile 的 verified_at/来源、size/quality/background 边界和 Provider 回归；别只更新模型名称，也别把别名映射当实际快照证据。网站资料是人工复核项，不冒充已加入 GitHub 自动漂移检测。

本轮复用用户指定的全局 URL/auth key，凭据不落工程、不改全局配置。47 项图片回归通过，新增 18 项覆盖真实 HTTP 模拟、任务不可重复消费、失败/取消/陈旧、蒙版极性、输出规格及离线恢复完整性。真实 Sunburst 生成仅两个客户端 POST，均 HTTP 200；第二个返回 1254×1254 而请求为 1024×1024。严格拒绝后显式全图等比离线缩放，保留原图与原 partial 回执，零新增请求；接受背景、改价、撤销/重开通过。真实局部编辑、Flare 对照、费用、真实商品融合及宿主证据仍缺失，P1-C 真实验收为 PARTIAL。

产物与实际查看记录：`dist/image-p1c-2026-10-04-a06e44ce/live-acceptance-report.json`、`visual-inspection.json`、`compare-normalized/comparison.png`。合成瓶子与背景光影融合未作为创意质量批准。Adapter 的执行回执桥接已实现，但安装版 Skill、正式公共工程合同、发布与 Pi/AIOS 集成状态未变；完整限制见[架构记录](content-production-architecture.md#image-harness-v1)。

### P1-C 后续验证与承接映射：2026-10-04

在新的独立工程中，按继续授权完成三个有界真实请求：一项 Sunburst 蒙版编辑、相同编译提示/1024×1024/medium 的 Sunburst 与 Flare 各一项生成，均 HTTP 200。`provider-acceptance.mjs` 提供离线 prepare 与显式 --live run，最多三个 POST、独占执行标记、无客户端重试；候选需检查后决定，未加入默认测试/CI。

真实提案去除测试叶片后由本地蒙版合成，保护区与有效合成区外改变为 0，实际改变 8,855 像素。原模型提案有全图差异且经历显式尺寸适配，不能把最终像素保留归因于模型提示词或 mask 承诺。完整海报/局部检查确认叶片移除，补丁纹理稍软；接受、撤销、恢复与重开 PNG 相同，商品/Logo/中文/¥149 对象保持。InvokeAI/Krita 的原固定路径 maps_to 补充 Provider 代码及蒙版测试，未来漂移可定位到执行/保护回归；固定 SHA 和引用/许可状态保持，不表示复用其源码或兼容其运行时。

本次背景生成样本从执行到对比文件完成分别 26.514 秒（Sunburst）和 23.732 秒（Flare），画面均可承载独立排版，光影/纹理略不同；只有一张/型号，且包含本地处理，不能下稳定画质或速度排名。三次均返回 1254×1254 PNG，按显式策略保留原图并适配工程。相同 usage 不能证明相同账单，实际快照/底层映射没有报告。模型选择仍作为任务假设：背景探索可试 Flare，重要精修沿用 Sunburst 基线，再以真实样例验证。

本轮 47 项图片回归通过，全局配置/auth 字节保持，技术夹具闭环通过。证据 `dist/image-p1c-eval-2026-10-04-70f6629a/acceptance-report.json`、`visual-inspection.json`、`edit-pixel-report.json`、`edit-detail.png`、`model-comparison.png`。真实商品/透明反射、账单、稳定模型排名、Owner 批准和宿主仍未验证，业务验收为 PARTIAL；原首轮失败/离线恢复证据不改写，未提交、推送、发布或安装共享 Skill。

### 单张真实商品图验证与方法回写：2026-10-04

用户提供的 GROLAND 1254×1254 PNG 带 alpha 通道但所有像素不透明，银色泵头、半透明瓶身观感和金色流体已与白底合成。先将原图原字节留存，四周加 13px 白色 padding 到 1280 方图，原区域 sRGB RGBA 保持；素材专属保护多边形经实际查看后覆盖完整商品/标签/流体。一项 Sunburst medium 编辑改变外围背景，再复用结果做零请求边界羽化。原候选保留并丢弃，羽化候选另存、查看后接受，仍沿用 InvokeAI 的候选与版本分离方法。

保护合成延续 Krita 的上下文/生成/保护/合成分离思路；515,312 保护像素在合成图和最终 PNG 中改变均为 0，独立标题修改的框外变化为 0。标题/背景撤销、恢复、重开和完整工程 ZIP 解压重渲染均保持 PNG 摘要一致，共 6 修订。商品场景仍为扁平栅格，文字为独立对象；未新增分割器或 alpha matting 依赖，也未复制上游代码或更新研究固定 SHA。

实际案例回写到源 Skill 的 image-production.md：扁平半透明商品保留原像素时也会保留旧背景，改变透过瓶身的背景需另验收 matte，不能把像素保护当透明抠图能力。模块 README 同步该限制和当前可用工作流；真实资产只在忽略的 dist 工程留存。证据 `dist/image-real-product-2026-10-04-bc9e89f9/acceptance-report.json`、`visual-inspection.json`、`portability-report.json` 与 `groland-editable-project.zip`。

同一真实工程继续验证 Satori / resvg-js 的规格适配：1:1、4:5、9:16 分别调整文字布局及场景位置，文案只改变换行，商品场景以原尺寸摆放，三种导出的 515,312 个保护像素改变均为 0。修订重开、撤销恢复和完整 ZIP 解压后逐规格重渲染保持 PNG 摘要一致，原工程保留。实际成品已经查看，但具体平台遮挡区域尚未验收；原半透明场景的白底限制继续适用。该轮没有新的模型请求、依赖、上游代码复制或研究 SHA 更新。证据 `dist/image-real-formats-2026-10-04-b1440128/format-index.json`、`visual-inspection.json` 与 `portability-report.json`。以后升级渲染器或字体，可用这组绑定工程检查中文换行、真实标签像素和多规格复现，不能只用合成夹具证明创意质量。

同一工程的真实 Pi CLI 验收补上 OpenPencil 所启发的“Agent 操作可寻址对象并检查结果”行为证据：显式读取当前源码 Skill/图片参考/模块说明，从自然语言任务自行确定对象 ID 与批次，通过修订绑定的 dry-run、改字、规格适配和撤销，再以图片工具读取成品。独立像素/重开检查通过，没有复制上游代码、引入编辑器或改变研究 SHA。首轮在最终答复前达到 360 秒时限，单会话交付保持 PARTIAL；另一个只读会话完成检查与收尾，不能抹去首轮超时。证据 `dist/image-pi-host-2026-10-04-0419ffc7/acceptance-report.json`。这证明显式源码 Skill 的 Pi CLI 行为，不证明默认共享发现、完整扩展集合或 packaged Desktop；后续吸收宿主机制继续沿用 upstream Pi，避免另建 Agent loop。

随后同模型 low thinking 在新副本中完整复验改字→4:5→撤销→最终交付，285.622 秒、20 turn、25 工具调用，正常退出；四次实际图片读取、修订绑定、商品像素、标题框外、撤销及重开检查通过，五份全局配置/auth 保持，生图调用为 0。证据 `dist/image-pi-complete-2026-10-04-dcece006/acceptance-report.json` 与 `agent-result.md`。单会话完整样例已通过，但提示/thinking/时限有变化，不能当作稳定性能对照，也不覆盖共享发现和 Desktop；旧超时与只读收尾证据仍保留。未增加运行时依赖、公共工具 API 或新的 Agent loop。

后续以本机 upstream Pi CLI 1.0.0 的实际资源发现机制完成项目接入：`.pi/settings.json` 直接引用 canonical Skill，RPC 检查证明可信项目选择源码、忽略项目时保留用户共享版本，真实用户默认模型保持。自然语言任务只给工程位置，Agent 自行找到 Skill/执行器，完成改标题→撤销→三张 PNG 查看→最终交付；213.684 秒、18 turn、17 工具调用，商品像素/标题边界/撤销/重开及全局文件、共享树保持。证据 `dist/image-pi-discovery-2026-10-04-989bd3ef/acceptance-report.json`。此轮吸收的是原生发现机制，没有新增 Agent loop、扩展工具注册、上游编辑器源码或研究 SHA；项目配置与可选执行器仍在 Skill 发布包之外。共享目录有 8 处源码差异且不匹配安装记录，保留其现场内容；跨项目全局启用、完整扩展及 Desktop 另验。

用户随后明确确认全局 Pi 配置增量，仅向 skills 添加 canonical 源码路径，备份并保留其他设置/凭据/共享目录。仓库外真实 Pi RPC 选中该用户资源，检查无模型任务，状态 PASS_GLOBAL_ACTIVATION_AND_DISCOVERY；证据 `dist/image-global-activation-2026-10-04-6c060829/activation-receipt.json`。watch 中 OpenPencil 的 adoption 说明同步为本地对象/批次/修订与 Agent 检查方法已实现，status 仍为 reference，避免将方法承接冒充 OpenPencil 编辑器接入。未更新研究 SHA、安装交互编辑器或升级共享安装；实际可用范围与余项见[架构中的当前状态](content-production-architecture.md#pi-全局启用与当前可用范围)。

后续用真实用户配置、仓库外工程副本验证实际工具使用：Pi 仅从自然语言任务自行定位源码 Skill/执行器，将两个文字对象的位置修改合为一个批次，再撤销、查看三张 PNG 并正常交付。独立确认修改框外及商品保护区改变为 0，搬移后各修订重开一致，全局文件和共享树保持。证据 `dist/image-pi-cross-workspace-2026-10-04-8021ff3a/acceptance-report.json`；继续沿用 upstream Pi 和原执行器，没有新依赖、工具协议或 Agent loop。这补充了 OpenPencil 对象/检查方法在跨 cwd 使用中的行为证据，没有扩大上游引擎集成状态或刷新研究 SHA。

该素材的受控外围背景/可编辑标题/保存迁移通过，深色透射背景、重打光、独立商品抠图、更广泛真实商品质量、公开文案/Owner 批准、账单和宿主仍未验证，业务验收继续 PARTIAL。本轮只发出一项真实 POST，未提交、推送、发布或安装共享 Skill。

### 图片 RGBA 合成承接：2026-10-04

按图片工程范围补充已有 Satori/resvg/Sharp 组合的已知透明度验收。`integrations/image-production/alpha-smoke.mjs` 将浅/深底合成、透明与不透明像素、隐藏 RGB 的缩放污染、对象透明度、contain/cover、候选接受、撤销、重开及迁移连成一项可复现回归；`tests/alpha.test.mjs` 已进入现有 `npm test`。15 项检查、图片模块 48 项测试通过，证据 `dist/image-alpha-2026-10-04-e029b940/acceptance-report.json`。以后涉及这些渲染依赖的上游 diff，除读取变化和更新固定点外，应运行该测试；需要保留对照工程时运行 `npm run smoke:alpha`。

本轮增加本地行为证据，没有更新上游研究 SHA、采用状态或依赖版本。透明度来自人工夹具，不能证明已吸收真实商品的自动抠图、玻璃透射/反射或去白边机制。后续对用户白底扁平瓶子的 matte 与背景融合应先提供对应质量证据，再确定承接文件与采用范围。

### 真实商品 matting 比较：2026-10-04

对用户 1254×1254 白底扁平 GROLAND 图进行了本地有界比较，没有真实图片 Provider 请求。Apple Vision revision 1 生成全实例前景基线（本机系统能力，未加入正式执行器）；随后在 `dist/image-matte-2026-10-04-4224e675/venv` 中隔离安装 PyMatting 1.1.16，按[官方示例](https://pymatting.github.io/examples.html)分别比较 alpha 估计与前景 RGB 估计，读取固定研究点的 README、alpha/foreground 实现和根许可。发布包版本与 GitHub 研究 SHA 分别记录，没有把研究 main 视为安装版本。

观察到三类问题：native 轮廓的白色残留；8px 外部不确定带的闭式 alpha 在泵头/油池边缘产生颗粒；只估计颜色而保留 native alpha 未解决粗白边。将外部不确定带缩至 1px 后，瓶身边缘及细油流改善，但深底仍有边缘颗粒和油池内部旧白底。全部对照保留，状态 `PARTIAL_REAL_PRODUCT_MATTING_LIGHT_REVIEW_CANDIDATE`。这验证了“选区、alpha、前景颜色、最终合成”分别检查的必要性，没有证明玻璃内部透射或重新照明已恢复。原始 RGB 乘一个 alpha 不是完整抠图交付。

采用范围仅为独立试验工程里的浅色预览候选：商品/油流/液体池整体 RGBA 场景层 + 独立文字。10 项工程检查通过，六次不缩放 PNG 导出各 59,159 个包装保护像素改变为 0，291,174 个声明为不透明的核心 RGB 保持；整体层移动/缩放、撤销、重开及迁移通过，既有商品工程完整文件摘要保持。此包装保护区与此前 515,312 像素的保守扁平场景保护区不同，不能混用；缩放后的画布是重采样结果。证据 `dist/image-matte-2026-10-04-4224e675/acceptance-report.json`、`project-acceptance-report.json`、`visual-inspection.json` 与 `README.md`。

PyMatting 新增四条监控路径，状态保持 candidate，正式 package.json/lock、CLI、Schema 和共享 Skill 不变。后续升级或正式接入必须用本例的浅/深底、泵头、瓶身边缘、细油流、油池与包装保护重验；深底失败不得被技术回执升级。原生 Vision 为 macOS 平台基线，其他平台和其他素材未验。下一质量缺口是实际前景 RGB/内部透明度及油池的背景融合，不直接把此单张白底照片试验设为通用自动抠图后端。

### Sunburst 透明输出与保护合成比较：2026-10-04

在 PyMatting 浅底试验后，用现有 Sunburst 别名做了一次真实透明请求。官方透明参数与本机实际返回分别核验；返回有真实 alpha、外边缘更干净，但包装/商品原色也改变，说明“模型承诺保持”仍需受控合成。既有 masked candidate/compositor 保留 291,174 个声明不透明的原图核心像素，其中包装 59,159 像素。只保护文字的色差方案已丢弃，核心保护版保持 ready 待审阅；深底的油池白块没有解决。

本次承接的是先前从 InvokeAI/Krita 提炼的候选与应用分离、生成范围与最终保护范围分离，在本仓实现上的真实素材验证。不是复制新上游源码、推进所有项目采用状态或证明光学恢复。正式 Image Job v2/Adapter 的 transparent 合同尚未扩展；试验使用未修改的 imagegen CLI，源工程和 config/auth 保持。额外 Python SDK 仅在试验 venv，未成为运行时依赖；研究 SHA、watch 路径和采用状态均未变。

证据 `dist/image-sunburst-alpha-2026-10-04-3338ec38/acceptance-report.json`、`visual-inspection.json` 及 `delivery-verification.json`；可编辑包保留旧版当前修订和未接受的新候选。后续上游更新验收应保留本次“有 alpha 但改了商品色”“仅保护文字仍出现色差”“深底光学失败”三类案例，避免把端点支持当成产品质量证明。机制和下一验收边界见[透明候选记录](content-production-architecture.md#sunburst-透明候选与商品原像素保护)。

### 透明协议承接：2026-10-04 至 10-05

用户确认后，透明输出进入本仓 canonical v2 与 Sunburst/Flare Adapter。承接文件为 image-job-v2 Schema、canonical 语义校验、可选 provider profiles、`provider-alpha.mjs`、Provider 执行/恢复/读回及候选合成检查。接收、缩放后和最终合成的 alpha 分别验证；原像素保护、候选/接受分离及失败产物保留沿用既有机制。旧 v1/不支持模型保持拒绝，普通回执兼容。

这把上一轮研究结论转为可执行检查与回归，而非新增第三方源码或依赖。上游固定 SHA、watch 路径和候选项目采用状态未变。真实产品缓存离线回放的保护像素、重开及迁移通过，未新增外部模型请求；有 alpha 仍不等于透射/反射正确，深底油池失败继续留存。证据 `dist/image-transparent-contract-2026-10-04-92fb3d73/acceptance-report.json`；详细协议及证据边界见[架构](content-production-architecture.md#透明任务协议正式承接)。

### 真实透明执行与几何失败样例：2026-10-05

正式 Adapter 经用户全局网关完成一次 Sunburst 透明请求。返回含真实 alpha，但尺寸由所请求的 1280 变为 1254；原始 partial 结果保留，显式离线恢复及候选读回/迁移通过。局部原像素保护再次验证，但模型改变商品位置和尺度，保护合成产生双泵头与双层油池；浅/深底均拒绝，并完成 discarded 状态和不可接受检查，未替换当前工程。

此例继续验证 InvokeAI/Krita 所启发的候选/应用分离与保护合成，同时暴露其前提：生成结果的内容必须与保护区对齐，栅格尺寸一致和保护像素不变不足以证明该前提。将“有 alpha、保护像素全保持，但整体几何失真”作为后续上游变化评估的真实失败样例，补查保护边界接缝、重复轮廓及光学污染。当前是人工实际看图后拒绝；没有声称已经实现自动几何质量评分。

证据 `dist/image-transparent-live-2026-10-05-f08c2d91/acceptance-report.json`、`visual-inspection.json` 与 `comparison.png`；[执行与质量边界](content-production-architecture.md#正式透明-adapter-真实网关验收)。本轮没有复制上游源码、引入依赖、更新研究 SHA/watch 路径或扩大项目采用状态，未新增自动跟踪/自动吸收流程。

### 局部边缘维护承接：2026-10-05

在真实生成发生几何漂移后，复用已留存的 PyMatting 输出，将泵头处理限定于资产专用边缘带；比较颜色传播和受原始 50% alpha 分类约束的局部平滑。最终全图 3,070 像素改变，轮廓分类、包装/核心及边缘带外原像素保持；进入现有 masked candidate 后的局部 context、读回、接受/撤销与迁移通过。视觉改善有限，浅底候选待审阅，深底光学仍失败。

本次承接的是区域约束、确定性处理与候选决策的工程方法，没有增加新的上游算法采用、生产依赖或 watch 固定点。后续吸收应保留“平滑改变轮廓须拦截”“ROI 外零变化”“导出与素材坐标对应”三类检查；50% alpha 轮廓一致仅是该试验的对齐证据，不是通用保真评分。证据 `dist/image-edge-local-2026-10-05-c1849a62/acceptance-report.json`；[局部验收及失败记录](content-production-architecture.md#固定位置的泵头局部边缘验收)。

### 候选导出证据承接：2026-10-05

候选/应用分离进一步落到独立预览回执：复用现有候选状态核验，保留待审阅、已丢弃、过期、决定处理中及已接受后撤销的上下文；技术 completed 与 visual_quality=UNVERIFIED 继续分开。真实拒绝候选的状态缺失已复现并修复，决定绑定损坏时停止导出；72 项图片回归及三个真实工程的状态/PNG 保持检查通过。证据 `dist/image-candidate-context-2026-10-05-52d098c1/acceptance-report.json`；[导出上下文](content-production-architecture.md#候选导出的状态上下文)。这是本仓既有机制的证据补全，没有新增上游源码复用、依赖或研究 SHA/watch 更新。

### 图片模块收尾与上游增量核查：2026-10-05

这轮完成的是 image 模块的有界核查及三项缺陷修复，没有全仓评分或发布结论。撤销现在遵守锁定对象的层级保护；弃用说明的序列化读写上限一致；验收报告分别表达 Provider 结果与候选/对比完成情况。6 项定向回归、78 项图片完整测试及两组只读独立复核通过。详细证据：`dist/image-closeout-2026-10-05-901be134/acceptance-report.json`。

实际运行 drift 工具检查 OpenPencil、InvokeAI、Krita AI Diffusion、Satori、Sharp，共 15 个监测路径。OpenPencil 的 MCP 文档与工具 Schema 有变化，LICENSE 路径未变；其他四个项目的监测路径未变，Satori/Sharp 的 npm latest 分别仍为当前固定的 0.35.0/0.35.5。仓库 HEAD 可能推进而监测路径不变，此结果只覆盖所列路径；其余 21 个登记项未在本轮联网刷新。原始报告：`dist/image-closeout-2026-10-05-901be134/upstream-live.json`。

OpenPencil 从 `aeba9a6bd5a416007e42086db438ffc9c71fb3c9` 到 `6a05e30f15398de70d36deda011003b4347d1627` 的两个监测文件 diff 已逐项阅读，Schema 全文及 MCP 对应段落已核对。以下是本项目的适用性判断，不代表运行了上游新功能。[固定版本 MCP 文档](https://github.com/open-pencil/open-pencil/blob/6a05e30f15398de70d36deda011003b4347d1627/packages/docs/programmable/mcp-server.md)；[工具 Schema](https://github.com/open-pencil/open-pencil/blob/6a05e30f15398de70d36deda011003b4347d1627/packages/core/src/tools/schema.ts)。

| 上游增量 | 本地承接与决定 |
| --- | --- |
| MCP/CLI 撤销不跨过最近的人工作业；每次编辑调用形成一个历史步骤 | **DOCUMENT / DEFER**：本地已有显式 base revision、不可变修订和隔离 revert；本轮补齐锁定层级校验。现有 author 是来源声明，不能冒充已实现可信的操作者归属或只撤销 Agent 自己的操作。未来接入共享编辑器、引入可信操作来源时再设计该能力。 |
| 关闭有未保存内容的文档须显式选择 save/discard；另设 activate_document | **DEFER**：本地工程提交即持久化，无活跃 tab 或未保存 GUI 状态；目前不添加空壳接口。未来编辑器必须保留明确的保存/丢弃决定与目标工程身份。 |
| Schema 增加 settings:read/write；文档将设置工具与凭据等配置分开 | **KEEP / DEFER**：当前 image 工具不提供全局设置写入，Provider 配置只读且不持久化密钥；保持此边界。没有设置工具调用方，不引入新的权限体系。 |
| 文档新增 lint/lint_fix，区分修复与建议 | **KEEP / DEFER**：保留现有文档、字形、边界、合成及渲染检查和可回滚批次；不将技术检查升级为视觉批准，也不新增未经样例验证的自动美化。 |

以上研究范围已完成，OpenPencil 的 watch 研究固定点更新到该 SHA，`status=reference` 与现有 adoption 保持；其含义是监测文件已审阅，不是整套编辑器已吸收、依赖升级或源码复用。方法取舍落在此记录，运行逻辑仍由本地合同及回归决定。其他固定点保持。本次使用现有手动跟踪工具，没有添加定时任务或自动升级。

维护闭环继续使用：drift 检查 → 阅读变化及适用范围 → 在此记录 KEEP/采用/DEFER 及本地落点 → 必要改动和回归 → 更新已审阅研究点。只有新增实际需求、失败样例或上游变化才启动下一轮；不以持续改动代替质量验收。

### 共享安装承接：2026-10-04

在后续独立授权下，将当前 canonical Skill 候选安装到 `~/.agents/skills/creative-craft`：8 个文件更新、7 个视频合同/命令/模板文件补齐，90 个内容文件与源码一致，完整旧目录备份和 provenance 绑定检查通过。安装后的 21 项模板合同自检通过；Codex 原生资源列表在仓库内外发现启用的共享 Skill，Pi 共享自动发现及真实用户全局源码选择均通过，三组检查没有提交模型任务。证据 `dist/shared-skill-upgrade-2026-10-04-5bda3972/acceptance-report.json`；安装/宿主边界见[架构记录](content-production-architecture.md#共享-skill-升级与宿主发现)。

这使已验证的图片方法文档与视频合同进入本机共享安装，未新增上游源码复用、引擎集成或研究 SHA 更新，也未打包图片执行器/依赖/字体。watch 的固定点、路径映射及采用状态保持；未来上游变化仍须读取 diff、定位承接文件、运行对应工程回归后再采用，安装同步不等于持续吸收已自动运行。当前为 0.3.2 未发布候选，完整扩展集、模型注入和 Desktop/AIOS/Windows 仍是独立证据；未提交、推送或发布。

后续沿用 upstream Pi 的实际启用扩展配置验证同一对象操作方法，没有新建 Agent loop 或扩展 Tool。原生 RPC 登记 28 个扩展命令；自然语言编辑/撤销/实际图片检查复验通过，保护像素、文字边界、原工程、配置/auth 与共享安装保持。证据 `dist/image-pi-daily-2026-10-04-e32f1850/acceptance-report.json`。首轮有未归因的 Codex config 漂移，原失败记录保留；四项既有扩展依赖声明告警未修复，仅本会话记忆只读，不能扩展为全部扩展业务或记忆写入验收。真实 Desktop 尝试因 Computer Use native pipe 不可用而未执行图片任务，记录在首轮 `desktop-attempt.json`。本轮更新的是宿主证据范围，没有改变上游研究 SHA、adoption 或运行时依赖；完整记录见[架构状态](content-production-architecture.md#当前启用扩展的图片操作与-desktop-阻塞)。
