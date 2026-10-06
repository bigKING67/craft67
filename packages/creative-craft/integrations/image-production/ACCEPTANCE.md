# Local image production — 验收记录

本文件保存图片模块带日期的本机/真实请求验收叙述，从 README 迁出以便 README 只保留用法与合同。引用的 `dist/` 路径为当时本机证据目录（gitignore，不随仓库提供）；路径相对本目录。数值与结论只代表记录当日的代码与环境，后续行为以测试与 [现行规格](../../openspec/specs/image-production/spec.md) 为准。

## 透明与 matte 验收

2026-10-04 本机验收 15 项检查通过，图片模块共 48 项测试通过。已知 matte 中不透明的 4,064 个商品像素换底后不变，半透明的 7,432 个像素随底色变化；浅/深底与预期合成值的最大误差均为 1 个色阶，移动/放大联合框外变化为 0，隐藏 RGB 变化后的缩放 PNG 摘要一致。证据见 `../../dist/image-alpha-2026-10-04-e029b940/acceptance-report.json`。夹具是人工构造的透明测试瓶，验证已有合成工程；真实玻璃的透射、折射、反射、白边去污染及从扁平照片恢复 matte 均不在此证明内。

真实商品的后续 matte 比较位于 `../../dist/image-matte-2026-10-04-4224e675/`：本机 Vision 选区 + 隔离 PyMatting 的 alpha/前景颜色对照，最终为浅色候选、深底未通过。新工程的包装保护 59,159 像素在六次不缩放导出中改变为 0，整体场景层移动/缩放、撤销、重开及迁移通过，原工程保持。核心执行器及依赖未变，试验不作为通用自动抠图入口；具体对照、输入假设和复现脚本见目录 `README.md`，机制与未通过原因见[架构](../../docs/content-production-architecture.md#真实商品-matte-试验与质量边界)。

该试验的可编辑交付包为 `../../dist/image-matte-2026-10-04-4224e675/groland-matte-preview-project-v2.zip`：含工程、原图、浅/深对照、包装保护区、检查记录、字体许可和专用使用说明。解压后 19 个清单文件与 7 个说明链接核验通过，使用既有图片模块重渲染的 PNG 与已查看的浅色候选摘要相同；编辑/导出无需 Vision/PyMatting 环境。证据为同目录 `delivery-v2-verification.json`，深色背景仍未通过。

Sunburst 原生透明输出的后续独立验证位于 `../../dist/image-sunburst-alpha-2026-10-04-3338ec38/`。一次真实 API 请求得到含 alpha 的 1254×1254 PNG，外边缘更干净，但模型也改变商品原色；只恢复包装会留下色差。既有 masked compositor 恢复 291,174 个原图核心 RGBA 像素（包含 59,159 个包装像素）后，留作浅底待审阅候选，深底油池仍未通过。独立工程当前版本保持旧浅底，`core-protected` ready、`packaging-protected` discarded；重开/迁移及解压后预览一致。交付包 `groland-sunburst-alpha-review.zip` 含缓存素材、字体、候选和说明，技术/画质分层记录在 `acceptance-report.json` 与 `delivery-verification.json`。当时 v2/Adapter 尚不接受 transparent，试验使用未修改的 imagegen CLI，没有绕过 canonical job 校验；后续正式支持见下文 GPT Image 2.5 Adapter；详见[透明候选验收](../../docs/content-production-architecture.md#sunburst-透明候选与商品原像素保护)。

2026-10-05 的局部边缘验收沿用本地 PyMatting 素材，仅处理泵头的资产专用 3px 边缘带，不调用模型。最终修改 3,070 个 RGBA 像素，50% alpha 轮廓完全一致，带外、291,174 核心及其中 59,159 包装像素均保持；既有 masked candidate 接口的局部 context、接受/撤销和迁移检查通过。放大对照仅见颗粒小幅减轻，选中版保持 ready 待审阅，深底油池仍不通过。参数不是通用商品标准，处理脚本未成为正式依赖。证据 `../../dist/image-edge-local-2026-10-05-c1849a62/acceptance-report.json`、`pump-comparison.png`；[范围与失败记录](../../docs/content-production-architecture.md#固定位置的泵头局部边缘验收)。

## Provider 真实请求

正式透明路径于 2026-10-04 通过离线回归与真实商品缓存回放；回放明确用 13px 留边将原始 1254 图适配到 1280，没有缩放或新增模型请求。保护区、暂存/接受/撤销/重开/迁移均通过，浅底 PNG 与先前已检查版本一致；深底油池仍未通过视觉检查。证据 `../../dist/image-transparent-contract-2026-10-04-92fb3d73/real-product-replay/replay-report.json`。

2026-10-05，正式 Adapter 对用户全局网关完成一次 Sunburst 透明编辑请求：HTTP 200、有实际 alpha，但请求 1280×1280、返回 1254×1254，严格尺寸检查保留 partial 回执。显式离线恢复和保护合成、候选读回/迁移通过，没有再次请求模型。实际查看发现生成图改变了商品比例/位置，合成后出现双泵头和双层油池；浅/深底均被拒绝，候选已标记 discarded，当前修订保持。291,174 个核心 RGBA 像素（含 59,159 个包装像素）不变仍不足以保证整体商品保真。`ready` 只代表技术上可供审阅；尺寸恢复只处理同宽高比的栅格尺寸，不能修复内容位置。透明提取需检查轮廓、保护边界接缝、重复部件及透射/反射后再接受。证据 `../../dist/image-transparent-live-2026-10-05-f08c2d91/acceptance-report.json`、`comparison.png`；共享安装、发布及 Flare 实测仍未由本轮覆盖。

## 真实工作流、宿主与收尾核查

本地证据（2026-10-04，macOS / Node 24）：47 项行为回归通过（原 P0/候选 29 项 + Provider 18 项）。前轮 P0 多规格与本地候选 smoke 均通过，保护区/有效合成区外改变均为 0，撤销/重开 PNG 字节一致；中文任务记录见 `../../dist/image-agent-2347063a/agent-operation-report.json`。

首轮两个真实 Sunburst 生成 POST 均 HTTP 200，第二次请求 1024×1024 返回 1254×1254；严格拒绝后零请求离线适配，保留原图/partial 回执，候选接受、人工改价、撤销重开通过。记录为 `../../dist/image-p1c-2026-10-04-a06e44ce/live-acceptance-report.json` 与 `visual-inspection.json`。

后续三次请求均 HTTP 200：Sunburst 局部去叶片的保护区/有效合成区外改变为 0，实际改变 8,855 像素，接受/撤销/恢复/重开 PNG 一致；已查看全图/局部，补丁纹理稍软。相同提示/1024×1024/medium 的生成各一张，从执行到比较完成 Sunburst 26.514 秒、Flare 23.732 秒；单样例不证明稳定排名。三次均返回 1254×1254，显式适配并保留原图。记录位于 `../../dist/image-p1c-eval-2026-10-04-70f6629a/acceptance-report.json` 与 `visual-inspection.json`；全局配置/auth 保持。商品仍为合成夹具，费用、实际底层路由、真实商品/透明反射、独立 Agent/Pi 宿主与批准均未验证，业务验收保持 PARTIAL。完整范围见[架构记录](../../docs/content-production-architecture.md#image-harness-v1)。

用户随后提供真实 GROLAND 产品图：1254 方图的 alpha 全为 255，四周加 13px 白边后原像素保持。一项真实编辑加离线边界羽化，保护 515,312 像素在最终 PNG 中改变为 0；独立标题编辑的框外改变为 0，标题/背景撤销、恢复、重开与完整工程 ZIP 解压重渲染通过，共 6 修订。证据 `../../dist/image-real-product-2026-10-04-bc9e89f9/acceptance-report.json`、`visual-inspection.json`、`portability-report.json`；成品为 `final/image.png`，完整工程为 `groland-editable-project.zip`。

同一工程的独立副本已导出 1:1（1280×1280，修订 7）、4:5（1280×1600，修订 8）和 9:16（1296×2304，修订 9）。文案仅改换行，场景不缩放/裁切，三张成品的 515,312 个保护像素相对原素材改变均为 0；资产/字体保持。各修订重开、撤销至原 4:5、恢复竖图及 ZIP 解压后的三个渲染全部保持 PNG 摘要一致，原工程没有改变，新增模型请求为 0。实际成品与对照已查看，具体平台界面遮挡和品牌批准未验收。证据 `../../dist/image-real-formats-2026-10-04-b1440128/format-index.json`、`visual-inspection.json`、`portability-report.json`；`groland-three-formats-editable.zip` 内的 render-formats.mjs 可传入现有模块路径和新输出目录，按对应修订重渲染，不调用 Provider。

真实 upstream Pi CLI 1.0.0 已在隔离会话中显式加载源码 Skill，以自然语言驱动本模块完成标题去句号、4:5 重排和撤销。Agent 实际读取 Skill/图片参考/本 README，自行编写批次，三次 dry-run 后提交，四次读取 PNG；工程 11→12→13→14。独立检查：标题框内改变 413 像素、框外 0，四个导出的 515,312 个商品保护像素改变均为 0；素材/字体、撤销和重开保持。首轮 medium thinking 在最终回复前达到 360 秒时限，单会话交付为 PARTIAL；另一 low thinking 只读会话检查报告和两张实图后正常收尾。两个会话的五份 Pi/Codex auth/config 文件均保持，图片 Provider 请求为 0。记录 `../../dist/image-pi-host-2026-10-04-0419ffc7/host-execution.json`、`verification-report.json`、`finish-host-execution.json`、`finish-agent-result.md` 与 `acceptance-report.json`。此例证明显式源码路径下的 Pi CLI 操作；共享安装、默认发现、完整扩展集合及 packaged Desktop/Windows 尚未验收。

后续同模型 low thinking 的独立完整复验正常退出并给出最终交付，285.622 秒（600 秒测试时限）、20 turn、25 工具调用，单会话样例为 PASS。三次 dry-run、四次实际图片读取及独立像素/撤销/重开检查通过，五份全局配置/auth 保持；生图调用仍为 0，Pi 文本/视觉推理费用未核验。新版 4:5 采用两行 64px 标题，完整场景不缩放/裁切。记录 `../../dist/image-pi-complete-2026-10-04-dcece006/acceptance-report.json`、`host-execution.json`、`verification-report.json`、`visual-inspection.json` 与 `agent-result.md`。首轮失败证据保留；单次复验且提示/thinking/时限有变化，不证明稳定性能或普遍无超时。默认发现、共享安装和 Desktop 的边界仍待验证。

项目原生发现已另补实测：仓库根目录的 `.pi/settings.json` 使 Pi 在信任项目后选中源码 Skill，无需 `--skill`；真实用户配置的 RPC 检查保持原默认模型，忽略项目资源时仍选原共享 Skill。自然语言验收仅提供工程位置，Agent 自行定位 Skill 和本模块，改标题后撤销，213.684 秒正常交付（18 turn、17 工具调用、两次 dry-run、三次实际 PNG 读取）。三个成品商品保护像素改变为 0，标题框外改变为 0，撤销与重开一致，五份全局配置/auth 及共享文件树保持。证据 `../../dist/image-pi-discovery-2026-10-04-989bd3ef/acceptance-report.json`、`discovery-report.json`、`default-discovery-report.json`；用法见 [Pi adapter](../../adapters/pi/README.md#work-from-this-source-checkout)。配置仅影响本仓库根目录，未新增扩展工具或升级共享安装；跨项目启用、完整扩展集与 Desktop 仍待验证。执行器在源码中，已发布 Skill 包不携带它。

随后按用户明确授权将 canonical 源码 Skill 路径加入全局 Pi 的 skills，保留其他设置/凭据/共享目录并备份原配置；仓库外的真实 Pi RPC 选中该用户资源，未提交模型任务。全局发现通过，证据 `../../dist/image-global-activation-2026-10-04-6c060829/activation-receipt.json`。这启用本机 Pi 的开发源码，仍依赖现有 checkout/模块/字体；不会升级其他宿主共享安装或把执行器加入发布包。完整扩展及 Desktop/Windows 仍待验证，当前首版能力与真实画质缺口见[架构状态](../../docs/content-production-architecture.md#pi-全局启用与当前可用范围)。

真实全局配置的仓库外编辑也已验证：工程副本放到外部工作目录，忽略项目资源，任务不提供 Skill/执行器路径或对象 ID。Pi 自行定位本模块，将标题下移 40px、说明右移 20px 合为一个批次，再撤销并查看三张 PNG，279.581 秒正常交付。文字框外及三个输出的商品保护像素改变均为 0，文案/画布/素材/字体保持，搬回验收目录后各修订重开一致；全局配置/auth、共享树与源工程保持。证据 `../../dist/image-pi-cross-workspace-2026-10-04-8021ff3a/acceptance-report.json`。本轮图片 Provider 调用为 0，扩展/上下文/主题在验收中禁用，不代替完整日常扩展集或 Desktop。

共享 Skill 随后按独立授权完成升级：8 个内容文件更新、7 个文件补齐，90 个内容文件与源码一致，完整旧目录备份、provenance 和安装版自检通过。Codex 真实用户配置的仓库内外原生发现、Pi 隔离设置的共享自动发现及真实用户设置的全局源码选择均通过；三组探针零模型任务，配置/auth 保持。证据 `../../dist/shared-skill-upgrade-2026-10-04-5bda3972/acceptance-report.json`。此项同步本机方法/合同安装，当前仍为未发布候选；本执行器、依赖和字体二进制仍不在共享 Skill 内，模型注入、完整扩展和 Desktop 另验。最新分层范围见[架构记录](../../docs/content-production-architecture.md#共享-skill-升级与宿主发现)。

当前启用扩展配置下的有界图片操作也已验证：移除前轮资源-disable flags，保留配置中原本禁用的资源，仅本进程记忆 read-only。自然语言任务不提供 Skill/工具路径；复验正常交付（233.986 秒、18 turn、17 工具调用），两次 dry-run、三张实际 PNG 读取及独立像素/撤销/重开检查通过，五份配置/auth 和共享安装保持。首轮因未归因的 Codex config 摘要漂移保持 PARTIAL；四项扩展包启动依赖告警保留，未修改全局包。证据 `../../dist/image-pi-daily-2026-10-04-e32f1850/acceptance-report.json`，首轮 `../../dist/image-pi-daily-2026-10-04-f4c86e31/config-drift-note.json`。图片 Provider 请求为 0；扩展 Tool 逐项、记忆写入与完整 Desktop/AIOS/Windows 未验收。实际 macOS 打包窗口已观察，GUI 图片任务因 Computer Use native pipe 不可用而未执行；准备工程/任务和阻塞记录保留，见[宿主记录](../../docs/content-production-architecture.md#当前启用扩展的图片操作与-desktop-阻塞)。

此例是受控修改扁平照片外围背景，标题/品牌字样/说明独立排版。没有独立商品抠图；保留半透明瓶身原像素也保留已烘焙的旧白底/反光。深色背景、透过瓶身的新背景、重打光、任意商品独立移动要另验收 alpha matte/合成。已有透明底产品素材可以作为普通独立图片对象导入，但不能把本例当抠图能力证明。正式品牌批准、费用及完整业务宿主仍待验证。

当前源码完成一次有界集中核查，修复撤销绕过锁定层级、合法弃用说明写后不可读，以及 Provider 成功被误当作候选就绪三处缺陷。先保留失败回归，再验证修复：6 项定向测试、78 项图片完整测试通过，两组只读独立复核确认修复。弃用说明仍允许最多 500 个 UTF-16 单元；读取上限覆盖最坏 JSON 转义后的 3,218 字节记录，仍保留有界读取与摘要核验。

证据见 `../../dist/image-closeout-2026-10-05-901be134/acceptance-report.json`。上游增量核查与采用/暂缓理由见[本次吸收记录](../../docs/upstream-absorption.md#图片模块收尾与上游增量核查2026-10-05)。本次没有真实模型请求、依赖升级或共享安装变更。工程核心可以继续用于已验证的本地工作流；透明玻璃/液体在深底上的光学效果、通用抠图质量、正式品牌批准、其他宿主及发布仍需各自的证据。

商品成品对照随后用同一 GROLAND 素材完成：新增独立的白底保真审阅工程，原图 1,572,516 个 sRGB RGBA 像素保持，仅在照片外延展背景并沿用已有文字。实际看图后建议以该版作为保真基线；米色方案及泵头候选保留原状态，透明光学问题不因边缘微调而视为解决。三版整体图与泵头/包装/液体池细节、可编辑工程及限制见 `../../dist/image-groland-review-2026-10-05-6e73f042/README.md`。这是单张商品审阅，未新增生图、运行时依赖或正式品牌批准。

该白底方案已另做可搬迁交接：`../../dist/image-groland-handoff-2026-10-05-a34c7d90/groland-white-review.zip` 包含完整工程、导出、对照、示例和字体许可。仓库外中文/空格路径解压后，真实 CLI 的 11 项检查通过：重开/重渲染一致、标题局部修改、商品像素保持、dry-run、陈旧版本/锁定拒绝及撤销恢复。报告见同目录 `README.md` 与 `acceptance-report.json`。测试仅改解压副本；原工程、模型调用数和执行器依赖保持，压缩包仍需现有源码执行器，不等于独立编辑器或公开投放批准。
