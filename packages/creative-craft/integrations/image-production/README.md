# Local image production — P0 + P1 candidates and Provider Adapter

可选的图片执行模块：本地商品/背景/Logo → 可编辑对象工程 → 有界批次编辑 → 中文排版 → PNG 预览/导出 → 保存重开与撤销。Agent 与人工调用同一套操作。模块只随源码 checkout 使用，不进入根 npm/Skill 包；目录独立维护图片文档、素材导入、排版与渲染，复用视频模块无外部依赖的 `content-store.mjs`，不加载视频执行器。

当前为本地实验合同 `creative-craft.local-image.v1`，不替代正式 Image Job / Receipt / Inspection。渲染回执属于本模块，不能直接用于正式项目的 approved/delivered 状态。P0 提供可编辑海报；P1 提供候选暂存/对比/接受/丢弃、受控蒙版合成及可选 GPT Image 2.5 Adapter。真实网络结果与验收限制见架构记录；没有 GUI 或分割器。

**从已有商品照片开始：** [可复用照片工程入口](PHOTO-WORKFLOW.md)使用 `create-photo`，只填照片路径、工程 ID 和标题即可创建。整张不透明照片按原尺寸保留并锁定，文字独立编辑，创建前可用 `--dry-run` 检查尺寸与排版；后续共用现有编辑、撤销和渲染命令。

**一次改文案，同步多个版式：** `copy-variants <project> <input.json>` 将共享文字更新应用到绑定的历史版式，输出各自可编辑的派生工程和成品。原工程保持不变，任一版式失败则清理本批输出；输入和边界见[照片工作流](PHOTO-WORKFLOW.md#一次改文案同步多个版式)。

**复用用途版式：** `create-photo` 可选 `template: "brand-detail"` 或 `"xiaohongshu-cover"`，用新照片、品牌和标题创建详情首屏／封面工程。照片按真实尺寸居中、不缩放，超出区域则拒绝；示例与画布约束见[用途模板](PHOTO-WORKFLOW.md#可复用用途模板)。

**明确授权后裁边：** `crop-photo <new-output> <input.json> [--dry-run]` 绑定原文件摘要与显式矩形，保存原图、规范化图、裁切图和回执。裁切图可交给现有模板；不自动识别白边，交付需携带裁切目录，见[受控裁边](PHOTO-WORKFLOW.md#经授权裁边后再排版)。

## 安装与最短验证

Node.js >=22；无需 Chrome、FFmpeg 或 GPU。依赖固定为 Satori 0.35.0、`@resvg/resvg-js` 2.6.2、Sharp 0.35.5，依赖闭包和原生平台包由 package-lock.json 固定。

Provider 功能另需 Python >=3.11（版本过低时明确报错；可用环境变量 `CREATIVE_CRAFT_PYTHON` 指定解释器绝对路径，默认按 PATH 查找 `python3`），使用标准库 tomllib 读取配置，复用 canonical 合同校验/提示词编译；本地对象编辑和渲染无需 Python。Provider profiles 在模块 `providers/` 中，只供 source-checkout 的 ImageContext 使用，未增加到安装版 Skill 或根注册表。

```sh
cd integrations/image-production
npm ci --ignore-scripts --no-audit --no-fund
npm run fetch-font
npm test
npm run smoke
npm run smoke:candidates
npm run smoke:alpha
```

字体首次下载需要网络。`fonts/manifest.json` 固定官方提交、文件、字节数与 SHA-256；下载或现有文件不匹配即失败，不覆盖异常文件。采用静态 Noto Sans CJK SC Regular（400）；已有视频模块的可变字体在 Satori 中实际解析失败，因此图片模块使用独立字体。字体二进制不入库，OFL 文本保留在 `fonts/OFL.txt`。

`smoke` 在 `dist/image-p0-<date>-<id>/` 新建一份合成测试工程，打印路径。它保留 create/edit JSON、7 份工程修订、PNG/SVG、预览和回执，覆盖改中文/价格、商品缩放、标题上移、撤销、重开、4:5 与 9:16 重排。测试素材不是实际商品或模型生成结果，无法据此证明真实品牌创意质量。输出目录须新建，不覆盖旧验收。

`smoke:candidates` 在独立 `dist/image-p1-<date>-<id>/` 验证三背景候选、整张海报对比、接受/丢弃、人工改价后的旧候选拒绝、局部去除背景装饰、保护区检查、撤销及重开。它是确定性脚本，不证明自然语言 Agent 能力。

`smoke:alpha` 在独立 `dist/image-alpha-<date>-<id>/` 验证已知 RGBA 商品层：浅/深背景候选、接受、移动/放大、对象透明度、cover 裁切、contain 留边、撤销、重开及迁移。原始尺寸逐像素与独立 source-over 公式比较；缩放时仅改变 alpha=0 像素的隐藏 RGB，要求整张 PNG 不变，以检测隐藏颜色渗入。保留输入批次、工程、各次 PNG/SVG/回执、`acceptance-report.json` 与六图 `comparison.png`（上排浅底、深底、放大；下排半透明裁切、完整 contain、撤销）。此验收也由 `npm test` 执行。

带日期的验收记录（真实商品 matte、Sunburst 透明候选、局部边缘、交付包等）已移至 [ACCEPTANCE.md](ACCEPTANCE.md)。其中 `dist/` 路径是本机证据目录，已被 gitignore，不随仓库提供，也不是运行前提。

## Agent 工具入口

```sh
node cli.mjs create-photo /absolute/new-project /absolute/photo-brief.json --dry-run
node cli.mjs create-photo /absolute/new-project /absolute/photo-brief.json
node cli.mjs create /absolute/new-project /absolute/create.json
node cli.mjs read /absolute/project
node cli.mjs read /absolute/project 2
node cli.mjs edit /absolute/project /absolute/edit.json --dry-run
node cli.mjs edit /absolute/project /absolute/edit.json
node cli.mjs preview /absolute/project /absolute/new-preview
node cli.mjs render /absolute/project /absolute/new-export
node cli.mjs render /absolute/project /absolute/new-history-export --revision 2
node cli.mjs preview /absolute/project /absolute/new-history-preview --revision 2
```

`read` 返回当前/指定修订、完整文档及摘要。CLI 成功在 stdout 输出 JSON，失败在 stderr 输出 JSON 并非零退出；中断渲染写 cancelled 回执。输入 JSON 与素材中的路径按进程 cwd 解析，建议使用绝对路径。工程/输出目录的父目录须存在；拒绝 URL、symlink 和非普通文件；文件系统根目录下的系统别名（如 macOS 的 `/tmp`、`/var`）会先解析为真实路径，其下各级仍拒绝 symlink。

`render` / `preview` 可在输出路径后加 `--revision <正整数>`，直接导出已保存的旧版式；不传时导出当前修订。回执绑定实际选中的修订与摘要，不解锁、撤销或新增工程修订。先用 `read <project> <revision>` 确认所选版本；参数错误或修订不存在时，在创建输出目录前失败。使用工程外的新输出目录（按目录身份而非路径文本判断，大小写变体或别名指向工程内部同样拒绝），保留每次导出及回执；`preview` 的缩小图不承担原生像素保真保证。

对象由 ID 寻址，数组顺序从底层到顶层。共用属性为 `id/kind/locked/visible/x/y/width/height/opacity`：

| kind | 额外字段 | 范围 |
| --- | --- | --- |
| image | `asset_id`, `fit` | PNG/JPEG/WebP；contain / cover / fill |
| text | `text`, `font_size`, `color`, `align`, `line_height` | 精确中文/拉丁文案；固定 Regular 字体；左/中/右对齐 |
| rect | `color`, `radius` | 纯色矩形/圆角装饰 |

画布为 `{width, height, background}`，颜色为 `#RRGGBB`，工作图固定 sRGB；P0 不支持旋转、任意 SVG/HTML、富文本、可变字体或第三方工程导入。文本按字符换行，缺字失败。`create-photo`、`edit --dry-run` 与实际编辑提交均用导出引擎检查最终可见文字的字宽和排版高度；超出文本框时失败且不保存新素材或修订。仅独立、显式解锁跳过排版测量，以便修复旧工程。通用 `create` 仍检查结构与字形，导出保留独立排版检查。预检不代表遮挡、安全区或创意质量通过。

创建输入示例（文件路径替换为已有授权素材）：

```json
{
  "project_id": "product-poster",
  "title": "春日海报",
  "canvas": {"width": 1000, "height": 1000, "background": "#ffffff"},
  "assets": [{"id": "product", "source": "/absolute/product.png"}],
  "objects": [
    {"id": "product", "kind": "image", "locked": false, "visible": true, "x": 500, "y": 180, "width": 400, "height": 650, "opacity": 1, "asset_id": "product", "fit": "contain"},
    {"id": "headline", "kind": "text", "locked": false, "visible": true, "x": 60, "y": 100, "width": 400, "height": 200, "opacity": 1, "text": "春日焕新", "font_size": 64, "color": "#263d30", "align": "left", "line_height": 1.25}
  ]
}
```

编辑批次示例：

```json
{
  "base_revision": 1,
  "author": "agent",
  "summary": "上移标题并放大商品",
  "operations": [
    {"type": "update_object", "id": "headline", "patch": {"y": 80}},
    {"type": "update_object", "id": "product", "patch": {"x": 480, "width": 440}}
  ]
}
```

操作包括 `add_asset {asset:{id,source}}`、`add_object {object}`、`update_object {id,patch}`、`remove_object {id}`、`reorder_objects {ids}`、`set_canvas {canvas}`、`revert_to {revision}`。完整字段及语义由 `document.mjs` / `project.mjs` 校验，未知字段失败。

### 候选工具与局部合成

```sh
node cli.mjs candidate-stage /absolute/project /absolute/stage.json
node cli.mjs candidate-list /absolute/project
node cli.mjs candidate-read /absolute/project warm-background
node cli.mjs candidate-compare /absolute/project /absolute/compare.json
node cli.mjs candidate-accept /absolute/project /absolute/accept.json --dry-run
node cli.mjs candidate-accept /absolute/project /absolute/accept.json
node cli.mjs candidate-discard /absolute/project /absolute/discard.json
node cli.mjs candidate-unlock /absolute/project /absolute/unlock.json
```

背景候选 stage JSON：

```json
{
  "id": "warm-background",
  "base_revision": 1,
  "target_id": "background",
  "source": "/absolute/candidate.png",
  "mode": "replace",
  "summary": "暖色背景候选，保留前景对象"
}
```

候选图须与目标图层的**素材栅格尺寸**一致，工具不隐式缩放。候选绑定工程身份、基础修订/摘要、目标对象/原素材、原始结果和最终 PNG；到达仅写入候选及素材缓存，不变更已接受文档。源文件移走后仍能查看/接受。

比较输入为 `{"candidate_id":"warm-background","output":"/absolute/new-comparison"}`；左侧是基础修订、右侧是候选应用后的完整海报。只读预览保存实际 PNG 和候选摘要，不创建工程修订。陈旧候选也可对比，但报告明确基础修订及当前修订；画面基于旧修订，不能以此覆盖人工的新文案。

单张候选预览及比较右侧的 `receipt.json` 在 `candidate_preview` 中附带 `checked_at`、`status_at_check`、`current_revision_at_check`、`accepted_revision`、`applied_in_current`、`stale` 和 `decision_pending`。例如 accepted 且 applied_in_current=false 表示保留接受历史、当前已不应用；discarded 图仍可用于失败复盘，回执明确其状态。状态来自现有 candidate-read 核验，无法核验决定记录时导出失败并清理本次图片。这里记录的是检查时观察，不是后续接受许可；决定前仍读取当前工程。渲染的 completed 只表示技术完成，`visual_quality` 始终为 UNVERIFIED，候选接受不自动产生视觉批准。普通当前修订导出不附带候选字段，旧回执不回写。

接受输入为 `{"candidate_id":"warm-background","base_revision":1,"author":"agent","summary":"采用暖色背景"}`，也可提交一个孤立 `accept_candidate {candidate_id}` 编辑操作。接受整批检查当前修订、候选基础摘要、锁定、绑定字节与重新合成结果，创建一个新修订。陈旧结果必须重新判断并以新 ID 显式暂存；修改请求中的 base_revision 不能默默重基。按当前任务授权策略选择，不额外强制人工审批。

丢弃输入为 `{"candidate_id":"warm-background","author":"human","summary":"不采用"}`，只写不可变决定，工程修订保持。状态包括 ready/stale/accepted/discarded/decision_pending。接受/丢弃通过候选级独占声明串行，工程提交仍受全局修订冲突约束。撤销接受形成新修订，候选保留已接受历史，`applied_in_current=false` 表明已不在当前目标图层；不重新开放消费同一 ID。

局部合成用 `mode="masked"`，附带以下 edit 输入。四个范围全部以目标素材原始栅格坐标描述；素材尺寸由工程读取，不由调用方猜测：

```json
{
  "context": {"x": 820, "y": 740, "width": 180, "height": 180},
  "generation_mask": "/absolute/generation.png",
  "protection_mask": "/absolute/protection.png",
  "blend_mask": "/absolute/blend.png"
}
```

context 是模型所需周边范围的声明；本地 candidate-stage 不向模型发送它，Provider Adapter 当前只接受全图 context 并发送完整目标栅格。generation_mask 的非零区声明允许生成范围，须位于 context 内；blend_mask 的非零区须位于生成范围内，0 保留原图、255 采用候选，中间值为羽化。protection_mask 必须为二值，255 强制保留原像素，并从最终有效 blend 扣除。本地蒙版全部为与目标尺寸一致的单通道 8-bit 灰度 PNG、不带 alpha；工具拒绝彩色、错尺寸及软保护蒙版。

合成在 sRGB 8-bit RGBA 上按预乘 alpha 混合，再完整解码 PNG，检查保护区及有效 blend 外的 RGBA 字节不变；接受前重算，拒绝篡改或伪造 QA。该保证针对目标素材栅格，移动/缩放/cover 裁切后的画布需要另查坐标映射及采样边界。它不是生成模型行为保证，也没有解决透明商品的光学/反射融合。

先 read，再拟定局部批次；dry-run 检查拟议文档并与旧文档比较，再提交、预览并检查实际画面。`base_revision` 陈旧时拒绝写入，重读后重新判断。`author` 只记录来源声明，不是身份认证或 ACL。整批结构/引用/字形校验后发布一个新修订；并发提交同一基础修订只有一个成功。文字框适配在渲染时检查，编辑合法仍可能需要调版才能导出。

锁定对象禁止修改、删除和显式重排；修改锁定状态必须是单独一个批次。撤销用单独的 `revert_to` 操作，创建新修订并保留当前锁定政策；会改变当前锁定对象字段或数组层级位置的撤销被拒绝，dry-run 与实际提交遵循同一规则。锁定不是像素保护蒙版，其他图层仍可能遮挡它，需看实际合成。新比例通过 set_canvas 与对象变换明确重排，不把缩放成品图当作工程适配。

## 保存、渲染与证据

```text
project/
├─ revisions/000001.json …   不可替换的修订及父摘要
├─ assets/<sha>.<format>     原始素材字节
├─ assets/<sha>.png          方向归正、sRGB 的渲染素材
├─ fonts/<sha>.otf           工程绑定的固定字体
├─ masks/<sha>.png           P1 固定蒙版字节
└─ candidates/<id>/          不可变候选；可选 discard 决定
```

将整个工程目录保存或搬移即可重开，无需原素材路径或安装字体。读取验证修订序列、父摘要、当前素材/渲染素材/字体；渲染再检查绑定。哈希检测意外篡改，不是对本地恶意进程的认证。并发提交失败可能留下无引用的不可变素材缓存，P0 不自动做垃圾回收。

候选接受记录在修订 change.candidate 中，读取校验其 manifest 摘要。候选源、合成结果和蒙版共用内容寻址缓存；失败/取消可能留下无引用字节，但不变更已接受文档。最多 64 个候选 ID，包含已接受/丢弃记录；不自动清理历史。进程异常可能留下 `.decision-lock` 或未完成暂存目录，工具明确报告并阻止决定，须检查工程/历史后人工恢复，不按 PID 猜测后自动解锁。确认后用 `candidate-unlock`（输入 `{"candidate_id","author","summary"}`）显式释放：锁内 PID 仍在运行时拒绝，释放时写入不可变的 `lock-release-*.json` 审计记录；接受/丢弃结果始终从修订历史与 `discard.json` 重新推导，释放锁不会伪造决定。`candidate-list` 对单个异常条目就地报告为 `incomplete`（缺 candidate.json 的中断暂存，检查后删除目录即可复用 ID）或 `unreadable`，不再使整个列表失败；`.DS_Store` 等非候选条目不计入 64 个名额。`candidate-read`/接受仍严格校验。

渲染由独立 Node worker 执行，默认 60 秒超时，支持 AbortSignal；成功回执记录实际安装的引擎版本、修订/素材/字体摘要、PNG 尺寸/摘要和技术 QA。输出含 `image.png`、字体已轮廓化的 `image.svg`、`document.json`、`receipt.json`。导出目录的 JSON 只是该修订的快照；继续编辑需要完整工程目录，SVG 本身也不是源工程。

预览由同一全尺寸 PNG 缩到最长边 640 px；导出保持画布尺寸。失败/取消留下回执并清理本次 PNG/SVG，源工程不变。技术 QA 覆盖 PNG 完整解码、尺寸、对象边界、字形与排版高度，回执始终将 `visual_quality` 标为 UNVERIFIED；真实视觉检查、品牌准确性和交付批准另行记录。

边界：画布/素材最多 16,777,216 像素、边长最多 8192；源文件最多 20 MB，最多 64 素材/100 对象/100 操作/1000 修订。工程读写是受信任本地工具，不是多租户隔离 worker。Provider Adapter 与 canonical Job/Receipt 桥接见下节；真实商品和显式源码 Skill 的 Pi CLI 证据见上游维护段落。权限、队列、费用、业务宿主与完整生成/编辑验收留后续。当前本机 macOS / Node 24 已验证；Linux CI 已配置待实际运行，Windows 与宿主工具注册未验证。

## GPT Image 2.5 Adapter

有界验收脚本 `provider-acceptance.mjs` 的事件 `outcome` 表示执行、候选创建及对比产物全部完成；`provider_outcome` 单独保存 Provider 结果。Provider 成功但候选创建或对比失败时，事件为 failed、总报告为 PARTIAL，原始模型产物保留且不重试。三项均完成才标记 CANDIDATES_READY_FOR_INSPECTION；这仍不代表视觉质量或人工批准。测试通过显式测试配置与 loopback 调用同一验收函数，不读取真实全局凭据。

按用户授权读取 `~/.codex/config.toml` 中 active model_provider 的 base_url，以及 `~/.codex/auth.json` 的 OPENAI_API_KEY；凭据只留当前进程内存，不复制到工程，不修改全局配置。HTTP 仅允许 loopback，远程地址须 HTTPS，拒绝带凭据、query 或 fragment 的 URL。初版不读取 OAuth token 或其他 provider key。

```sh
# 只查询登记型号，不证明生图成功
node cli.mjs provider-check .
# 不读取凭据、不发送请求、不写入工程的试运行
node cli.mjs provider-run /absolute/project /absolute/run.json --dry-run
# 当前任务授权覆盖后执行；会产生真实模型请求
node cli.mjs provider-run /absolute/project /absolute/run.json
```

run.json 示例：

```json
{
  "job": "/absolute/image-job.json",
  "candidate_id": "warm-generated",
  "base_revision": 1,
  "target_id": "background",
  "references": []
}
```

job 使用 canonical `creative-craft.image-job.v2`，profile 明确为 `openai.gpt-image-2.5-sunburst.2026-09-08` 或 `openai.gpt-image-2.5-flare.2026-09-08`，surface 为 openai.image_api。须 ready、single_turn、一个 PNG 输出，尺寸与目标素材一致，且满足 Provider 的 16 倍数和像素限制。支持 low/medium/high/auto 与 opaque/auto/transparent；xhigh/max 尚未扩展。canonical v2 的 transparent 需 profile 明确声明 `transparent_background: true`，并使用 PNG/WebP；本 Adapter 继续只输出 PNG。默认 Skill 的 GPT Image 2 profile 和 legacy v1 仍拒绝透明任务。

透明任务只需在 job 中设置 `"canvas.background":"transparent"`，其余 run.json、引用和蒙版接口不变。返回图必须实际含 alpha，至少有一个 alpha=0 的背景像素和一个 alpha>0 的前景像素；这是最低结构要求，不是抠图或玻璃画质评分。无 alpha、没有全透明背景（包括全不透明/全图半透明）及全透明空图分别报 `output_missing_alpha`、`output_no_clear_background`、`output_empty_foreground`。已收到的图保留为 received-output，写 partial 回执，不发布候选或自动重试。

回执 `parameters.transparency.received/output` 记录对应图片 SHA、尺寸、alpha 通道及全透明/半透明/不透明像素数。显式缩放前后分别检查，离线恢复和候选读回重新从绑定字节计算；证据缺失或计数不符则拒绝。蒙版合成后的候选也必须保有可见前景与透明背景，且保护区/合成边界外像素检查继续生效。若合成耗尽透明区域，保留 Provider 成功回执和产物，`result.json` 标记 candidate_failed 及原因，不能因此再次生图。opaque/auto 及历史普通回执不要求新增 alpha 证据。

generate 的 references 为空；参考图创作和局部编辑使用 edit。每个引用为 `{asset_id,source}`，最多 3 项，顺序与 job.asset_refs 一致；edit 第一项须为当前目标素材。蒙版编辑附带 candidate-stage 的 edit 字段，但 context 须覆盖全图；本地“白色可改”转换成 Provider 的“alpha=0 可改”，保护区保持 alpha=255。合成仍以原图和本地保护/合成蒙版执行，Provider 的掩码不是像素保证。

使用网关的 `/images/generations` 和 `/images/edits` 路由；全局 wire_api=responses 不会把图片模型当作文本主模型。网关源码含 Images → Responses 转换，不推定实际运行与源码逐行一致，也不代替真实请求验证。

任务永久保存在 `jobs/<job_id>/`，包含原 Job、编译包、请求摘要、已发送引用/蒙版、started、输出与 canonical Execution Receipt。job_id 的独占目录保证工具不会自动重试或重复消费；若请求尚未发出就失败（如发请求前的修订冲突或取消），目录会被删除并释放 job_id，重新读取工程后可用同一任务再执行；中断遗留的 started 不是成功证据，检查上游执行后再决定恢复。默认请求超时 180 秒；客户端取消不能承诺撤销上游计算或费用。网关内部重试、实际费用、未报告的快照/审核结果均保留 UNVERIFIED，不用官方价格冒充账户账单。

返回的图片须完整解码并符合请求规格；可解码但不符合规格的产物单独留存为 received-output，回执标 partial，工程保持。成功结果先暂存，候选绑定 Job/Receipt 摘要与真实源图；接受时重验。生成中发生人工修改时结果标 stale。Provider 成功但暂存失败时保留产物/回执，禁止为此重复生成。上述回执只证明执行，不自动批准创意或推进正式项目状态。

默认 output_policy=strict；run.json 可显式设 `"output_policy":"resize_to_target"`，只允许宽高比完全相同的单帧 8-bit PNG 全图缩放到目标尺寸，拒绝裁切、拉伸或猜测尺寸。原始返回图与适配图都保留，回执记录原始/目标规格、摘要与 Lanczos3 参数；接受时重新计算适配结果。此策略用于本次网关“请求 1024×1024、返回 1254×1254”的已观察差异，不推定所有 GPT Image 2.5 服务都有这个行为。

已有 partial 尺寸错误但 received-output.png 仍在时，可使用 `provider-recover <project> <input.json>`，输入为 `{"job_id":"original-job","candidate_id":"new-candidate","output_policy":"resize_to_target"}`。它只做离线缩放和暂存，不读凭据、不发请求，不覆盖原 receipt；生成 normalized-receipt 并绑定原回执摘要。异常遗留的 normalization-started 须人工检查，工具不自动重新执行。若请求已发出但本地回执校验失败（如 Python 不可用），执行会保留 `receipt.unvalidated.json` 与已收到的输出；校验恢复后用同一命令（`{"job_id","candidate_id"}`，成功回执无需 `output_policy`）先校验并提升为 `receipt.json`，再暂存候选，同样不发请求；已有 `result.json` 的任务不再重复暂存。响应体完整收到后，迟到的超时/取消不再丢弃结果。

`provider-smoke.mjs --live` 会产生最多两个真实客户端 POST，故未接入 npm 默认 smoke 或 CI；只在当前授权覆盖调用时运行。普通 npm test 使用本地模拟服务，不访问真实 Provider。

复用已保存背景的后续验收入口如下。prepare 只做本地夹具/蒙版/正式 Job 与 dry-run；run 最多三次真实 POST（一次 Sunburst 局部编辑、两个型号各生成一次），独占 live-started，失败不自动重跑。结果仅暂存，不自动接受；应查看完整海报和局部细节后决定。输入背景须为 1024×1024 PNG，generation-job 为 canonical ready 生成任务。

```sh
node provider-acceptance.mjs prepare /absolute/cached-background.png /absolute/generation-job.json
# 将 prepare 返回目录传入；仅在当前授权覆盖时执行
node provider-acceptance.mjs run /absolute/prepared-directory --live
```

官方选型：Flare 是偏速度的小模型，Sunburst 是偏质量/精确编辑的基础模型；两者都支持生成、编辑和透明背景。先按具体任务建立质量基线，再用相同提示/参考/尺寸/quality 比较速度；不能假定 Flare 更便宜。依据：[官方提示词与选择指南](https://developers.openai.com/api/docs/guides/image-prompting)，2026-10-04 核验。

能力边界：受控修改扁平照片外围背景与独立排版已验证；不提供独立商品抠图，深色背景、透过瓶身的新背景、重打光和商品独立移动须另行验收 alpha matte/合成，见 [ACCEPTANCE.md](ACCEPTANCE.md)。

## 上游维护

Satori / resvg-js / Sharp 与字体的固定点，以及 InvokeAI 候选流程、Krita 蒙版方法的承接路径，在[上游登记](../../docs/upstream-absorption.md#image-engineering-references)及[监控清单](../../docs/upstream-watch.json)。维护时先跑：

```sh
python3 ../../scripts/upstream_drift.py --only satori --only resvg-js --only sharp --only noto-cjk
python3 ../../scripts/upstream_drift.py --only openpencil --only invokeai --only krita-ai-diffusion
```

实际依赖许可：Satori、resvg-js 为 MPL-2.0，Sharp 为 Apache-2.0，字体为 OFL-1.1；Sharp 的 libvips 与原生/传递依赖单独保留自身条款。新版 resvg 核心的 Apache-2.0 OR MIT 不能替代本模块 Node 绑定及其旧核心的许可。此模块使用发布包，不复制上游编辑器源码；上游默认分支 SHA 是研究点，package-lock.json 才是所用 npm 闭包。
