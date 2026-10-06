# Creative Craft 内容制作架构

日期：2026-09-22；图片 P0/P1 更新：2026-10-04。状态：通用方法、可选本地视频与图片对象/候选/蒙版已有部分实现；图片 Provider Adapter、真实生成/蒙版编辑、单样例双型号对照及一张真实商品的保真/排版/外围背景闭环已验证。显式源码 Skill 的真实 Pi CLI 单会话编辑/查看/撤销/交付复验通过，保留首轮超时记录。复杂抠图与透明背景适配、费用、Desktop/AIOS 接入及正式业务验收仍待补证。AIOS（原 DataHub）工作区重构为待实施合同。宿主已有媒体容器运行观察，不等于完整制作、真实模型质量或生产性能验收。

配套：[上游吸收登记](upstream-absorption.md)、[现有架构](architecture.md)、[运行方式](operating-model.md)。本文件描述新增方向，不将未来能力改写为当前 API。

图片执行层的范围、实施顺序和验收见 [Image Harness v1](#image-harness-v1)；视频历史状态保留如下。

## 目标与当前差距

Creative Craft 是可被不同 Agent 与产品调用的创意制作能力。目标是更好的构思、图片制作、脚本、选片、剪辑与实际交付，同时支持营销图片及电商、品牌、口播等短中视频。AIOS 是首个业务宿主，历史记录中的 DataHub 指其原工程；核心能力保持跨宿主通用性。

现有 Brief、Concept Routes、Creative Direction、Copy Sheet、Brand/Reference Binding、Image/Video Job、Receipt、Inspection、Revision 和 Delivery 合同可以复用。核心 Python CLI 做校验、提示词编译和证据管理；没有直接模型调用、片段搜索服务或视频渲染器。Provider Profile 描述能力，不能证明账户已可调用。

可选的 [local-production 模块](../integrations/local-production/README.md) 已实现独立本地工程、版本化编辑、字幕/音轨及 HyperFrames 预览和导出。当前为源仓库可用的基础执行工具；除合成媒体检查外，DataHub 已通过宿主适配调用该模块完成真实缓存素材的本地隔离渲染。模块本身不包含自然语言规划器、DataHub 连接或真实业务创意验收；宿主适配存在不等于核心内置连接。其 local-edit/local-render 实验合同与现有正式交付合同分开，不能据此推进既有项目的 approved/delivered 状态。

Quick Craft 保持默认轻量路径。简单文案、概念或局部修改无需创建完整项目文件；真正制作与反复修改视频时，由宿主在后台保存必要工程状态。通用内容无需虚构商品、促销或转化目标。

## AIOS 产品接入：先剪辑，后创作

宿主将现有素材库的“视频创作”重构为 AI 剪辑，再增加 AI 创作。Agent 是宿主结合专业方法、模型 API、受控工具、持久任务与检查形成的执行能力，不要求聊天界面或独立 Creative Craft 服务。

AI 剪辑以已有画面为基础，支持智能成片、口播精剪、多素材混剪、原片改版、高光/摘要、批量变体；默认一条。AI 创作后续结合已有素材与经账户验证的 Seedance 等生成能力。平台投放与经营自动化不是普通制作的前置条件，通用方法不要求虚构商品或 ROI。

方法输出可见的制作方案，含结构、来源选择、字幕声音、保留/改变与缺口。默认自动执行，用户可选先看方案，也可暂停后修改、锁定满意部分和重新制作。宿主持有 plan/project revision 与执行版本，迟到结果不得覆盖用户新方案；Creative Craft 只基于最新快照提出有界编辑和检查意见。

## 三层职责

| 层 | 所有权 | 明确边界 |
| --- | --- | --- |
| 核心 Skill 与方法 | 需求理解、创意路线、参考片拆解、分镜、选片策略、剪辑决策、质量检查与迭代 | 不含特定宿主数据库、账户、对象存储和投放表结构 |
| 可选制作集成 | 工具调用、引擎编译、生成/渲染执行、进度与结果转换 | 不让网络、Node、Chromium、FFmpeg 变成轻量 Skill 安装的强制依赖 |
| 业务宿主 | 素材身份、检索、权限、存储、队列、界面、成本配置和效果数据 | 调用固定版本的能力包，不维护另一份分叉 Skill |

现有 Python 标准库核心与 v1/v2 合同继续兼容。制作集成采用独立可选模块；现有 `adapters/` 是 Agent 宿主发现与接入说明，不直接混入渲染引擎实现。已实现的首个可选执行集成为 HyperFrames，FFmpeg 负责媒体预处理及底层编码；Seedance 仍是生成或修改镜头的待接入方向。

## 交付与包边界

轻量方法包、可选制作执行包分别发布，后者才携带 Node/Chromium/FFmpeg 或引擎依赖。当前根包 files 不包含 `integrations/local-production`；AIOS 已用内容摘要锁快照装入自己的媒体镜像，不等于安装主 Skill 就获得制作模块，也不等于该模块已正式发布。

正式制品需要记录源码 revision、制品摘要、合同版本和兼容范围，并验证包内实际文件。AIOS 构建加载固定版本，运行时不读取个人 Skills 或临时更新上游；在途任务继续原锁，不兼容明确失败，升级/回退只改变新任务默认值。

通用适配器只接收经过宿主解析的确定媒体、工程输入及执行限制，返回产物/回执。认识 AIOS 数据库、素材权限、队列或预算的代码留在 AIOS；不因可能复用就提前增加公共框架。Creative Craft 不维护宿主的第二套工程或成功状态。

Commerce Growth OS 拥有经营策略和内容组合的专业方法，Creative Craft 接收其适用输出并发展概念、脚本和制作；宿主映射既有 Brief、Copy、EditDocument、Inspection，避免另造同义对象。每项交付一个主责，简单任务不强制完整策略流程。

## 制作流程与分析层次

主流程：需求 → 创意与脚本 → 分镜 → 搜索候选素材 → 选择/生成镜头 → 工程编辑 → 实际预览与检查 → 修改 → 导出 → 复盘。

按需工作流包括素材混剪、口播编辑、品牌/产品视频、参考片再创作、内容变体和成片检查。一个 Agent 可以完成多个步骤，不为每个角色默认启动独立 Agent。

分析区分：

1. 内容事实：画面、语音、文字和真实时间范围。
2. 创作判断：表达作用、可复用优点、节奏与连续性。
3. 效果诊断：投放或传播数据、比较窗口和证据边界。
4. 制作决策：具体片段、脚本修改、生成镜头和编辑动作。

整条素材表现好不能直接证明某个片段有效。品牌、口播和电商共享事实层，使用不同目标的评价；缺效果数据时仍可制作和评价内容，不虚构业务提升。

## 宿主能力接口方向

下表是跨宿主语义接口方向，不是已上线 endpoint 或 MCP 工具名。DataHub 已实现其中部分宿主能力，但尚未沉淀为 Creative Craft 通用工具接口；具体状态见下文与吸收登记。实现时先复用现有合同，只有新行为确实无法表达时再增加版本化类型。

| 能力 | 输入与结果 |
| --- | --- |
| 检索片段 | 意图、素材范围、时长及使用条件 → 稳定资产/版本/片段引用、起止时间、匹配证据与可用性 |
| 读取素材证据 | 精确引用 → 转写、画面、OCR、品牌事实与来源；未知项保持未知 |
| 创建制作任务 | Brief、分镜、引用、输出目标与预算 → 可恢复任务 ID 与状态 |
| 读取/修改工程 | 工程 ID、预期版本及有界编辑操作 → 新版本、变更摘要或明确冲突 |
| 生成镜头 | 已选参考、修改/保持约束、Provider 能力与预算 → Provider 任务、产物及执行回执 |
| 预览/渲染/检查 | 确定工程版本 → 进度、实际产物、检查证据与失败原因 |

宿主提供经过权限校验的素材解析器；公共核心只认识稳定引用。signed URL 是临时传输地址，不作为永久资产身份。API 密钥、内部地址及客户素材不进入公共仓库或共享 Skill。

## 工程状态与可编辑性

每个创作项目关联 Brief、分镜、素材引用、生成任务和工程版本。Agent 与人工使用同一编辑接口；提交基于预期版本，冲突时重读，不能覆盖用户刚完成的调整。

采用宿主持有的版本化剪辑描述作为受支持时间线操作的真源。引擎 HTML/配置为编译产物；自定义图形片段同时保存源文件和可编辑参数，以组件引用接入。首期不承诺任意 HTML 都能无损还原为可视化多轨编辑。

源时间与成片时间分开保存，源切点依据真实媒体时间戳校正。素材替换、变速、删段时同步更新相关音轨和字幕。导出固定工程版本及素材 hash，预览或重新渲染不悄悄采用最新素材。

继续复用 Receipt、Inspection 和 Revision 语义。生成、剪辑、渲染是不同任务，不能把合成任务伪装成一次 Video Job 模型生成；历史合同只读兼容，不自动迁移或批准。

## 执行约束

- Skills 固定受审阅版本、按需加载；不把上游自动更新、安装或默认 Provider 策略直接带入宿主。
- 长任务运行在隔离 worker；浏览器预览与生成代码不获得 DataHub 页面会话或服务端秘密。项目文件范围、网络访问和运行资源按任务限制。
- 宿主已有队列负责调度；重试先核实远端任务状态，保留幂等标识和计费记录，不因超时盲目重发生成请求。
- 各阶段保存可恢复结果，失败或取消不写成功回执；预算耗尽停止新的付费动作并保存已有候选。
- 技术结构检查、实际画面/听检和创意评价分别记录。模型自评不能冒充人工验收，单次成功不能变成普遍创意规律。

## 验证与实施顺序

独立制作和宿主局部接入已有基础；下一步验证 AIOS 自动剪辑及方案中途修改，随后真实生成混合制作。效果回流属于后续经营扩展。先验证已有 HyperFrames/FFmpeg 路径及普通编辑快路径，不预先实现多个引擎适配。

共同样例：口播删段加 B-roll 与中文字幕；品牌片加入新生成镜头和图形包装；电商片输出不同开场版本。每类都验证预览、再次编辑、重开工程、导出和来源追踪。

对照固定同一组素材、Brief 和输出约束，比较当前 Creative Craft 与升级后的表达质量、素材适配、剪辑连贯性、人工修改量、耗时和成本；分别记录模型、Skill、引擎版本。只有真实输出和检查证据才能证明质量改善。

设计文档阶段后已实现独立本地 MVP；DataHub 的项目、台词分镜、原片分析段落检索、镜头提取队列、目录导入、代表帧语义任务和目录范围关键词检索已有本地实现与限定验证。真实模型创意/识别质量、时序多模态检索、Seedance 混合成片、公共接口沉淀、正式制品发布、目标环境完整制作与负载仍待后续验收。现有未提交工作不因此被覆盖或发布。


## 当前接入状态与下一步

详细状态与证据定位统一见 [宿主验证状态更新](upstream-absorption.md#宿主验证状态更新2026-09-20)。DataHub 提供的队列、索引和界面留在宿主；Creative Craft 可复用的是创作/编辑方法、片段证据使用规则与可选制作集成。单帧描述不是动作识别，文字关键词匹配不是完整视频 RAG，模型模拟服务通过也不是识别质量通过。

下一批优先补通用编辑流程和选片证据合同，再验证已有素材与生成镜头混合制作。范围、承接与完成条件见 [下一批吸收与验收](upstream-absorption.md#下一批吸收与验收计划尚未完成)。这些是待办方向，不改变现有 API、Skill 加载方式或发布状态。

## 宿主性能与方法收益的验收边界

AIOS 首期目标约 10 用户、每天 50 条合格成片；已分析素材、30—60 秒/1080p，含排队 p50 ≤3 分钟、p95 ≤5 分钟是宿主待实测目标，不是 Creative Craft 对所有宿主的性能保证。1/2 渲染槽、10 用户突发、冷素材和复杂工程各自测量，容量以宿主 `docs/autonomous-content-production/05-capacity-cost-and-operations.md` 为真源。

对照人工/既有规则、仅经营方法、仅创作方法与组合方案，使用同一输入和质量标准；经营方法对照限有相关业务任务的样本。报告成片盲评、事实错误、总耗时、返工与人工分钟，以及方法加载/执行的额外成本。组件安装成功、容器运行或短样片不代表专业质量提高。

业务经验留宿主；通用方法候选经脱敏、跨任务验证和仓库评测后发布。生产 Agent 不直接修改共享 Skill、权限或验收标准。本次文档同步未更新 Skill、模块代码、包清单或任何宿主运行配置。

## Video Harness v1（2026-10-02，实施中）

承接上文三层职责，把“需求 → 分镜 → 选片 → 生成 → 工程编辑 → 实际检查 → 修改 → 导出”落成代码强制的流程。参考依据见[上游复核 2026-10-02](upstream-absorption.md)：阶段关卡与交付承诺（OpenMontage）、素材/实例分离与合成画面验证（ChatCut）、批次编辑与试运行（OpenChatCut）、lint/抽帧/检查（HyperFrames）、按模态证据（Cerul）。只吸收方法，不复制 AGPL 源码；Remotion 与 OpenCut 维持原处置。

### 分层与真源

| 层 | 内容 | 位置 |
| --- | --- | --- |
| 共享合同 | `creative-craft.edit-document.v2`（多轨剪辑真源）、`creative-craft.render-qa.v1`（成片技术检查与评审） | `skills/creative-craft/schemas/`；跨语言语义一致性样例在 `tests/fixtures/edit-document-v2/{valid,invalid}/` |
| 证据与关卡（Python 核心） | `creative-craft.production-plan.v1`（分镜每拍的来源、选片证据、交付承诺）、`creative-craft.video-production.v1`（阶段状态、产物 digest、审批、修改轮次、预算台账、事件） | Skill 包内，仅标准库 |
| 执行（可选 Node 模块） | EditDocument v2 读写与有界编辑、编译到 HyperFrames、预览/导出、QA 采样与检测 | `integrations/local-production/`，不进 Skill 包 |

EditDocument v2 是剪辑真源；HyperFrames HTML 只是编译产物，不反向解析。v1（`local-edit.v1`）旧修订保持只读；首次对 v1 工程提交编辑时在内存中迁移并发布 v2 新修订（`change.author = migration` 记录在该修订），旧文件不改写。

### EditDocument v2 语义规则

- 素材（asset）与时间线实例（item）分离；同一素材可被多处引用。工程创建后可通过 `add_asset` 继续导入（含生成镜头，`origin.kind = generated` 并记录 `provenance_ref`）。
- 轨道 `video | audio | caption`，数组顺序即视频叠放顺序（靠前在下）。`locked` 轨道上的 item 不可被任何操作修改。
- 输出时间为 canvas.fps 下的整数帧，半开区间；源时间为秒。同一轨道上的 media item 不可重叠，允许空隙。
- media item 必须有 `asset_id/start_frame/frames/source_in_seconds/volume`；视频轨要求素材含画面，音频轨要求含声音；`source_in_seconds + frames/fps ≤ asset.duration`。
- caption item 只能在 caption 轨：`link` 形式按所链接 media item 的源时间换算输出时间并随其移动、裁切；无 `link` 时必须给 `start_frame/frames`。`link.source_to > link.source_from`。
- 成片时长 = 所有 media item 与非链接字幕的最大结束帧，1 帧至 10 分钟。
- 字段按类型互斥：media item 不得带 `text/style/link`；caption item 不得带 `asset_id/source_in_seconds/volume`；音频轨 item 不得带 `fit/opacity/transform`；link 字幕不得带 `start_frame/frames`。`revision > 1` 必须有 `parent_sha256`，`revision = 1` 必须为 null。字幕之间允许重叠。
- 以上规则在 Node（`integrations/local-production/edit-document.mjs`）与 Python（`creative_craft_contracts.py`）各实现一次，由 `tests/fixtures/edit-document-v2/` 共享样例强制一致；新增规则必须同时补样例。

### P2 语义规则：包装与音频（2026-10-02，已实现：合成素材验证）

在 EditDocument v2 上增加可选字段，旧文档继续合法；Node 与 Python 同步实现，`tests/fixtures/edit-document-v2/valid/p2-packaging.json` 与对应 `invalid/` 样例强制一致。

- **变速** `speed`（media，0.1–10，缺省 1）：源区间 = `source_in_seconds + frames / fps × speed`，必须在素材时长 + 0.001 s 内；link 字幕的输出时间按同一比例换算。
- **淡变** `fade_in_frames` / `fade_out_frames`（media、graphic）：两者之和不超过 `frames`；视频画面为透明度，声音为音量包络。caption 不得带 speed、淡变或转场字段。
- **转场** `transition_in: {kind: "crossfade", frames}`（media）：同一轨道上 item 不得重叠，唯一例外是后一 item 声明 crossfade 且与紧邻前一 item 的重叠帧数恰好等于 `frames`，`frames` 不超过两者各自长度；声明了 crossfade 却没有重叠同样无效。
- **自动闪避** 轨道 `duck: {under_track_id, depth_db (−24…−3), attack_frames, release_frames}`：只允许在 audio 轨；`under_track_id` 必须存在、不能是自身、可以是 video 或 audio 轨，且被参照的轨道自身不能再带 `duck`（只有一层）。编译时依据被参照轨道上有声 media item 的区间生成音量包络。
- **图形** item `kind: "graphic"`：只在 video 轨，参与同轨不重叠与成片时长计算；必须有 `template`、`vars`、`start_frame`、`frames`，可带淡变与 `opacity`，不得带 media/caption 字段。`vars` 的值只能是字符串（1–200 字符）、有限数字或布尔值。模板定义（变量类型、固定 HTML/CSS、安全区）属于执行层 `integrations/local-production/templates/`，变量类型与模板存在性由 Node 校验；Python 只校验结构。首批模板：`lower-third`、`title-card`。不接受任意 HTML、脚本或外部 URL。
- **执行映射**：变速用 HyperFrames `data-playback-rate`；淡变、转场与闪避的音量统一写入 `data-automation` volume lane，不同时使用音量补间；画面淡变与转场使用透明度时间线。
- **补充约定**：crossfade 重叠帧数 = 紧邻前一 item 的结束帧 − 后一 item 的起点，前一 item 必须是 media，后一 item 必须结束得比前一 item 晚（不能嵌套其中）；graphic `vars` 的键名须匹配 `^[a-z][a-z0-9_]{0,31}$`，字符串长度按 UTF-16 码元计（1–200）；volume 自动化每条最多 512 点，在编辑提交与创建时即校验，不留到渲染才失败；锁定冻结的是该轨道自身的 item 与设置（含 `duck` 配置，回退也不得改动），不冻结由被参照轨道派生的闪避包络。graphic 字段白名单为 `id/track_id/kind/template/vars/start_frame/frames/fade_in_frames/fade_out_frames/opacity`；`duck` 不能指向 caption 轨；crossfade 的后一 item 起点必须严格晚于前一 item，且同轨重叠检查覆盖所有在前 item。
- **生成镜头占比** 承诺只统计 media 画面，graphic 叠层不计入遮挡；crossfade 重叠区间内任一段为生成素材即计为生成（上界计法）。
- **导出人工评审** `policy.export_requires_human_review`（可选，缺省 false）：为 true 时，inspect 阶段在评审接受后必须再经显式签字 `video-approve --stage inspect --by <name>` 才能完成，导出所依据的那次通过检查必须带有该签字。render-qa 中的 `review.reviewer_kind` 只是 Agent 写入的说明，不作为人工证据。边界：本地 CLI 无法核实签字人是否真人，签字只提供具名、可追溯的责任记录；真实身份认证由宿主（如 AIOS 的登录用户）绑定到签字动作。
- **QA 补充**：引用渲染回执中的 `audioLoweredDb` 作为真峰值限幅证据；字幕与图形采样帧检查安全区（距画面边缘 5%）。

### 图形模板固定到修订（2026-10-03）

修订是可复现的渲染依据，图形模板也必须随修订固定，而不是只按 id 引用当前执行层模板。

- 顶层可选字段 `graphic_templates: [{id, version, sha256, file}]`：`file` 必须等于 `templates/<sha256>.json`，是模板 JSON 原始字节按内容寻址复制进工程目录的文件。字段存在时，每个 graphic item 的 `template` 必须恰有一个同 id 的绑定；绑定 id 不得重复，也不得存在未被任何 graphic 使用的绑定。
- 字段缺失的历史修订仍然有效，渲染使用当前执行层模板，回执标记 `pinned: false`；不自动改写旧修订。
- Node 执行层：创建或编辑产生的新修订只要含 graphic，就绑定所用模板（首次使用时复制当前模板字节）；渲染只从工程内绑定文件加载模板，核对 sha256 并重新执行模板校验，缺失或不符即失败。显式操作 `rebind_template {template}` 把某个模板升级到当前执行层版本，必须单独成批，作为可追溯的决定；涉及锁定轨道上的 graphic 时拒绝，字节无变化时拒绝。`revert_to` 把绑定视为修订内容的一部分，恢复目标修订的绑定（工程内按内容寻址的旧字节仍可用），锁定轨道上的 graphic 不得因此改变所用模板字节。其余操作不会改变已有绑定。绑定写入的是经执行层最小字号规范化后的模板字节，加载时只核对摘要并做安全/结构校验、不再改写；若后续校验规则拒绝旧绑定则明确失败，而不是静默改变渲染。
- Python 只校验结构与覆盖规则；模板内容与变量类型仍由 Node 校验。

### 源素材帧对齐（2026-10-03）

真实素材验证发现：入点写成 24.4333 而镜头首帧是 733/30 时，渲染取到上一帧，所有自动检查都通过。根因修复是在编译时把入点对齐到源素材帧网格，而不是事后由 QA 报警。

- asset 可选字段 `frame_rate`（有理数字符串，如 `"30/1"`、`"30000/1001"`），由导入时 ffprobe 读取写入；仅含画面的素材可带此字段。
- 对带 `frame_rate` 的视频素材，只修正“小数截断”这一种情况：视频轨 media item 的源入点若低于某帧起点不超过 2 ms 且不足 0.1 帧（覆盖截到毫秒的写法，如 30 fps 第 733 帧写成 24.433 或 24.4333），编译为该帧起点 + 0.1 ms；其余入点保持原值不变（避免整体位移破坏拆分连续性、音频精确入点与片尾范围）。音频轨 item 不做处理。编辑文档中的数值不被改写。
- 只有视频流起点（`start_pts × time_base`）等于所有流最早起点（渲染器与 QA 共同的媒体时间零点）的恒定帧率素材才记录 `frame_rate`；所有流同一非零起点也记录（MKV 与 MP4 edit list 均实测渲染器以该起点为零点），音频早于视频开始（如 MKV/WebM 保留的负音频起点、MP4 中 AAC 编码延迟造成的提前）则不记录。渲染与 QA 编译前按同一规则复核已有 `frame_rate`（旧工程可能带有过期值），不满足的素材不做修正并在渲染回执 `frame_alignment` 中记录原因，工程文件不改写。`video` 标记与宽高保持原行为（第一条视频流，封面图也算）；仅当第一条视频流不是封面图时才记录帧率，保证帧率与宽高来自同一条流。
- 编译视图只计算一次，渲染、字幕与 QA 剪辑点检查共用；无 `frame_rate` 的历史素材保持原行为并继续由 QA 报警。

### 编辑操作（P0）

一次调用提交一个批次：`{ base_revision, author, summary, operations[] }`。整批校验通过才发布新修订；`--dry-run` 只返回 diff（新增/删除/变更的 item、时长变化）不发布；基于过期修订提交直接拒绝，需重读。操作：`add_asset`、`add_track`、`edit_track`（lock/unlock/rename）、`add_item`、`remove_item`（可选同轨 ripple）、`move_item`（改轨或起点）、`trim_item`（入/出点，或 slip 只移源入点）、`split_item`（链接字幕随之拆分归属）、`replace_media`（保持时序，未给新字幕则移除旧链接字幕）、`set_item_props`（volume/fit/opacity/transform/text/style）、`revert_to`（以旧修订内容发布新修订，必须单独成批；不解除当前锁定，也不能改动当前锁定轨道的内容）。修改轨道锁定状态的 `edit_track` 必须单独成批，避免“先解锁再修改”藏在同一批次中。转场、变速、淡入淡出、音乐自动闪避、图形模板属于 P2。

### 检查（P0）

`qa` 针对某一修订的实际渲染文件生成 render-qa：结构（时长/分辨率/音轨与修订一致）、视频（ffmpeg blackdetect/freezedetect）、音频（silencedetect、ebur128 响度与真峰值）、字幕（每条字幕时段内有采样帧）、lint（编译 HTML 的 HyperFrames lint，错误即阻断渲染）。采样合成后的成片帧（每个 item 中点、每个剪辑点前后、每条字幕），生成缩略图墙和剪辑点前后短片供听看。自动 `verdict` 只反映技术检查；`review` 由 Agent 或人工依据采样填写，发现须指向时间/item/采样，critical 须附修复方案。工具成功、源素材帧或自动检查都不能代替对合成画面的评审。

### 阶段与关卡（P1）

阶段：`brief → reference → plan → select → generate → assemble → inspect ⇄ revise → export`，可显式跳过（须给理由）；跳过与完成同样受前序顺序和产物漂移约束，`select/generate` 在绑定计划前不可跳过。关卡由 Python CLI 执行，不依赖提示词：

- 前序未完成或未跳过，后续不能完成；需审批的阶段（默认仅 `plan`，宿主可配置为空以自动执行）在审批前停在 `awaiting_approval`。
- `plan`：产物通过 production-plan 校验。`select`：每个 `footage` 拍都有选定源区间与证据，`tbd` 拍阻断；仅有候选证据的标为 candidate 并在状态中可见。已审批的计划文件不可覆盖，select/generate 阶段的计划修改须另存新文件；与 plan 阶段计划相比，除填写 selection、generation_ref 及 tbd 改为具体来源外的结构变化（增删或重排拍、作用、时长、约束、锁定拍的选片、交付承诺、输出规格）会使该阶段转为待审批并列出差异。`generate`：有 `generate` 拍时须绑定 Job/Receipt，否则不可完成（可改计划并记录决策）。
- `assemble`/`revise`：绑定 EditDocument v2 修订文件 digest。`inspect`：render-qa 必须绑定当前修订 digest；`verdict = fail` 或评审 `revise/reject` 进入 `revise`；`revise` 轮次超过上限（默认 3）进入 `blocked` 交人处理，不强制放行；人工决定继续时用 `video-extend-rounds --by --reason [--rounds 1–3]`，提高 `policy.max_revision_rounds`（上限 20）并写入事件。
- `export`：导出修订必须等于最近一次检查通过（`verdict ≠ fail` 且评审 `accept`）的修订；导出阶段还须绑定实际交付文件及其 `render.kind = export` 的 render-qa（同一修订、`render.sha256` 等于交付文件、`verdict ≠ fail`），预览检查不能代替导出文件检查；可机器检查的交付承诺（时长范围、含字幕、生成镜头占比上限）对该修订实算，不满足则阻断。
- 预算台账先预留后结算；`cap` 模式下预留超过上限即拒绝；结果不明的付费任务不得自动重发。

简单的局部修改（单次裁切、换一句字幕）走执行层的“读取—编辑—检查”快路径，不需要建立 production 状态。

### 分期与验收

- P0 执行底座：EditDocument v2、操作 v2、`add_asset`、v1 迁移、多轨编译、QA 与 lint 关卡、HyperFrames 升级评估。验收：共享样例两侧一致；smoke 覆盖多轨 B-roll、补导入素材、过期修订拒绝、锁定轨道、QA 产物与失败阻断。
- P1 流程与合同：production-plan / video-production 合同与 CLI、关卡、交付承诺实算、样例与评测，`video-production.md` 增加阶段路由。验收：口播删段 + B-roll + 中文字幕样例端到端可追溯，含一次修改轮。
- P2 包装与音频（转场、变速、淡变、闪避、带类型变量的图形模板）：音量包络统一用 HyperFrames `data-automation` volume lane，变速用 `data-playback-rate` 与 `rate` lane（0.8.108 已支持），图形模板参考 Remotion 的类型化 props；输入见[首次复查结论](upstream-absorption.md#首次复查结论2026-10-02)；P3 Seedance 生成适配与预算台账实接；P4 可选本地素材分析 sidecar。

以上为实施合同；各项能力以对应提交、测试与实际渲染证据为准，本节不宣称已完成。

## 真实素材验证（2026-10-02）

首次用客户自有素材（三段竖屏 1080×1920/30 fps：混剪口播、上脸实测、促销机制）跑通 brief → plan → 剪辑 → 预览 → QA → 评审 → 修订。客户素材与产物只保存在本地被 git 忽略的 `dist/`，不进入仓库；转写用本机 whisper.cpp，音频不出本机。

已证明：
- 执行层在真实素材上可完成多段剪辑、crossfade、图形叠层、按段音量归一（成片 −14.1 LUFS、真峰值 −4.7 dBTP，原片约 −7 LUFS 且削波），渲染时间与画面经逐帧核对正确。
- 修订闭环有效：评审修订 1 的合成帧发现 5 项问题（3 major），修订 2 通过修订批次全部修正；合成帧评审抓到了自动检查无法发现的问题。

暴露的缺口（转入 P2.1）：
- 背景音乐垫底的人声混音使静音检测失效，剪辑点只能依赖 ASR 时间戳与能量谷，且需人工听审。
- 烧录字幕比语音晚切换，仅按 ASR 间隙选入点会显示被剪掉那句的字幕；剪辑点需同时满足语音间隙与字幕换行。
- 固定间隔采样漏掉 0.63 s 短镜头（其中有不应出现的人物），需要按镜头采样。
- 模板固定位置会挡住竖屏人脸或与烧录字幕/免责声明冲突，竖屏下副标题字号偏小；QA 看不到画面里已有的文字。
- 8 帧音频 crossfade 会淡掉上一句末字，需在语音结束后开始。
- 来源素材可能自带明星形象、第一人称代言或促销说法；剪辑可回避新段落中的此类内容，但无法移除贯穿全片的角标，必须交人确认授权与有效性。

后续（2026-10-03）：计划由人审批、修订 2 经人观看听审后具名签字，1080×1920 导出与导出 QA 通过（−14.1 LUFS、8 个剪辑点烧录字幕对齐、4 个镜头均有采样），全部阶段完成且无产物漂移。仍未证明：创意质量与投放效果、来源素材中的明星形象与促销有效性授权、宿主（AIOS）接入。

### 第二条真实素材（2026-10-03）

同一客户的 137 秒整片剪出 15.7 秒竖屏短版（技术验证，非发布），全部阶段完成，2 轮修订。新增发现：

- 本地 whisper 对背景音乐垫底的密集口播会把 15–28 s 合成一句；改用词元时间戳按标点切分短语后，相对云端 ASR 句末边界中位偏差 0.09 s、p90 0.66 s，可用于提名剪辑点（个别句首离群 3 s，仍需核对）。
- 烧录字幕剪辑点检查在新素材上发现 2 处 1–2 帧的字幕残留，自动建议可直接采用；但漏掉了“入点后 0.55 s 才切镜头”和“入点落在白色闪场里”两类相邻镜头碎片。
- 入点写成 24.4333 而镜头首帧是 733/30 时，渲染取到上一帧，成片第 0 帧闪旧镜头，自动检查全部通过，只能靠逐帧评审发现；QA 按时间戳抽帧在剪辑点附近也会差一帧。由此确定：入点取帧中点、按帧号核对剪辑点，并新增相邻镜头碎片检查（实施中）。

<a id="image-harness-v1"></a>

## Image Harness v1（2026-10-04，P0/P1 与 Provider Adapter）

目标：让 Agent 与人共同维护一份能继续修改的图片工程，首先覆盖产品海报、封面与营销卡片，随后覆盖场景图局部精修。已有 Image Job、提示词编译、修改/保留约束和 Inspection 合同；可选[图片执行模块](../integrations/image-production/README.md)实现本地对象工程、候选决定、受控蒙版合成、确定性 PNG 及 GPT Image 2.5 Adapter。真实生成与蒙版编辑有合成夹具证据，用户商品的外围背景/多规格保真及显式源码 Skill 的 Pi CLI 编辑行为也已验证；透明抠图、交互编辑器及完整业务宿主仍待验收。参考与固定研究点见[图片上游登记](upstream-absorption.md#image-engineering-references)。

### 工程与职责

- Creative Craft 维护创意路线、编辑意图、参考职责、保留约束与结果评审；Pi 等现有 Agent 调用受控工具。
- 可选图片执行模块维护文档读写、对象操作、渲染、候选合成与导出。AIOS/pi-67 等宿主维护工作区、素材身份、权限、持久任务和预算；凭据与业务素材留宿主。
- Image Job 描述一次生成或编辑请求；本地 `creative-craft.local-image.v1` 保存可编辑状态，尚未成为跨宿主公共 ImageDocument；后续生成输出、合成输出及接受后的工程修订分别记录。图层合成不冒充一次模型生图，也不自动推进正式项目的 approved/delivered 状态。
- 海报采用可寻址的图片、文字、Logo/矢量对象与层级；场景图可以是一张栅格素材加蒙版和局部候选。首期不承诺任意生成图都能拆成可编辑对象。

ImageDocument 的最小字段方向：画布尺寸/工作色彩空间、素材引用及摘要、对象 ID/类型/变换/层级/锁定、字体与模板参数、修订及父摘要、选区与蒙版引用。仅定义当前任务需要的对象与属性；具体 Schema 和迁移在实现时确定。引擎 JSON/SVG/HTML 为适配产物或附带源文件，不把某个编辑库的序列化格式直接变成跨宿主公共合同。第三方工程导入与无损交换需另做能力验证。

### 操作与生成边界

实际入口为 `integrations/image-production/cli.mjs` 的 create/read/edit（含 dry-run）/preview/render，以及 candidate-stage/list/read/compare/accept/discard；撤销作为孤立 `revert_to` 批次。本地候选不调用模型，接受才发布工程修订；陈旧候选需要重读并明确重新暂存。接受/丢弃决定互斥，接受后即使撤销也保留已消费记录。工具只随源码 checkout 使用，不在已发布 Skill 中；Pi 通过现有文件/Bash 工具调用该 CLI，没有新增宿主扩展工具注册或 AIOS 接口。

写操作绑定工程身份、对象 ID 和基础修订。Agent 与人工使用同一操作语义；整批校验后作为一步可撤销修改提交。陈旧版本拒绝写入，重读后重新判断；锁定对象不能由同一批次先解锁再修改。生成任务带基础修订；结果到达先留在候选区，按用户已授权的决策策略接受，不把每次生成都强制变成额外人工审批。

局部编辑区分模型上下文、生成蒙版、保护区域与最终合成蒙版，固定尺寸、坐标及缩放关系。当前本地合成器使用目标栅格坐标、同尺寸单通道 8-bit 灰度 PNG；保护蒙版只允许 0/255，生成/合成蒙版可软边。生成区域必须在上下文矩形内，合成区域必须在生成区域内，保护区域优先保留原 RGBA。以预乘 alpha 合成后完整解码，要求保护区和有效合成区外改变数为 0。当前上下文仅约束本地输入，不证明模型实际看到了哪些像素。Provider 的格式/极性需由其 Adapter 明确转换，不把本地蒙版格式设为通用标准。对象分割只提名选区，alpha matting 另处理细边与透明度；透明瓶身、反射、投影及新背景融合仍需实际检查。

原始商品、文字和 Logo 尽量保留独立素材/对象。保护检查在固定色彩空间的无损工作图上、压缩导出前进行；允许移动或缩放商品时，分别检查素材身份与变换，不按整张画布像素不变验收。保存候选实际字节、模板源、参数和字体；提示词与 seed 不保证模型重生成一致。失败、取消或陈旧候选不得覆盖已接受版本。

### 实施顺序与底座选择

| 顺序 | 可交付能力 | 选择与门槛 |
| --- | --- | --- |
| P0（已实现） | 本地素材 → 可编辑海报 → 有界对象修改 → 预览/检查 → 保存重开 → PNG 导出 | 采用 Satori 0.35.0 → resvg-js 2.6.2 → PNG，Sharp 0.35.5 做素材归正/sRGB 与预览缩放；图片/文字/矩形对象，固定静态中文字体；Fabric.js/Konva 保留交互编辑候选 |
| P1-A/B（本地已实现） | 本地背景候选 → 完整海报对比 → 接受/丢弃 → 蒙版合成 → 撤销/重开 | 候选绑定基础修订与素材；保护原像素，保存上下文及三个蒙版；不调用模型，不推进正式交付状态 |
| P1-C（技术闭环与单商品保真通过，业务验收 PARTIAL） | 真实生成/编辑任务 → 候选 → 工程回入 | 复用 Image Job v2 与 Execution Receipt；读取授权的全局 URL/key，生成/局部编辑与单样例型号对照通过；真实商品外围背景、多规格、像素保护与迁移重开通过；Pi CLI 单会话编辑/撤销/交付复验通过，首轮超时记录保留；抠图/深色透射、费用、正式批准及 Desktop/AIOS 仍缺证据 |
| 条件触发 | 人工交互编辑、分割/精细抠图、本地复杂工作流、批量多规格 | 完整编辑能力对照 OpenPencil/Penpot/Polotno；对象选择对照 SAM 2/3，边缘处理参考 ViTMatte；需要本地节点工作流再评估 ComfyUI。采用具体版本前复核许可与部署方式 |

复用视频侧的资产/实例分离、内容摘要、修订冲突、批次试运行和锁定原则；图片直接复用现有无外部依赖的 `content-store.mjs`，不修改视频 API。依赖仅安装在独立图片模块中；主 Skill、正式工件合同与发布状态保持各自边界。

### 第一轮验收

同一授权产品海报连续完成以下场景，并保留输入、工程修订、真实预览/导出与检查结果：

1. 真实商品素材与背景合成；中文标题、价格、Logo 可独立编辑，字体缺失明确失败或报告替代，不静默漂移。
2. 只改标题和价格，再放大商品并上移标题；检查换行、层级、遮挡与安全区，商品源素材保持。
3. 局部去除背景杂物；保护区域检查与边缘视觉检查同时通过，透明/反射样例单独记录限制。
4. 生成多个背景候选，接受一个并撤销；失败/取消不变更当前工程，陈旧候选不覆盖人工新修改。
5. 人工修改后 Agent 重读接续；陈旧批次拒绝写入，锁定对象保护有效，重开后素材和字体仍可解析。
6. 从 1:1 适配 4:5 与 9:16，再次编辑并导出；分别检查排版和裁切，保存源工程及参数，预览/导出内容一致。

P0 可先用本地背景验证确定性闭环；P1 的生成与局部编辑必须另补真实 Provider 产物和费用证据。结构测试、合成夹具、安装成功与真实业务创意质量分别报告。复用验收样例做引擎/模型升级回归；只有对应实现和证据完成后才升级吸收状态。

### 本轮 P0 证据与限制

2026-10-04，本机 macOS / Node 24：图片模块 15 项行为回归通过，复用内容写入工具的既有回归通过；CLI 创建/读取/试运行/编辑/预览/导出完成真实子进程验收。改标题/价格之外的画布像素保持，显式中文换行与两个独立文本对象的像素一致；并发提交、锁定、撤销保留当前锁、素材/字体/历史篡改、URL/SVG/动画拒绝、文本溢出、取消与超时分别验证。

合成商品海报连续执行 7 个修订，导出 1:1、4:5、9:16；撤销与重开的 PNG 摘要一致，原商品与 Logo 素材摘要保持。实际查看三个规格的 PNG，中文可读、显式换行保持且未见文字裁切/图层遮挡；这只覆盖该夹具。对应本地证据为 `dist/image-p0-2026-10-04-1ccd3d5a/smoke-report.json` 与同目录 `visual-inspection.json`，源码 smoke 可再生成独立产物。

P0 当时未执行首轮条目 3/4；本地 P1 的补充证据见下节。真实商品素材、真实品牌创意质量、Provider 输出/费用、透明与反射边界、宿主 Agent 注册、Linux/Windows 实机均未验证。回执的技术 QA 不升级 `visual_quality`；源码 CI 已加入 Ubuntu 图片任务，尚无本次远端运行结果。

### 本轮本地 P1 证据与限制

2026-10-04，本机 macOS / Node 24：图片模块共 29 项行为回归通过（原 P0 15 项 + 候选/蒙版 14 项）。覆盖只读暂存/对比、接受/丢弃互斥、并发单赢家、锁定、陈旧拒绝/禁止静默变基、候选字节/蒙版/接受摘要篡改、遗留决定锁、撤销后保留消费记录、软边预乘 alpha 与保护透明 RGBA。

`dist/image-p1-2026-10-04-c98d7c25/smoke-report.json` 保存三张本地背景候选、接受/丢弃、人工改价、陈旧拒绝、局部清理、撤销重开共 5 修订。保护区 197,840 像素，实际改变 1,558 像素；保护区与有效合成区外改变均为 0。撤销/重开 PNG 摘要与局部编辑前一致。原 P0 smoke 也重新通过，见 `dist/image-p0-2026-10-04-186d03c8/smoke-report.json`，三个规格的 PNG 摘要与既有记录一致。

另在当前 Codex 会话中读取中文任务、实际调用 CLI、查看三张背景对比后选择暖色，再查看局部清理后接受并撤销重开。任务、输入、实际工具结果、失败结果和视觉检查保存在 `dist/image-agent-2347063a/agent-operation-report.json` 与 `visual-inspection.json`。画面确认中文、¥149、商品/Logo 保持，叶片按预期移除和恢复。这是当前会话的工具可用性 smoke，不是独立 Agent、自动 Skill 路由或 Pi 宿主验收；合成夹具不证明模型生图、真实商品保真、透明/反射边界或创意质量。正式合同桥接和安装版 Skill 更新未执行。

### P1-C Adapter 与真实生成证据

2026-10-04，按用户指定复用全局 Codex active Provider 的 base_url 和 auth.json 的 OPENAI_API_KEY；未修改全局配置或把凭据复制进工程。新增 source-checkout Adapter、两个型号/Surface profile、canonical Image Job v2 编译与 Execution Receipt 桥接。支持单轮 PNG 生成、参考图/蒙版编辑、只读试运行、取消/超时、独占 job_id 和无客户端自动重试；结果先暂存，接受时重新核对任务、回执、源图与基础修订。Profile 仅在可选模块中解析，未进入发布 Skill 或宿主注册表。当前 v2 的 quality/background 字段范围保留，官方 xhigh/max/transparent 尚未开放到此 Adapter。

模型选择依据本轮读取的[官方提示词指南](https://developers.openai.com/api/docs/guides/image-prompting)：Flare 是偏速度的小模型，Sunburst 是偏质量的基础模型；两者均支持生成与精确编辑。先以 Sunburst 建立质量基线，再用相同提示、参考、尺寸及显式 quality 比较 Flare，不推断网关费率或固定速度比例。实际快照未由网关报告，回执保留 null。

本机 macOS / Node 24：47 项图片回归通过（原 29 项 + Provider 18 项），包含模拟 HTTP、蒙版 alpha 极性/保护合成、并发只发一次、失败/取消/超时、陈旧结果、输出格式、显式缩放与离线恢复篡改检查。普通测试和 CI 不调用真实模型；CI 增加 Python 3.11 供 canonical 合同桥接，远端结果尚未验证。

真实调用限定为两个客户端生成 POST，均指定 gpt-image-2.5-sunburst，HTTP 200；未执行真实编辑或 Flare。第一个响应未通过规格检查，当时未保留被拒图片，故该次实际尺寸未知。修复留存后，第二个响应请求 1024×1024、实际返回 1254×1254 PNG；原图和 partial 回执均保留，未直接回入工程。随后显式采用 resize_to_target，以 Lanczos3 做同宽高比的全图离线缩放，零额外请求、不裁切/拉伸，保存原图、适配图、新回执与原回执摘要。尺寸差异是该网关的已观察行为，不推定所有服务均如此。

已查看原图、完整海报对比、接受后的海报和人工 ¥149 版本；背景接受后保持商品/Logo/文字对象，人工改价重开 PNG 一致，撤销恢复接受背景时的 PNG，共 4 修订。证据：`dist/image-p1c-2026-10-04-a06e44ce/live-acceptance-report.json`、`visual-inspection.json` 与 `compare-normalized/comparison.png`。原失败 smoke/partial 回执保持原样；离线恢复成功不重写历史为成功。

此轮只证明真实生成能经尺寸适配进入可编辑工程。合成瓶子与背景的光影融合仍有限制，技术回执不升级 visual_quality；真实商品保真、透明/反射、真实局部编辑、Flare 速度/质量对照、实际账单、上游内部重试、Owner 批准、Pi/AIOS 与 Windows 均未验证。P1-C 真实端到端验收保持 PARTIAL，未提交、推送、发布或安装共享 Skill。

### P1-C 后续：真实蒙版编辑与单样例型号对照

2026-10-04，用户继续授权后，新建独立验收工程，复用已保存背景，不改首轮工程/回执。`provider-acceptance.mjs` 的 prepare 不读凭据、不发请求；run 必须显式 --live，独占 live-started，最多三个客户端 POST，无自动重试，不接入默认测试/CI。实际完成一项 Sunburst 蒙版编辑和两项 Sunburst/Flare 同提示生成，均 HTTP 200。两项生成的编译提示摘要一致，size=1024×1024、quality=medium、opaque PNG，每个型号只有一个样本。

局部编辑移除右下角人工加入的绿色叶片。真实模型提案含全图像素差异（也含 1254→1024 缩放影响），最终经本地保护/合成蒙版约束：保护像素 435,520，实际改变 8,855，保护区与有效合成区外改变均为 0。已查看完整海报和局部放大，叶片去除，但补丁纹理略软；此限制保留，不把像素保护通过当创意质量批准。接受、撤销、恢复和两次重开均通过 PNG 摘要比对，商品/Logo/中文/¥149 对象保持，共 4 修订。

本次生成样本从执行到对比文件完成：Sunburst 26.514 秒，Flare 23.732 秒；请求开始到回执完成分别 24.908/22.176 秒，均包含本地响应处理，不是纯模型推理时长。两个型号返回 1254×1254，按显式同宽高比策略保留原图并缩放。查看完整海报时，两者均给出可排版的暖色摄影背景、没有明显文字裁切，光影/纹理有差异，没有足够依据排稳定质量名次。可在背景探索中试用 Flare，重要精修仍先沿用 Sunburst 基线；后续用真实任务验证。相同 usage 不等于相同费用；网关未报告实际模型快照/底层映射，不能只凭请求别名确认实际路由。

证据：`dist/image-p1c-eval-2026-10-04-70f6629a/acceptance-report.json`、`visual-inspection.json`、`edit-pixel-report.json`、`edit-detail.png` 与 `model-comparison.png`。本轮 npm test 47 项通过，全局配置/auth 字节保持。真实 Provider 的合成夹具技术闭环通过；真实商品/透明反射、稳定型号排名、账单、底层路由、Owner 批准及 Pi/AIOS 仍未验证，业务验收保留 PARTIAL。原 P1-C 首轮证据保留历史状态。

### P1-C 后续：用户真实商品图的受控背景与可编辑海报

2026-10-04，用户选择自己的素材并提供一张 GROLAND 产品图，允许按既定范围修改背景并保留产品/包装内容。输入为 1254×1254 PNG，虽然文件带 alpha 通道，所有像素均不透明；瓶身半透明观感、银色泵头、细流与金色液体池均已烘焙在白底里。原字节另存，工作图只做四周各 13px 的白色 padding 至 1280×1280，没有缩放原商品；提取原图区域后 sRGB RGBA 与输入一致。

先查看保守的素材专属保护多边形，覆盖瓶身、所有标签、泵头、细流及液体池；背景生成/保护/合成蒙版分别保存。一次 Sunburst medium edit 请求只调整外围浅象牙/香槟色背景，HTTP 200；网关仍返回 1254×1254，因此仅对模型提案做显式全图适配，保护合成使用未缩放原工作图。初次海报的顶边衔接稍明显，复用同一提案做离线合成羽化：保留 16px 外围，80px 渐变；原候选/蒙版不覆盖，新候选另存并在查看后接受。没有第二次模型请求。

原保护区域 515,312 像素，最终合成及最终 PNG 的保护像素改变均为 0；有效合成区外改变为 0。已查看完整海报、标签原图/模型提案/保护结果放大图和羽化后的边界。1280×1600 海报将品牌字样、标题「光，沿着瓶身流动。」、300 mL 探索说明保留为独立文字对象，未添加功效或价格。场景仍为一张扁平栅格图，不宣称商品已独立抠出。独立标题修改的框外像素改变为 0，撤销标题、撤销背景、恢复与重开 PNG 全部相同，共 6 修订。

实际采用 Creative Craft 的创作/保留规范及 imagegen 的提示词/检查规范；执行由用户已授权的本仓库 CLI/Adapter 完成。使用本地实验工程及 canonical Job/Execution Receipt，不创建或批准公开 Campaign。完整工程 ZIP 含素材/字体/修订/候选/回执，解压到新目录后 read/render 通过、PNG 摘要与成品一致；运行依赖当前 source-checkout 模块。证据 `dist/image-real-product-2026-10-04-bc9e89f9/acceptance-report.json`、`source-inspection.json`、`visual-inspection.json`、`portability-report.json`、`final/image.png` 与 `groland-editable-project.zip`。

随后在独立副本中完成同一创意的三规格适配，新增模型请求为 0：1:1 为 1280×1280（修订 7），4:5 为 1280×1600（修订 8），9:16 为 1296×2304（修订 9）。方图将两行标题排在商品左侧，竖图采用上方两行标题与下方完整场景；文案只改换行，图片资产及绑定字体均保持。商品场景均以原 1280 方图按 1:1 像素放置，没有裁切或缩放；三个最终 PNG 的 515,312 个保护像素相对原商品图改变均为 0。已实际查看完整成品和缩略对照；这组通用比例没有证明具体平台的界面遮挡适配或品牌批准。

各规格按对应历史修订重开渲染均保持 PNG 摘要一致，4:5 与前轮成品完全一致。修订 10 撤销至原工程、修订 11 恢复竖图均通过，源工程 33 个文件摘要没有改变。三规格工程 ZIP 共 52 条目、35,219,433 字节，包含工程、三个成品及修订索引；解压到新目录后按修订 7/8/9 重渲染全部一致。交付脚本只调用现有 renderProject，不读 Provider 凭据或发起生成。证据 `dist/image-real-formats-2026-10-04-b1440128/format-index.json`、`visual-inspection.json`、`portability-report.json`、`formats-comparison.png` 与 `groland-three-formats-editable.zip`；执行器仍为可选 source-checkout 模块，不据此宣称 Pi/AIOS 宿主已接通。

本例通过的是同姿态/同包装/同光影原像素保留的外围背景流程。保留原像素也保留瓶身内已烘焙的旧白底与反光，不能据此承诺深色背景、透过瓶身的新背景、任意商品独立移动、透明 alpha matte 或重新照明正确。更广泛商品质量、Owner 批准、公开文案、实际账单、底层快照/路由与 Pi/AIOS 仍未验证；完整业务验收维持 PARTIAL。原工程与失败/历史候选证据保留，未提交、推送、发布或安装共享 Skill。

### P1-C 后续：真实 Pi CLI 的自然语言编辑验收

2026-10-04，使用本机真实 upstream Pi CLI 1.0.0，在独立工程副本与临时 agentDir 中显式加载当前源码 Skill。禁用默认扩展/其他 Skill/项目上下文发现和 Session 持久化，沿用 upstream Agent loop 与内置 read/bash/write 工具，没有自建 orchestrator 或安装全局扩展。验收会话显式选择既有 codex/gpt-6.1-sol 视觉模型；其 URL/key 与用户指定的 Codex 全局配置相同，凭据只由临时目录中的外部文件指针读取。用户默认的 deepseek/deepseek-flash 没有改变，图片 Provider 请求为 0。

自然语言任务要求去掉标题末尾句号、保持两行竖版，再排成 1280×1600 的 4:5，最后撤销本轮修改。没有预先提供对象 ID 或编辑 JSON。Pi 的实际工具轨迹证明读取了源码 SKILL.md、image-production.md 和模块 README，自行读取当前修订/对象、编写批次，三次 dry-run 后提交并导出，四次通过图片工具读取实际 PNG。工程修订 11→12→13→14；标题改动为框内 413 像素、框外 0，四份导出的 515,312 个商品保护像素改变均为 0。素材与字体绑定保持，各修订重开一致，最终恢复的对象/画布及 PNG 与初始竖图相同，原工程保持。

首轮为 medium thinking，21 个 Agent turn、25 次工具调用，在三步操作及图片读取完成后、最终回复前达到 360 秒测试时限。保留退出码 143 / TIMEOUT，首轮单会话交付为 PARTIAL，不能改写为完整成功。随后另起同模型 low thinking 的只读收尾会话：5 个 turn、4 次 read，读取独立检查报告与两张实际成品，正常退出并给出 192 字交付说明，没有再次编辑工程。编辑行为/产物检查和只读收尾分别通过，不外推为单会话稳定交付或默认资源发现成功。两个会话前后 Pi auth/models/settings 和 Codex auth/config 五份文件字节均保持。

上述两轮证据 `dist/image-pi-host-2026-10-04-0419ffc7/host-execution.json`、`verification-report.json`、`finish-host-execution.json`、`finish-agent-result.md` 与 `acceptance-report.json`；实际查看改字竖图与 Pi 排版的 4:5 成品。该历史记录保留原状态，后续完整复验不抹去首轮超时。

为了补单会话交付缺口，又在独立副本中以相同 codex/gpt-6.1-sol、low thinking 运行完整自然语言任务，并明确保留 dry-run、实际图片查看与恢复检查，避免重复读取同一份已读结果。测试时限为 600 秒，实际 285.622 秒正常退出；20 个 Agent turn、25 次工具调用，读源码 Skill/图片参考/工具说明，自行生成三项批次，查看四张 PNG，最后给出图片链接与观察到的限制。新的 4:5 保留两行标题、字号 64；商品场景只移至 (0,320)，保持 1280×1280。修订 11→12→13→14，标题框内改变 413 像素、框外 0，四个导出的 515,312 个保护像素改变均为 0；撤销后的对象/画布/PNG 与初始相同，四个修订重开一致，五份全局配置/auth 文件保持。图片 Provider 调用为 0，Pi 文本/视觉推理账单未核验。

完整复验状态为 PASS_COMPLETE_SINGLE_SESSION_CLI_WORKFLOW，证据 `dist/image-pi-complete-2026-10-04-dcece006/acceptance-report.json`、`host-execution.json`、`verification-report.json`、`visual-inspection.json`、`agent-result.md` 与 `four-five/image.png`。这是一个有界完整样例；thinking、提示和测试时限均有变化，不据此推断稳定速度排名或普遍不会超时。当前证明显式源码路径下的真实 Pi CLI 行为，未升级共享 Skill、未加载日常完整扩展集合，也未验收 packaged Desktop、Windows、AIOS 业务接入、账单或品牌批准。后续宿主工作先补实际资源发现与 Desktop 接入，保留 CLI 和 Desktop 的证据边界。

### P1-C 后续：Pi 项目原生发现

2026-10-04，新增项目配置 `.pi/settings.json`，仅声明 `skills: ["../skills/creative-craft"]`。路径由 Pi 从 `.pi/` 解析，项目显式资源优先于同名用户自动发现资源；配置只在本仓库根目录作为 Pi cwd 且项目受信任时生效。未复制 Skill、增加运行时依赖或改变用户默认模型。操作说明见 [Pi adapter](../adapters/pi/README.md#work-from-this-source-checkout)。

真实 Pi CLI 1.0.0 的 RPC `get_commands/get_state` 分别在隔离配置及真实用户配置中完成正/负检查，没有提交模型任务或传入 `--skill`：`--approve` 选中当前源码，`--no-approve` 选中原共享 Skill；真实用户默认仍为 deepseek/deepseek-flash。RPC 子进程在收齐响应后由测试器主动终止，其退出码 143 不是创作会话失败。扩展、项目上下文与主题在探针中禁用，此证据不覆盖完整日常扩展集。

随后仅给自然语言任务和工程副本位置，未提供 Skill 路径、执行器路径或对象 ID。隔离会话以既有 codex/gpt-6.1-sol、low thinking 从项目配置发现源码 Skill，自行读取图片参考/模块说明、确定标题对象、dry-run 后改字、再 dry-run 撤销，三次读取实际 PNG 并正常交付。213.684 秒、18 turn、17 工具调用；修订 11→12→13。独立检查：标题框内改变 413 像素、框外 0；三个导出的 515,312 个商品保护像素改变均为 0；资产/字体、撤销后的对象/画布/PNG 及各修订重开一致，源工程保持。五份全局配置/auth 和共享 Skill 文件树保持，生图调用为 0，文本/视觉推理账单未核验。

状态 PASS_NATIVE_DISCOVERY_AND_BOUNDED_EDIT；证据 `dist/image-pi-discovery-2026-10-04-989bd3ef/discovery-report.json`、`default-discovery-report.json`、`host-execution.json`、`verification-report.json`、`visual-inspection.json` 与 `acceptance-report.json`。运行器元数据曾声明 480 秒，但沿用模板的实际 timer 为 600 秒；两条时限均未达到，差异与修正记录保留在 `runner-limit-note.json`，helper 已对齐实际时限，原执行回执保持。共享 Skill 有 8 个源码差异且当前内容不匹配安装 provenance，未覆盖替换。当时跨项目全局启用仅准备了配置增量；后续执行记录见下节。完整扩展、共享升级和 Desktop/AIOS/Windows 仍需各自验收。

### Pi 全局启用与当前可用范围

2026-10-04，用户明确确认后，仅在 `~/.pi/agent/settings.json` 的 `skills` 数组加入本 checkout 的 canonical Skill 绝对路径，写入前保存原始字节备份并核对已审阅配置摘要。其他配置值与默认 deepseek/deepseek-flash 保持，Pi auth/models、Codex auth/config 和共享 Skill 树保持。真实 Pi 从仓库外临时 cwd、忽略项目资源且不传入 `--skill` 启动，RPC 选中源码 Skill，来源为 local/user/top-level；检查没有提交模型任务。状态 PASS_GLOBAL_ACTIVATION_AND_DISCOVERY，证据 `dist/image-global-activation-2026-10-04-6c060829/activation-receipt.json` 与 `global-discovery-report.json`。此项只启用本机 Pi 的开发源码引用，checkout 路径需继续可用；其他宿主共享安装和发布包没有升级。

当前定位为可用的本地首版，不能标为全部图片场景或完整生产系统已完成：

| 范围 | 已有证据 | 剩余完成条件 |
| --- | --- | --- |
| 可编辑海报工程 | 对象/修订/批次、候选、中文、素材/字体绑定、撤销重开、多规格与真实商品像素检查 | 仍限本地对象合同、Regular 单字体与有限对象类型；无 GUI/第三方工程交换 |
| 生成与受控局部修改 | 真实 Sunburst/Flare 调用、候选接受及保护/合成范围检查；单商品外围背景通过 | 更多真实商品与复杂局部编辑、费用核对、稳定性/型号对照 |
| 核心上游方法 | OpenPencil 对象/共用操作、InvokeAI 候选决定、Krita 蒙版边界已承接到原创实现；Satori/resvg-js/Sharp/Noto 实际采用 | Fabric.js/Konva 交互编辑、ComfyUI 与分割/matting 按实际缺口评估，未集成全部上游产品 |
| Pi 宿主 | 项目发现、自然语言编辑/撤销/交付、全局跨 cwd 和当前启用扩展下的有界图片操作通过，见后续记录 | 扩展工具逐项行为、记忆写入、真实 packaged Desktop/AIOS 与 Windows 各自验收；4 项启动依赖告警保留 |
| 共享 Skill | 后续授权升级当时 90 个内容文件与源码一致、完整旧目录备份、安装版自检及 Codex/Pi 原生发现通过；收尾发现源码新修订，现差一份视频参考，见末节 | 新视频参考未同步；本地未发布候选，图片执行器/依赖/字体仍在源码 checkout，发现检查不代替模型注入或 Desktop 验收 |
| 持续吸收 | 固定 SHA、路径映射、离线/在线检查入口及升级回归样例已登记 | 未部署定时检查或通知；检查发现变化后仍需人工/Agent 复核、采用与验证 |

主要真实画质缺口是半透明瓶身：当前保留原照片像素，也保留内部旧白底与反光。换外围浅色背景通过，深色透射背景、独立抠图和重新照明没有对应证明。自动技术 QA 仍保留 visual_quality=UNVERIFIED；现有画面检查只覆盖具体输出，不能升级成普遍创意质量或品牌批准。当前局部修复、保真及交付首版已验证，后续优先真实商品/复杂编辑覆盖与实际宿主验收，再按缺口引入条件组件。

### 继续打磨：真实全局配置的仓库外编辑

2026-10-04，将原商品工程副本放入仓库外的私有临时目录，以真实 `~/.pi/agent` 配置启动 upstream Pi CLI 1.0.0。忽略项目资源，不传 `--skill`，不在自然语言任务中提供 Skill/执行器路径或对象 ID；沿用全局源码资源发现，扩展/项目上下文/主题在测试中禁用。模型仅本会话选择既有 codex/gpt-6.1-sol、low thinking，默认配置没有改变。Agent 自行定位源码 Skill、图片参考和执行器，合并提交标题下移 40px、说明右移 20px 两项操作，再撤销并交付；两次 dry-run、三次实际 PNG 读取。279.581 秒、18 turn、17 工具调用，正常退出，无工具错误。

独立检查：文字框联合区域内改变 36,323 像素，外部 0；三个输出的 515,312 个商品保护像素改变均为 0；文案、品牌、商品场景/素材/字体及画布保持，撤销对象/PNG 与初始一致。工程与产物搬回验收目录后，各修订重开 PNG 摘要保持，源工程不变；五份 Pi/Codex 配置/auth 和共享树保持。图片 Provider 请求为 0，文本/视觉推理账单未核验。状态 PASS_GLOBAL_CROSS_WORKSPACE_EDIT_UNDO_AND_HANDOFF；证据 `dist/image-pi-cross-workspace-2026-10-04-8021ff3a/acceptance-report.json`、`host-execution.json`、`verification-report.json`、`visual-inspection.json`。此证据补上实际跨 cwd 工具使用，不升级为完整扩展、Desktop 或稳定性能结论。

同轮复核共享安装：前述 8 个差异是同名文件内容差异，此外共享目录还缺 7 个源码文件（视频 Schema、命令模块及模板），没有共享独有内容文件。按安装器实际摘要算法排除生成的 provenance 后，当时内容仍不匹配安装记录。已在上述验收目录准备完整候选安装，90 个内容文件与源码一致，安装器 staging self-test 通过；`shared-upgrade-plan.json` 列出更新/新增文件、源/目标摘要、备份与保护范围。该准备阶段保留原目录，候选不捆绑图片执行器或字体二进制，仍为未发布开发源码；随后授权替换记录见下节，原计划/证据保持。

### 共享 Skill 升级与宿主发现

2026-10-04，用户接受已审阅的共享升级方案后，复核源/目标摘要，再通过现有安装器将 `~/.agents/skills/creative-craft` 原子替换为当前源码候选：8 个同名文件更新、7 个文件补齐，共 90 个内容文件逐文件一致；没有共享独有内容文件被删除。新增文件补齐视频 Schema、命令模块与模板，图片参考同步真实商品的半透明/旧白底边界。完整旧目录保存为 `~/.agents/skills/.creative-craft.backup.20261004T124726419746Z`，旧内容与备份摘要一致。新 provenance 绑定源码 HEAD `3a4a0b5f202d696e92d5768144f7cdd4475f2889`、dirty=true 和 Skill 摘要；这是 0.3.2 未发布开发候选，不表示该 HEAD 已包含所有候选内容。

安装器 staging 自检及安装后的独立 leaf self-test 通过，21 项模板合同检查无错误/警告。五份 Pi/Codex 配置/auth 与两个原商品工程摘要保持，另外 2,046 个其他共享 Skill 文件系统条目的元数据保持。后者是文件系统元数据检查，未称为所有其他 Skill 的内容哈希审查。

实际 Codex CLI 0.160.0 app-server 在真实用户配置下执行原生 `skills/list`、forceReload=true，从本仓库及外部临时 cwd 均发现新共享 Skill，user scope、enabled=true，零资源解析错误；未注入额外 Skill 根目录或启动模型任务。upstream Pi CLI 1.0.0 在仓库外以隔离的空 agent 资源设置自动发现共享 Skill（auto/user/top-level）；另一组真实用户设置检查继续选中已配置的 canonical 开发源码（local/user/top-level），默认 deepseek/deepseek-flash 保持。RPC 子进程收齐响应后主动终止，退出码 143 为受控结束。三组探针共提交零模型任务，五份配置/auth 和新共享树摘要保持；不证明模型提示词注入、完整日常扩展集或 packaged Desktop。

安装与备份状态 PASS_ATOMIC_INSTALL_PARITY_AND_BACKUP，宿主发现状态 PASS_CODEX_SHARED_AND_PI_DISCOVERY；证据 `dist/shared-skill-upgrade-2026-10-04-5bda3972/installation-receipt.json`、`installed-self-test.json`、`host-discovery-report.json` 与 `acceptance-report.json`。已安装的 Skill 不携带图片执行器/依赖/字体，当前图片工程仍依赖现有源码 checkout。此次未改变上游研究固定点或依赖，没有提交、推送或发布；完整扩展/实际 Desktop 与更广商品画质仍按上一状态表分别验收。

### 图片工程质量：已知 RGBA 商品层验收

2026-10-04，后续范围收窄为图片工程。既有 RGBA 素材导入、对象编辑及渲染没有增加新协议或运行时依赖；补充 `integrations/image-production/alpha-smoke.mjs` 与自动回归，覆盖浅/深背景候选、接受、移动/放大、透明度、cover 裁切、contain 留边、撤销、重开和工程迁移。输入是人工构造、透明度已知的测试瓶，含透明边缘、半透明瓶身和不透明标签；alpha=0 的隐藏 RGB 设为醒目的紫色，再用仅隐藏 RGB 不同的候选验证缩放 PNG 完全一致，检查隐藏颜色是否渗出。

15 项验收检查和图片模块 48 项测试通过。不缩放时，浅/深底的每个商品像素均与独立 source-over 公式比较，最大色阶误差为 1；换底后的 4,064 个不透明像素保持、7,432 个半透明像素随背景变化。移动/放大联合框外像素改变为 0；对象透明度及 contain/cover 的内部样点和裁切/留边检查通过，撤销、重开与迁移 PNG 摘要一致。实际查看六图对照，夹具边缘没有可见紫色污染。证据 `dist/image-alpha-2026-10-04-e029b940/acceptance-report.json`、`comparison.png` 和 `visual-inspection.json`；执行入口及限制见[图片模块](../integrations/image-production/README.md#安装与最短验证)。没有调用真实图片 Provider。

此项验证已有透明度的合成，不恢复真实玻璃的光学信息。用户 GROLAND 扁平照片的 alpha 全为 255；其独立商品 matte、白底颜色去污染、透射/反射和重新照明仍待验证。下一图片质量工作聚焦该素材在浅/深背景的边缘、包装文字、形状及光影检查，再决定是否引入条件性分割/matting 组件。下面的扩展及 Desktop 记录保留历史证据，不作为本轮图片工作的前置条件。

### 真实商品 matte 试验与质量边界

2026-10-04，在独立目录 `dist/image-matte-2026-10-04-4224e675/` 对用户白底扁平瓶子进行前景提取/颜色比较。原图字节与既有工程保持；本机 Apple Vision 全实例 mask 作为选区基线，隔离 venv 的 PyMatting 1.1.16 分别验证闭式 alpha 与多尺度前景颜色估计。没有真实图片 Provider 请求，没有修改正式依赖、CLI 或 Schema；[PyMatting 官方示例](https://pymatting.github.io/examples.html)用于区分 alpha 与 foreground extraction，Apple 平台 API 见[前景请求文档](https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest)。

native mask 保住商品主要轮廓，但深底有粗白边和油池内部的白底残留。闭式 alpha 的 8px 外部不确定带改善细油流同时引入颗粒；只改前景颜色不足以修复 native 粗边。收窄不确定带到 1px 后减少颗粒，并改善瓶身边缘；实际查看完整 PNG 及细节，深底仍不通过光学/背景融合检查。原照片的瓶身内部旧白底和反光、油池透明度没有被正确恢复，不能发布通用透明商品换底承诺。

收口为 **浅色预览候选，深底未通过**。候选在新的可编辑工程中作为商品＋油流＋液体池一个整体图片层，标题独立。10 项工程检查通过，六次不缩放导出各 59,159 个包装保护 RGBA 像素改变为 0；不透明核心 291,174 像素 RGB 保持。候选预览/接受保持 PNG 一致，整体层移动/缩放、撤销、重开及复制迁移通过，既有工程完整文件摘要保持。缩放不作原坐标像素一致承诺，新的包装保护范围也不沿用此前扁平照片的 515,312 像素保守保护区。

证据：`acceptance-report.json`、`project-acceptance-report.json`、`visual-inspection.json`、各对照及复现脚本均在上述目录；最终浅色候选为 `project-07-final-light/image.png`，独立工程为 `editable-project/`，质量未通过样例为 `project-06-dark-rejected/image.png`。执行器继续使用既有图片模块，试验 venv/Apple Vision 未成为正式 Adapter。状态 `PARTIAL_REAL_PRODUCT_MATTING_LIGHT_REVIEW_CANDIDATE`，品牌批准及真实光学 matte 未验证；采用登记见[matting 比较](upstream-absorption.md#真实商品-matting-比较2026-10-04)。

### Sunburst 透明候选与商品原像素保护

2026-10-04，在 `dist/image-sunburst-alpha-2026-10-04-3338ec38/` 对同一原图做一次原生透明输出比较。[官方 Image generation 文档](https://developers.openai.com/api/docs/guides/image-generation)确认 Sunburst/Flare 可请求 transparent PNG/WebP；当前 canonical Image Job v2 和可选 Adapter 仍只接受 opaque/auto。因此本次使用未修改的 imagegen Skill CLI，通过用户已授权的全局 URL/auth 发起隔离请求，不伪造 canonical job 或 receipt，也未更改正式 Schema、依赖和共享安装。本地临时转发器以一次外发 POST 为限，实际 1 次、HTTP 200、无客户端重试；config/auth 前后内容一致。网关实际上游 snapshot、内部重试和计费仍未验证。

返回 1254×1254 PNG 与原图同尺寸，全透明像素 1,223,385 个；alpha 存在证明通过，但原始结果的 59,159 个包装保护像素 RGBA 全部改变，不能作为商品保真交付。实看白/浅/深底、泵头、标签、油流和油池，外边缘较上一版本地 matte 干净，商品饱和度和明暗也发生变化。只恢复包装会留下色差，已在独立工程丢弃；由既有 compositor 恢复声明为不透明的 291,174 个核心像素后，保留 `core-protected` 浅底审阅候选。保护区外不承诺原图形状或颜色完全保持。

独立工程 revision 1 继续使用旧浅色素材，模型结果没有自动覆盖当前版本。新候选预览、重开、迁移和 ZIP 解压后的 PNG 摘要一致；不缩放工程导出的核心/包装 RGBA 改变均为 0，独立文案与旧工程完整文件摘要保持。候选状态为 ready，技术通过不等于接受或品牌批准。深底仍有油池白块和内部光学问题；状态 `PARTIAL_SUNBURST_ALPHA_WITH_DETERMINISTIC_PRODUCT_PROTECTION`，不升级为通用透明商品换底能力。

交付为目录内 `groland-sunburst-alpha-review.zip`，含工程、缓存素材/字体、原图、浅/深对照、保护蒙版与专用说明；证据见 `acceptance-report.json`、`execution-report.json`、`pixel-inspection.json`、`project-review-report.json`、`visual-inspection.json`、`delivery-verification.json`。首轮实验输出 RGB 蒙版被既有单通道校验拒绝，修正实验编码后通过，失败样例保留且未放宽执行器规则。后续透明协议的验收需要同时检查实际 alpha、空白/不透明伪结果、对齐、保护区与多底视觉结果；不能仅凭 HTTP 200 或 PNG 文件名自动接受。

### 透明任务协议正式承接

2026-10-04 至 10-05，用户批准上一阶段建议后，canonical Image Job v2 增加 transparent 枚举，并由语义校验要求 provider 明确声明支持以及 PNG/WebP。Sunburst/Flare 可选 Adapter 声明该能力，继续要求单个 PNG；GPT Image 2 原 profile、legacy v1、普通 opaque/auto 行为保留。前述独立 CLI 试验不再是唯一执行入口；本节取代“正式 Adapter 尚不支持”的当时状态。

Provider 在原始返回和显式尺寸适配后检查实际 alpha；最小结构条件是含 alpha、至少一个全透明像素和一个可见像素。全不透明、无通道、全图半透明但没有清空背景、空白透明图均留存原结果和具体 partial 回执。alpha 统计绑定各自图片 SHA，恢复和候选读回重新计算，丢失/伪造统计不得通过。合成后若透明区域消失，则候选失败，已成功生成的产物继续保留；保护像素校验、修订冲突和“不自动接受”规则不变。

真实素材离线回放使用先前原图和 Sunburst 缓存字节，显式各边留白/透明 13px 到 1280，以本机回环服务替代外部 Provider，外部模型请求为 0。新协议完成暂存、技术接受、深底检查、撤销、重开及迁移，浅底 PNG 与先前候选完全一致；291,174 核心及其中 59,159 包装 RGBA 像素改变均为 0。深底油池/内部透射继续未通过；alpha 门禁不是光学或品牌批准。证据 `dist/image-transparent-contract-2026-10-04-92fb3d73/real-product-replay/replay-report.json`；变更合同见 `openspec/changes/archive/2026-10-05-add-image-transparent-output/`，现行规格 `openspec/specs/image-production/spec.md`。

本轮未发起新的真实网关生成，不修改全局配置、共享安装、视频工程，不提交或发布。旧 image v1 Schema 仅按既有紧凑叶节点风格等价排版，解析后的 JSON 完全一致；用以保持已有包体积门禁，没有放宽门禁或删除约束。规格、回归和最终检查记录见同目录 `acceptance-report.json`。

### 正式透明 Adapter 真实网关验收

2026-10-05，使用用户已授权的全局 URL 和 auth.json，通过现有 `executeProvider` 发起一次 Sunburst 编辑 POST，约 45.3 秒返回 HTTP 200。没有新建独立 SDK 执行通道、自动重试或修改全局配置。输入原照片仅各边补 13px 白色到 1280×1280；请求 transparent/high/PNG，返回却为 1254×1254，含 1,160,005 个全透明像素。严格尺寸门禁正确保留原始 PNG、alpha 证据和 `output_dimensions_or_format_mismatch` partial 回执，没有直接暂存候选。实际账单、内部重试及上游模型快照保持 UNVERIFIED。

为检查恢复路径，显式用既有 `recoverProvider` 离线按同宽高比缩放到目标尺寸，未再次调用 Provider。原始 partial 回执保持，normalized receipt 绑定原始 SHA 与 Lanczos3 适配；候选保护合成、读回、预览和复制迁移一致，当前修订仍为 r1。独立像素比较确认 291,174 个核心及其中 59,159 个包装 RGBA 像素改变为 0，顶部独立文案区域保持。恢复栅格尺寸不证明内容位置与原图一致。

实际查看返回图、浅/深底对比及泵头/包装细节，发现模型放大并移动了商品；原图核心与新轮廓叠加，形成双泵头、额外液体线及双层油池，深底另有白底污染。两种背景均 **REJECTED**。主验收工程和搬移副本的候选已标记 discarded，重新读回及拒绝接受检查通过；没有删除产物或覆盖当前画面，三个既有商品工程完整文件摘要保持。

结论为 **技术失败处理与离线恢复通过，真实透明商品画质不通过**。这是一例真实失败路径证据，不是成功透明抠图、全模型稳定性或 Flare 验收。工程 `ready`、alpha 合格、保护区逐像素保持均不得单独升级为视觉批准；后续上游/模型更新须复查整体几何、重复部件、保护边界接缝及浅/深底光学表现。优先验证局部边缘修复或有可靠前景信息的素材，保留该失败样例，不以重复整图生成代替问题定位。

证据与复现脚本在 `dist/image-transparent-live-2026-10-05-f08c2d91/`：`acceptance-report.json`、`execution-report.json`、`recovery-inspection-report.json`、`visual-inspection.json`、`candidate-decision-report.json` 及 `comparison.png`。本轮未修改执行器、Schema、依赖、上游研究固定点或共享安装；文档追加本次证据，没有提交、推送或发布。

### 固定位置的泵头局部边缘验收

2026-10-05，在 `dist/image-edge-local-2026-10-05-c1849a62/` 复用原坐标的本地 PyMatting 素材，限定泵头矩形内距 50% alpha 轮廓 3px 的边缘带，比较局部颜色传播与小范围 alpha 平滑。仅使用既有试验 venv 的 NumPy/SciPy/Pillow，零模型请求，没有生产依赖或执行器改动。首次无约束平滑使局部轮廓最大偏移 4.12px，已拒绝；后续约束每个像素的原始 50% alpha 分类完全保持，没有放宽位移检查。

最终允许区 3,329 像素，修改 3,070 个 RGBA 像素；50% alpha 轮廓改变为 0，区域外改变为 0。291,174 个核心和其中 59,159 个包装像素保持原图 RGBA。实际查看白/浅/深底及放大细节，泵头颗粒略减，整体缩略图差异很小；光学透射及油池没有处理，深底仍不通过。`edge-smooth` 是浅底局部审阅候选，`color-only` 作为未选中方案标记 discarded；没有把该结果称为全面画质提升。

既有 masked candidate 使用局部 context 承接；主验收工程保持 r1、候选待审阅，独立技术副本完成接受和撤销。14 项工程检查通过，导出改变 2,820 个像素且允许区外为 0，搬移重开候选 PNG 一致，四个既有商品工程保持。首次工程 verifier 错将灰度 mask 按默认 RGB raw 读取；修为显式单通道并补长度断言后重跑通过，生产合成器原本已正确读取，未改运行时或放宽零变化门禁。两次首次失败均保留记录。

复现与证据为 `edge-report.json`、`project-report.json`、`visual-inspection.json`、`acceptance-report.json` 和 `pump-comparison.png`；交付包含可编辑工程和待审阅候选。该验收证明固定位置的有限边缘维护可以走确定性工具与受控候选流程，不能从单张白底照片推导真实玻璃光学，也不证明其他商品参数适用。

### 候选导出的状态上下文

2026-10-05，在已拒绝的真实 Sunburst 工程复现：单独渲染候选时，回执只有候选 ID/摘要，虽然正确保留 visual_quality=UNVERIFIED，却没有说明候选已丢弃。现有 render 在输出前复用 candidate-read 的决定核验，将检查时间、候选状态、当时当前修订、接受修订、当前是否应用、stale 与 pending 附在 candidate_preview 中。画面仍按不可变基础修订生成；不改变接受/丢弃/锁机制，不赋予自动视觉批准，也不禁止查看正常的已丢弃候选。决定记录损坏则无法出具有效状态回执，导出失败并清理本次图片。

新增回归先在原实现失败，修复后覆盖 ready/stale/discarded/decision_pending、已接受及撤销后仍保留的接受历史；图片模块 72 项测试通过。三个真实工程分别验证待审阅、已丢弃和已接受后撤销，候选 PNG 与原有证据逐字节一致，普通当前画面也保持；源工程完整文件摘要不变，模型请求为 0。记录为 `dist/image-candidate-context-2026-10-05-52d098c1/acceptance-report.json`、`reproduction-before.json`、`real-project-report.json` 和测试日志。只更新新的导出回执，旧包与旧回执保留历史快照；状态是 checked_at 时的观察，决定前须重新检查当前工程。

### 当前启用扩展的图片操作与 Desktop 阻塞

2026-10-04，使用真实全局 Pi 配置、仓库外的商品工程副本，移除前轮的 `--no-extensions`、`--no-context-files`、`--no-prompt-templates` 和 `--no-themes`。保留配置中原本禁用的资源，不安装或修改扩展；仅本进程将 OpenViking privacy 设为 read-only，避免验收写入长期记忆。零模型请求的原生 RPC 选中 canonical 源码 Skill，并登记 28 个扩展命令；这证明实际注册及发现，不证明每个扩展 Tool 的业务行为。

首轮 Agent 完成标题下移 40px、说明右移 20px 的单批次修改、撤销、三次实际 PNG 查看与交付，260.067 秒、20 turn、19 工具调用。独立像素/撤销/重开检查通过，但五份配置/auth 中 Codex config.toml 的摘要在运行期间改变（mtime 为 13:11:21 UTC），整体保护门禁未通过。已执行工具轨迹中未找到该文件写入，定向扩展源码搜索也未定位写入者；未保留当时的配置原始字节，来源仍为 UNVERIFIED，未自动回滚现有配置。四行启动依赖告警在原 runner 中归入 errors，原回执与严格验收失败记录保持。首轮证据 `dist/image-pi-daily-2026-10-04-f4c86e31/host-execution.json`、`strict-verifier-result.json`、`verification-report.json` 与 `config-drift-note.json`；续跑检查未降低失败门禁，状态保持 PARTIAL。

为核验未通过的配置保护项，另做一次有界复验，不并行操作 Desktop，保存前后摘要，并将已知启动 Warning 与实际错误分开记录。Agent 同样只从自然语言任务自行定位源码 Skill/执行器，沿用 codex/gpt-6.1-sol、low thinking 的单次调用覆盖默认值，未改用户默认模型。233.986 秒、18 turn、17 工具调用，正常结束；两次 dry-run、修订 11→12→13、三次实际图片读取。独立检查：文字框联合区域内变化 36,323 像素，区域外 0；三个输出各 515,312 个商品保护像素改变均为 0；文案/画布/素材/字体及完整场景保持，撤销后的对象/PNG 与初始相同，搬移重开一致，源工程保持。五份配置/auth 及共享 Skill 摘要均保持；没有运行/工具错误，图片 Provider 请求为 0，文本/视觉推理账单未核验。复验 PNG 与首轮实际查看的三图逐文件一致，视觉检查复用并绑定摘要。

该有界工作流状态 PASS_BOUNDED_PI_IMAGE_WORKFLOW_WITH_STARTUP_WARNINGS；证据 `dist/image-pi-daily-2026-10-04-e32f1850/acceptance-report.json`、`host-execution.json`、`verification-report.json`、`visual-inspection.json`、`guard-before.json` 和 `guard-after.json`。通过的复验不抹去首轮未归因漂移，也不证明稳定性能或完整扩展业务。启动仍有四项 host dependency 声明告警：pi-subagents 0.38.0、pi-web-access 0.17.0、pi-smart-fetch 0.3.12、rpiv-advisor 2.0.0 将部分宿主库列入 dependencies 而非所要求的 peerDependencies。清单见首轮 `startup-warning-inventory.json`；未修改全局包，未核查这些包的最新上游版本，当前样例未观察到由告警导致的任务失败。

实际运行的 macOS arm64 New Money 打包应用为 0.1.0-alpha.43，Computer Use 已观察窗口和界面，并读取原生 File 菜单；未打开用户既有对话、提交模型任务或完成新工作区绑定。随后输入/截图通道报 noWindowsAvailable，再报 Sky Computer Use native pipe startup failed；隔离 REPL 重置后按精确 bundle ID 重连仍失败。阻塞在自动化传输，不能据此认定应用或图片执行器故障，也不能把 CLI 结果升级成 Desktop 验收。状态 BLOCKED_AUTOMATION_TRANSPORT，证据首轮 `desktop-attempt.json`、`desktop-route.json`；已留存 `desktop-workspace/project` 和 `desktop-task.md` 供通道恢复后接续，未保存含用户其他工作内容的整窗截图。UI 核验使用 design-craft、L1-F/normal、既有 PRODUCT/DESIGN、主代理串行及 Computer Use，没有浏览器替代或子代理。Desktop/AIOS/Windows 与复杂商品画质仍未验收；本轮没有源码执行器/依赖/上游固定点变化，没有提交、推送或发布。

收尾现场另观察到仓库在验收期间从 main / `3a4a0b5f202d696e92d5768144f7cdd4475f2889` 变为 feat/cut-tools / `80f0c94eed410ea1c63a86c61b41e8d22eb1e6e0`。本验收未执行 Git 写操作，保留该并行变化；当前共享安装与源码相差 `references/video-production.md` 一份，未覆盖替换。图片 entrypoint/reference 的摘要仍与实际会话读取版本一致；此前安装通过是当时版本的结果，不表示新 HEAD 的完整安装一致性。证据复验目录 `source-drift-closeout.json`。后续先核对新修订的相关作用范围，再同步安装或发布；本轮图片行为结果与新的源码同步状态分别保留。
