# Local production MVP

可选的本地制作模块：已有/生成素材 → 版本化多轨工程（EditDocument v2）→ 有界批次编辑 → 预览 MP4 → 技术检查（QA）→ 修改 → 导出。它是 Creative Craft 的执行工具（Video Harness v1 的 P0 执行层，0.3.0 起含 P2 包装与音频：变速、淡入淡出、交叉淡化、音乐自动闪避、带类型变量的图形模板），不包含自然语言规划器、阶段关卡、DataHub UI、素材检索或 Seedance 调用。现有 Python CLI 和轻量 Skill 安装保持不变；本模块目前只随源码 checkout 使用，不在根 npm/Skill 发布包中。

## 安装和运行

Node.js >=22、FFmpeg/ffprobe、可用的独立 Chrome 渲染进程。不要在用户浏览器 Profile 上执行渲染。

```sh
cd integrations/local-production
PUPPETEER_SKIP_DOWNLOAD=true npm ci --ignore-scripts
npm run fetch-font   # 下载 fonts/manifest.json 固定的字幕字体并核对 SHA-256；二进制不入库
export PRODUCER_HEADLESS_SHELL_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
node cli.mjs --help
npm test
npm run smoke        # 需要带 jsonschema 的 Python，见“验证与限制”
```

Chrome 路径示例仅适用于对应 macOS 安装；其他主机指定自己的渲染 Chrome 路径。模块不会自动下载 ASR/TTS 模型或调用云端语音服务。`ffmpeg`/`ffprobe` 需在 worker 的 PATH；`CREATIVE_FFMPEG`/`CREATIVE_FFPROBE` 仅覆盖本模块校验/QA/样例命令，不修改 HyperFrames 的二进制解析方式。

这是受信任本地用户的执行工具，不是多租户沙箱。DataHub 接入前必须另建隔离 worker、权限检查、任务队列、预算及受控素材解析。当前只接受本地普通文件；不接受 URL、任意 HTML、脚本或外部工程导入。项目路径与素材路径拒绝 symlink；macOS `/tmp`/`/var` 的系统别名需改用其真实路径。

### 固定版本（HyperFrames 升级评估结论）

所有 `@hyperframes/*` 精确固定为 **0.8.108**：`@hyperframes/producer` 与 `@hyperframes/lint` 为直接依赖，`core`/`engine`/`parsers`/`studio-server` 通过 package.json `overrides` 固定为同一版本（producer 自身声明为 `^0.8.108`，不加 overrides 会随发布漂移）；`gsap@3.13.0`。依赖闭包见 package-lock.json（其中 `puppeteer-core@25.12.0`）。

升级前（0.1.0）锁定为 `@hyperframes/producer@0.8.53`，但其 `^0.8.53` 间接依赖实际解析为 core/engine/lint/parsers/studio-server **0.8.54**，版本并不一致。2026-10-02 评估：升级到 0.8.108 后 `npm test`、`npm run smoke`、`node --test tests/font-render.integration.mjs` 全部通过，故保留升级。0.8.108 的 `executeRenderJob(job, projectDir, outputPath, progressSink, signal, assertRenderActive?)` 前五个参数与 0.8.53 相同（新增可选第六参数，本模块不使用）；上游 README 的 `inputPath/outputPath` 写法仍与安装包不一致。输出尺寸仍从编译 HTML 的 composition 定义读取，不能依靠无效的 `width/height` RenderConfig 字段。回执的 `engine_version`、`lint.version` 从已安装包读取，不再写死。

## 工程模型：EditDocument v2

共享合同为 `skills/creative-craft/schemas/edit-document-v2.schema.json`；语义规则由 `edit-document.mjs` 的 `validateV2` 执行，并以 `tests/fixtures/edit-document-v2/{valid,invalid}` 与 Python 核心保持一致（invalid 文件名即被违反的规则）。

- **素材（assets）与时间线实例（items）分离**；同一素材可多处引用。素材按 SHA-256 内容寻址复制到 `assets/<sha256>.media`，记录 `origin.kind = import | generated | render`（生成镜头须带 `provenance_ref`）。
- **轨道（tracks）** `video | audio | caption`，数组顺序即视频叠放顺序（靠前在下）；`locked` 轨道上的 item 不可被任何操作修改、删除或移入。修改锁定状态的 `edit_track` 必须单独成批（不能与其他操作同批，堵住“先解锁再修改”）；`revert_to` 保留当前锁定，且不能改动当前锁定轨道的内容。v2 `create` 与 `add_asset` 同样要求 `origin.kind = generated` 的素材带 `provenance_ref`。
- **输出时间**为 canvas.fps 下的整数帧，半开区间 `[start_frame, start_frame + frames)`；**源时间**为秒。同一轨道 media item 不可重叠，允许空隙（空隙为黑场/静音）。
- **media item** 必须有 `asset_id/start_frame/frames/source_in_seconds/volume`；视频轨要求素材有画面，音频轨要求有声音；`source_in_seconds + frames/fps ≤ asset.duration`。视频轨 item 可带 `fit`（默认 contain）、`opacity`、`transform {x, y, scale}`：x/y 是 item 中心占画布的比例，scale 是 item 框占画布宽高的比例（0.05–1）。音频轨 item 不接受画面属性。
- **caption item** 只能在字幕轨。`link {item_id, source_from, source_to}` 形式按所链接 media item 的**源时间**换算输出时间：显示区间 = link 源区间 ∩ 该 item 当前源窗口，随 item 移动、裁切自动生效，**不存输出时间**（带 link 时不得有 start_frame/frames）。无 link 时必须给 `start_frame/frames`。
- 与 Python 核心一致的附加规则：media item 不得带 `text/style/link`；caption item 不得带 `asset_id/source_in_seconds/volume`；`revision = 1` 时 `parent_sha256` 必须为 null，否则必须为 64 位十六进制。
- **成片时长** = 所有 media item 与非 link 字幕的最大结束帧，1 帧至 10 分钟。
- 每个修订带 `change {author: agent|human|system|migration, summary, operations_sha256}`。
- 可选 `graphic_templates: [{id, version, sha256, file}]`：本修订固定的图形模板（`file` 必须是 `templates/<sha256>.json`）。字段存在时每个 graphic 的 `template` 恰有一个同 id 绑定，绑定不得重复、不得有未被使用的绑定；见“模板版本与回执”。

### P2 字段：包装与音频

均为可选字段，旧文档继续合法。规则见 `docs/content-production-architecture.md`「P2 语义规则」，Node 与 Python 各实现一次。

- **变速** `speed`（media，0.1–10，缺省 1）：源区间 = `source_in_seconds + frames/fps × speed`，须在素材时长 +0.001 s 内；link 字幕输出时间 = item 起点 + (源时间 − 源入点) / speed。
- **淡变** `fade_in_frames` / `fade_out_frames`（media、graphic）：非负整数帧，二者之和 ≤ `frames`。画面为透明度，声音为音量包络。
- **转场** `transition_in: {kind: "crossfade", frames}`（media）：同轨 item 不得重叠，唯一例外是后一 item 声明 crossfade、起点严格晚于紧邻前一 item、且重叠帧数恰好等于 `frames`（不超过两者各自长度）；重叠检查覆盖所有在前 item，不只相邻的；声明 crossfade 却无重叠同样无效。
- **自动闪避** 轨道 `duck: {under_track_id, depth_db (−24…−3), attack_frames (0–60), release_frames (0–120)}`：只在 audio 轨；参照轨必须存在、不是自身、是 video 或 audio 轨，且自身不带 duck（只有一层）。
- **图形** item `kind: "graphic"`：只在 video 轨，只接受 `id, track_id, kind, template, vars, start_frame, frames, fade_in_frames, fade_out_frames, opacity`；参与同轨不重叠与成片时长；`vars` 值只能是 1–200 字符字符串、有限数字或布尔值。模板存在性与变量类型由 Node 校验（见下文“图形模板”）。
- caption 不得带 speed、淡变或转场字段。

### 源素材帧对齐（0.6.0）

合同见 `docs/content-production-architecture.md`「源素材帧对齐（2026-10-03）」。入点常被写成截断的小数（镜头首帧是 733/30 = 24.4333… 而写成 24.4333），渲染器显示“时间 ≤ 入点”的帧，于是成片第 0 帧是上一帧（旧镜头末帧）。

- **asset `frame_rate`**（可选，有理数字符串，如 `"30/1"`、`"30000/1001"`）：v2 `create` 与 `add_asset` 导入时由 ffprobe 写入，只在 `video: true` 的素材上合法（`validateV2` 拒绝纯音频素材上的该字段及非 `<num>/<den>` 形式；这是素材规则的唯一来源，编译时的修正函数只看 `frame_rate`）。导入时按工程格式决定：v1 工程（`local-edit.v1`）的导入不探测也不写该字段；已有工程不改写、不补写；v1 迁移得到的素材也没有该字段。
- **导入规则**（`probe` + `probedFrameRate`）：`video` 标记与宽高**保持原行为**，取自第一条视频流（任何视频流，包括封面图 `attached_pic`）；因此带封面图的音频文件仍是 `video: true`、宽高为封面尺寸，v1 工程照旧可把它用作 clip。`frame_rate` **只在第一条视频流不是封面图时**记录（保证帧率与宽高来自同一条流；封面图在前、画面流在后的文件不记录）。该流 `r_frame_rate` 与 `avg_frame_rate` 约分后**完全相等**（恒定帧率），且该流起点（`start_pts × time_base`，与 QA `sourceTiming` 同一来源）**等于所有流的最早起点**（渲染器与 QA 共同的媒体时间零点，见下文「素材兼容与渲染尺寸」；按整数精确比较），才记录约分后的帧率。所有流从同一非零时间开始（如都在 0.5 s）也记录；音频早于视频开始（MKV/WebM 可保留的负音频起点，或视频晚于音频 0.5 s）则不记录（0.7.0 起；0.6.0 只要求视频流自身起点为 0，会给负音频起点的 MKV/WebM 记录帧率并按错误的帧网格修正）。否则（可变帧率、视频晚于其他流开始、缺 `start_pts` 等）不记录，这类素材保持渲染器原口径，由 QA 按解码出的实际帧时间检查并报警。“分析画面流”（第一条非封面视频流，`pictureStream`）、比值解析（`rational`）、流起点（`streamStart`，唯一的起点解析：返回精确有理数 `{p, q}` 与秒数 `seconds`）、最早起点（`earliestStart`）与“帧网格是否从媒体时间零点开始”的判定（`mediaZeroProblem`，给出不满足的原因）由导入、渲染/QA 复核与 QA `sourceTiming` 共用。
- **加载时复核**（`frameAlignment`，`frame-alignment.mjs`，0.7.0）：0.6.0 导入的工程可能在负音频起点的 MKV/WebM 上留有 `frame_rate`。是否对某素材应用 `frame_rate` 在 **`loadProject` 中一次性确定**（与模板集同样方式）：对每个带 `frame_rate` 的素材先校验文件摘要（文件被改或缺失时加载失败，与绑定模板一致），再 ffprobe，按导入同一规则（`mediaZeroProblem`）核对“视频流起点 = 所有流最早起点”；各素材并行探测。探测结果按“文件真实路径 + 刚校验通过的 `sha256`”在进程内缓存：只有自己已通过摘要校验的调用者才会用到缓存，进行中的探测只在同一键的调用者间共享，失败不缓存，因此并发加载不会因别的工程素材被改而失败。不满足的素材**不做截断修正**（其 item 保持写定入点，即渲染器原口径）。结果 `alignment`（`[{asset_id, frame_rate, applied, reason?}]`，每个带 `frame_rate` 的素材一项）随加载结果返回，并绑定到加载出的文档上（`bindAlignment`），所以这份文档的每一次 `compiledView`（编辑时的字体规划与校验、`activeCaptions`、`compose`、渲染）都使用同一决定，没有可遗漏的参数；`editBatch` 把同一字节已作出的决定带到新修订（`carryAlignment`；本批新导入的素材刚按导入规则探测过，视为应用；`revert_to` 用目标修订加载时的决定）。渲染回执记录 `frame_alignment`（v2 工程无此类素材时为 `[]`，v1 工程无该字段）；渲染时 `verifyAssets` 复用 `loadProject` 已校验的文件，每个素材文件只做一次摘要。**QA 以回执为准**：`qaRender` 用回执的 `frame_alignment` 构造编译视图，不再自行探测决定；回执缺该字段（0.7.0 之前的渲染，当时对所有带 `frame_rate` 的素材都做了修正）时按“全部已应用”构造。`burned-caption-cut-points` 与 `cut-boundary-fragments` 的 `measured` 给出 `frame_alignment` 与来源 `frame_alignment_source`（`receipt` 或 `legacy-default`）；回执的对齐与文档的 `frame_rate` 素材不一致时 QA 报错。已存工程文件不改写，`project.json` 快照仍是原文档。代价：读取 v2 工程（含 CLI `read`、编辑）会对带 `frame_rate` 的素材做一次摘要与（首次）探测。
- **修正规则**（`truncatedFrame` / `correctedSourceIn`，`source-frames.mjs`）：只修正“小数截断”。视频轨 media item 的源入点若低于某帧起点（k/帧率）**不超过 2 ms 且严格不足 0.1 帧**（两条同时满足；覆盖截到毫秒的写法，如 30 fps 第 733 帧写成 24.433、24.4327 或 24.4333，29.97 fps 写成 24.457，24 fps 写成 30.541），编译为该帧起点 **+ 0.1 ms**（0.0001 s，保留到 1e-9 s）；恰在帧起点、或低于帧起点超过 2 ms（如 30 fps 下 24.430，低 3.3 ms）、或达到 0.1 帧（60 fps 下 0.1 帧 = 1.67 ms，先于 2 ms 生效）的入点**保持原值**（不再整体对齐到帧中点）。全程用 BigInt 有理数精确计算：入点按文档中 JSON 数值的最短十进制形式（如 `24.4333` = 244333/10000），帧率按整数比；恰低 2 ms 仍修正，恰低 0.1 帧不修正。位移上限为 min(2 ms, 0.1 帧) + 0.1 ms。帧率参数可传字符串或 `parseFrameRate` 的解析结果，`correctedSourceIn` 只解析一次，两种形式结果一致。
- **编译视图**（`compiledView(doc)`）：一次算出带修正入点的 items（文档不被改写，未修正的 item 与原文档共用同一对象，`correctionOf(item)` 给出原 item 与修正到的帧号）；对视图再调用直接返回自身。应用哪些素材的 `frame_rate` 由文档绑定的对齐决定（见上文加载时复核）；**未绑定的文档**（内存中构造的文档：测试、直接 `compose` 的字面文档、`createProject` 刚按导入规则探测过的素材）只做结构计算，即按记录的 `frame_rate` 全部应用，不读任何文件。编译（`data-media-start`、link 字幕窗口、字体绑定的可见字幕）、`activeCaptions`、QA 字幕采样与两项剪辑点检查都使用同一个视图，不各自调用修正函数：渲染时 `renderProject` 只计算一次视图，传给字体校验（`verifyAssets`、`copyCaptionFont`）与 `compose`（`project.json` 仍写原文档）；`qaRender` 按回执的对齐计算一次，供字幕采样与剪辑点检查；创建/编辑时 `planCaptionFont` 只算一次字体 runs，`editBatch` 对 base 与 next 各算一次。同一视频轨 item 的 `<audio>` 与 `<video>` 用同一个修正后的入点（位移 ≤ 2 ms + 0.1 ms，音画同步不变）。
  - **音频轨** item（包括放在音频轨上的同一视频素材）**不修正**，精确写定的音频入点保持不变。
  - **拆分连续性**：`split_item` 写定的尾段入点 = 头段入点 + 头段时长，一般不在截断容差内，编译后仍等于头段结束处；头段本身被修正时，接缝两侧相差不超过 2 ms + 0.1 ms。
  - **片尾范围**：修正后的入点 + 时长若超出素材时长 + 0.001 s（与 `validateV2` 同一容差 `SOURCE_END_TOLERANCE`），该 item 不修正，保持写定入点。
- **QA**：两项剪辑点检查（烧录字幕、相邻镜头碎片）按编译视图判断（渲染实际起播时间），但**按文档写定值报告与建议**：`measured.points` 的 `source_seconds` 是文档写定值（入点为写定入点，出点为写定入点 + 时长换算的写定出点），`suggested_shift_seconds` 以它为基准（写定值 + shift = 建议值，按 shift 改文档即得到目标帧中点），描述文本中的 “source in X” / “at source X” 也是写定值。入点被修正的 item 另列 `compiled_source_seconds`（编译后实际值，文本中写作 “(compiled X s)”），入点还记录 `source_frame`（修正到的帧号）。未修正的剪辑点不加这些字段，按渲染器口径判断（见下文 QA）。内部剪辑点（`cutPoints`）不携带原 item，需要写定值时用 `correctionOf(point.item)`。
- **真实素材复验**（`byq-foundation-02` 整片，720×1280 30 fps，视频与文件起点均为 0，只读，临时工程已删除）：v2 导入记录 `"30/1"`。item `cut` 入点 24.4333、30 帧，编译为 24.433433333（第 733 帧起点 + 0.1 ms）；预览第 0 帧（`select=eq(n\,0)`）与源第 733 帧（新镜头首帧）MAE 0.89、与第 732 帧 55.0。同工程 item `plain` 入点 60.65（帧内，非截断）编译后仍为 60.65。QA `cut-boundary-fragments` 与 `burned-caption-cut-points` 均为 pass。第二轮（2 ms 阈值）复验：同一素材临时 v2 工程，item `cut` 入点写成 3 位小数 24.433、30 帧，编译为 24.433433333；预览第 0 帧与源第 733 帧 MAE 1.01、与第 732 帧 55.08；两项剪辑点检查均为 pass，入点报告 `source_seconds` 24.433（写定值）、`compiled_source_seconds` 24.433433、`source_frame` 733（碎片检查 aligned），出点报告写定出点 25.433 与编译出点 25.433433。
- **局限**：只修正入点，不改输出帧数；帧网格假设第 0 帧位于媒体时间零点、恒定帧率（导入规则已排除不满足的素材）；源帧率与画布帧率不同时，后续帧仍按画布 fps 推进，与原行为一致；入点在帧内但离帧起点很近（如晚 0.001 帧）不属于截断，保持原值。

## 素材兼容与渲染尺寸（0.7.0）

起因：一次在 128×72 画布上的测试中，HEVC MOV、VP9/Opus WebM、H.264/AAC MKV 都在第 0 帧卡住（producer 60 s 后报 “Sequential screenshot capture stalled … stuck at frame 0”），当时疑为编码不受支持。在完全相同的条件下补做 H.264 MP4 对照后，**对照同样卡住**；同一批素材在 320×180 下全部成功。真正原因是输出画面高度，与容器和编码无关。因此**不按编码拒绝导入，也不提供转码**。

**渲染尺寸：自动放大截图再缩回**（本机实测：`@hyperframes/producer` 0.8.108、Google Chrome 154 headless、macOS；`MIN_RENDER_HEIGHT = 88`、`MAX_CAPTURE = 7680×7680`、`captureSize`、`renderSizes`，`render.mjs`）：

- **高度下限实测**（H.264 MP4 纯色素材）：截图（合成）高度 **≤ 86 px 稳定卡住**（64×64、128×72、144×80、150×84、160×72、160×86），**≥ 88 px 正常**（160×88、128×90、128×128、90×160、160×90 及以上）。源素材尺寸不影响结果：320×180 素材放进 128×72 画布同样卡住，128×72 素材放进 320×180 画布正常。**没有视频的工程同样会卡**：160×72 画布上只有音频 item 加一条字幕，停在第 6/15 帧。问题出在 Chrome 截图视口，与素材无关。
- **宽度实测**（竖向极端，高 160 px，直接以该尺寸合成并截图）：宽 **2、4、6、8、10、16、32、64 px 全部完成渲染**，输出尺寸正确；4、8、10、16、32、64 px 另核对了第 0 帧颜色为素材颜色（2 px 宽的成片无法用中心区域取色，只核对了尺寸）。8×88 也正常。也就是说宽度在 2 px 以上都不是截图瓶颈。合法画布的最窄输出是 64×3840 画布的预览（10 px 宽，单元测试遍历全部合法画布核对），因此**宽度不需要截图规则**，不设宽度下限。大尺寸方向：7680×128 与 128×7680 的截图均正常，以此作为截图上限 `MAX_CAPTURE`。
- **策略**：输出尺寸（导出 = 画布，预览 = 长边缩到 640，偶数，不超过画布）高度低于 `MIN_RENDER_HEIGHT` 时，取能达到下限的**最小整数倍** k（`captureSize`），以 k 倍尺寸编译合成（字幕字号、描边、图形 em 都按合成尺寸计算，因此与画面同比例放大）、由 producer 截图编码为 `capture.mp4`，再用 ffmpeg 缩回输出尺寸（`scale=W:H:flags=area`、`setsar=1`，整数倍时精确且宽高比不变；沿用截图的像素格式与色彩标记；音轨直接复制），随后删除 `capture.mp4`。**预览截图不大于导出截图**（`renderSizes`）：预览的整数倍截图在任一维超过导出截图时（例如 648×88 画布：预览 640×86 需要 1280×172，而导出只截 648×88；3840×88 画布：预览 640×14 需要 4480×98），预览改用导出截图尺寸截图，再按非整数比例缩回（回执 `factor: null` 并注明 `basis`；预览尺寸取偶数造成的宽高比差异小于输出的 1 px）。例：128×72 画布导出与预览都以 256×144 截图后缩回 128×72；1280×160 画布预览为 640×80（以 1280×160 截图）；3840×64 画布导出以 7680×128 截图（该截图尺寸已实测可行），预览 640×10 以 9 倍（5760×90）截图（未单独实测）；3840×88 画布预览以 3840×88 截图缩回 640×14（`tests/render-size.integration.mjs` 实测）。遍历全部合法画布（偶数，64–3840）：截图最大 7680×3840，都在 `MAX_CAPTURE` 内；超出上限的截图直接报错拒绝（对合法画布不可达，用来防止规则改动后静默使用未实测的尺寸），不做“改为不放大”的降级，因为不放大正是会卡住的尺寸。因此**任何通过 `validateCanvas` 的画布都能渲染与导出**，不再有“画布过小”的拒绝，预览也不再为截图下限把高度抬到 88 px。
- **缩回编码参数**：缩回固定使用 libx264 `-preset medium -crf 18`、像素格式与截图一致，不随预览/导出档位变化。原因：截图已经按 producer 的档位编码过一次，缩回是第二代编码，用固定的高质量参数让这一代尽量不再叠加损失，也不必跟随 producer 内部的分档参数（升级 producer 时无需同步）。代价：预览缩回比 producer 的预览档（ultrafast/CRF 28）编码慢、文件略大；缩回只发生在小于截图下限的输出上，画面很小，实际耗时可忽略。
- **缩回失败或取消**：`scaleBack` 在失败或取消时删除不完整的 `video.mp4`，任何情况下都删除 `capture.mp4`；截图阶段失败时也删除 `capture.mp4`。回执照常记录 `failed` / `cancelled`。
- **回执**：`capture: {width, height, factor, downscale?, basis?}` 记录实际截图尺寸与倍数（截图尺寸不同于输出时 `downscale: "ffmpeg scale flags=area"`；使用导出截图尺寸的预览 `factor: null` 并附 `basis`）；`output` 是缩回后的 `video.mp4`，其 `width`/`height` 就是本次渲染的输出尺寸。**QA 的分辨率检查以回执记录的 `output.width/height` 为预期**（`measured.expected_source: "receipt"`），因此按旧规则渲染的预览（如 0.6.0 把 1280×160 预览抬高到的 704×88）按它自己的尺寸判定，不会误判；回执缺这两个字段时才退回当前 `outputSize` 规则，并在 observation 与 `expected_source: "output-size-rule"` 中注明。
- **局限**：放大截图时固定像素的装饰（v1 无样式字幕的 8 px 内边距、6 px 圆角、1–2 px 文字阴影）不随倍数放大，缩回后相对变小，与预览按缩小尺寸编译时的既有行为同类；缩回会重新编码一次视频（多一代有损压缩，见上文编码参数）。
- 下限是本机实测值，换渲染器版本或 Chrome 版本后需要重新扫描（用 `MATRIX_SIZE` 跑下面的矩阵即可）。

**支持矩阵**（`node tests/media-support.matrix.mjs`，需要 `PRODUCER_HEADLESS_SHELL_PATH`；每例为 1 s 合成素材，320×240、30 fps，经 `createProject` 导入后预览渲染；判定条件为完成渲染、第 0 帧的上、中、下三个区域都是素材的颜色、有音轨的用例成片平均音量高于 −40 dB；producer 的卡顿看门狗通过 `HF_DE_STALL_MS` 缩短到 15 s；逐例串行，整轮约 1 分钟。每例的合成、探测、建工程、渲染与判定都在该例内部捕获错误，单例失败只记一行失败；临时目录在全部用例结束后删除；用例定义 `tests/media-support-cases.mjs` 是无副作用的纯模块，运行器只在直接执行时改写 console 与环境变量）。**不要并发**：同一进程内并发渲染实测会互相破坏画面（画面只覆盖帧的上部、下部为黑；320×240 下旧的“仅中心区域”判定因中心均值 rgb(195,0,0) 仍误判为通过），因此改为串行并检查三个区域；`MATRIX_CONCURRENCY` 仅用于复现该问题。0.7.0 修复后另以 `MATRIX_SIZE=128x72` 复跑整套矩阵（自动 2 倍截图再缩回），27 例全部可渲染。另用 `MATRIX_SECONDS=8 MATRIX_IN=3 MATRIX_SIZE=1080x1920 MATRIX_FULL=1`（8 s、入点 3 s、竖屏 1080×1920 导出）复测了 HEVC、VP9、MKV、HLG、VFR、旋转和 H.264 MP4 对照，结果相同。

| 用例 | 用途 | 容器 | 视频（编码/profile/像素格式） | 音频 | 结果 |
|---|---|---|---|---|---|
| H.264 8-bit 4:2:0 | 视频 | MP4、MOV | h264/Constrained Baseline/yuv420p | AAC | 可渲染 |
| H.264 10-bit | 视频 | MP4 | h264/High 10/yuv420p10le | — | 可渲染 |
| H.264 4:2:2 | 视频 | MP4 | h264/High 4:2:2/yuv422p | — | 可渲染 |
| H.264 4:4:4 | 视频 | MP4 | h264/High 4:4:4 Predictive/yuv444p | — | 可渲染 |
| HEVC 8-bit（hvc1） | 视频 | MP4、MOV | hevc/Main/yuv420p | —、AAC | 可渲染 |
| HEVC 10-bit（hvc1） | 视频 | MOV | hevc/Main 10/yuv420p10le | — | 可渲染 |
| HEVC 10-bit HLG（BT.2020，iPhone HDR 形态） | 视频 | MOV | hevc/Main 10/yuv420p10le | AAC | 可渲染（色彩见局限） |
| HEVC / H.264 可变帧率 | 视频 | MOV、MP4 | hevc/Main、h264 | AAC、— | 可渲染（不记录 `frame_rate`） |
| HEVC 旋转 90°（display matrix） | 视频 | MOV | hevc/Main/yuv420p | — | 可渲染，方向正确 |
| VP9 / Opus | 视频 | WebM | vp9/Profile 0/yuv420p | Opus | 可渲染 |
| H.264 / AAC | 视频 | MKV | h264/yuv420p | AAC | 可渲染 |
| H.264 视频的音轨 | 视频 | MP4、MOV | h264/yuv420p | MP3、Opus（MP4）、PCM s16le（MOV）、FLAC（MP4）、ALAC（MOV、MP4） | 全部可渲染且有声 |
| 独立音频素材 | 音频轨 | M4A、MP3、MP4、Ogg、WAV、FLAC | — | AAC、MP3、Opus（MP4、Ogg）、PCM s16le、FLAC、ALAC（M4A） | 全部可渲染且有声 |

原因：producer 用 ffmpeg 抽取视频帧再注入页面，音频也由 ffmpeg 处理，不依赖浏览器解码，所以本机 ffmpeg 能解码的容器和编码都可以渲染。旋转素材另行核对过方向：编码为 320×240、上红下蓝的 HEVC，带 90° 旋转元数据，在 240×320 画布上渲染成左红右蓝，与 ffmpeg 自动旋转后的源帧一致。H.264 10-bit 那一例用时约 18 s（其他约 2 s），原因未查。

**媒体时间零点（与 QA 一致）**：渲染器和 QA 剪辑点检查（`sourceTiming`）都以**所有流的最早起点**作为媒体时间零点，文档中的入点 X 对应视频时间 X + start（start 为最早起点，通常 ≤ 0）。实测（第 1.0 s 由红变蓝的素材，320×180）：
- MP4/MOV：即使用 `-itsoffset -0.044 -avoid_negative_ts disabled` 封装，ffprobe 读到的各流起点也都是 0（muxer 已经归零），因此零点就是视频起点。入点 1.016667 和 1.06 的第 0 帧都是蓝色。
- MP4 的**非零起点**（edit list 中的空 edit）实测同样以最早起点为零点：H.264 + ALAC 以 `-output_ts_offset 0.5` 封装、或纯视频 MP4 以 `-itsoffset 0.5 -c copy` 重封装，各流起点都是 0.5 s，导入记录 `frame_rate`，截断入点 0.7333 修正到第 22 帧后第 0 帧为蓝色（第 22 帧），入点 0.72 为红色（第 21 帧），与假设一致，因此 MP4 这类素材照常记录帧率。H.264 + AAC 以同样方式封装时，AAC 编码器延迟（1024 个采样）使音频起点为 0.47678 s、早于视频 23.2 ms：不记录 `frame_rate`，入点 0.75 显示视频时间 0.7268（第 21 帧，红色；若零点是视频起点则应为蓝色），入点 0.76 为蓝色（`tests/source-start.integration.mjs`）。
- MKV/WebM：可以保留负的音频起点（MKV −0.067 s，WebM −0.056 s）。此时零点在视频起点之前：MKV 入点 1.016667 和 1.06 的第 0 帧仍是红色（视频时间 0.95 与 0.993），入点 1.1 是蓝色（1.033）；WebM 入点 1.06 是蓝色（1.004）。
- 这类素材不记录 `frame_rate`（见上文导入规则），因此不做截断修正，保持渲染器原口径，入点偏差由 QA 剪辑点检查按解码出的实际帧时间报警。所有流从同一非零时间开始的素材（如 MKV 整体偏移 0.5 s）零点就是视频起点，照常记录帧率并修正，实测修正后第 0 帧正确（`tests/source-start.integration.mjs`）。

**局限**：
- HDR（HLG/PQ 10-bit）在 `hdrMode: 'force-sdr'` 下可以出画（矩阵中纯红 HLG 素材渲染为红色），但没有做色调映射，也没有验证色彩准确性。
- 可变帧率素材可以渲染，但不记录 `frame_rate`，不做截断修正。
- 矩阵只用了合成纯色素材和正弦音，没有覆盖真实 iPhone 文件中的额外数据轨（如 `mebx` 元数据、`tmcd` 时间码）、杜比视界或超长素材。

可选集成测试（需要真实 Chrome）：`tests/render-size.integration.mjs`（128×72 画布导出与预览经 2 倍截图缩回 128×72、左红右蓝素材第 0 帧左右颜色正确、字幕在缩回后仍可见、QA 分辨率检查通过；1280×160 画布预览为 640×80；3840×88 画布预览以导出截图 3840×88 缩回 640×14；QA 按回执记录的输出尺寸判定，模拟的旧 704×88 预览通过，回执缺尺寸时退回当前规则并注明）、`tests/source-start.integration.mjs`（媒体时间零点与 `frame_rate` 规则，MKV 与 MP4 edit list；夹具无法按预期构造时测试失败并给出 ffprobe 读数，不跳过）、`tests/frame-alignment.integration.mjs`（模拟 0.6.0 工程：负音频起点 MKV 上手工写入 `frame_rate`，渲染不修正、回执与 QA 记录原因、工程文件不变；删去回执中的 `frame_alignment` 后 QA 按旧渲染“全部已应用”判定并标注 `legacy-default`）、`tests/render-concurrency.integration.mjs`（同进程两路并发渲染，红/蓝素材各自的颜色覆盖整帧）、`tests/font-render.integration.mjs`。

## 创建工程

`create` 按 spec 格式决定工程格式：v2 spec（`tracks/items`）产出 v2 工程。v2 spec（媒体路径相对于命令 cwd）：

```json
{
  "project_id": "talk-broll",
  "title": "口播 + B-roll",
  "canvas": { "width": 1280, "height": 720, "fps": 24 },
  "assets": [
    { "id": "talk", "path": "/absolute/path/to/talk.mp4" },
    { "id": "music", "path": "/absolute/path/to/music.m4a" }
  ],
  "tracks": [
    { "id": "v_main", "kind": "video", "locked": false, "name": "主轨" },
    { "id": "a_music", "kind": "audio", "locked": false },
    { "id": "c_sub", "kind": "caption", "locked": false }
  ],
  "items": [
    { "id": "talk1", "track_id": "v_main", "kind": "media", "asset_id": "talk", "start_frame": 0, "frames": 48, "source_in_seconds": 0, "volume": 1, "fit": "cover" },
    { "id": "bed", "track_id": "a_music", "kind": "media", "asset_id": "music", "start_frame": 0, "frames": 48, "source_in_seconds": 0, "volume": 0.2 },
    { "id": "cap1", "track_id": "c_sub", "kind": "caption", "text": "第一句字幕", "link": { "item_id": "talk1", "source_from": 0.2, "source_to": 1.5 } },
    { "id": "title", "track_id": "c_sub", "kind": "caption", "text": "标题", "start_frame": 24, "frames": 24 }
  ]
}
```

```sh
node cli.mjs create /absolute/new-project spec.json
node cli.mjs read /absolute/new-project
node cli.mjs preview /absolute/new-project /absolute/new-preview 1
```

旧 v1 spec（`clips/audio`，片段按数组顺序连续拼接、字幕 `from/to` 为源秒）仍创建 `local-edit.v1` 工程，与 0.1.0 行为一致，宿主原有的 `edit <project> <revision> operations.json` 流程不变；首次提交 v2 编辑批次时按下文迁移规则升级（`tests/host-compat.test.mjs` 覆盖这条宿主路径）。创建会 ffprobe 输入、复制素材并记录 SHA-256，不修改源文件；工程目录必须不存在。P2 字段（变速、转场、淡变、闪避、图形）只在 v2 工程中可用；不支持自动语音分句。

## Agent 有界编辑（批次 v2）

先 `read` 当前修订，再提交批次文件：

```json
{
  "base_revision": 1,
  "author": "agent",
  "summary": "补导入 B-roll 叠在主轨上",
  "operations": [
    { "type": "add_asset", "id": "broll", "path": "/absolute/path/to/broll.mp4", "origin": { "kind": "generated", "provenance_ref": "jobs/broll.json" } },
    { "type": "add_track", "track": { "id": "v_broll", "kind": "video", "locked": false }, "index": 1 },
    { "type": "add_item", "item": { "id": "over", "track_id": "v_broll", "kind": "media", "asset_id": "broll", "start_frame": 12, "frames": 24, "source_in_seconds": 0, "volume": 0, "transform": { "x": 0.75, "y": 0.25, "scale": 0.4 } } }
  ]
}
```

```sh
node cli.mjs edit /absolute/project batch.json --dry-run   # 只返回 diff，不写任何文件
node cli.mjs edit /absolute/project batch.json
node cli.mjs render /absolute/project /absolute/new-export 2
```

操作（字段之外的键一律拒绝）：

| 操作 | 字段 | 说明 |
| --- | --- | --- |
| `add_asset` | `id, path, origin?` | 工程创建后补导入（含生成镜头）；默认 `origin.kind = import` |
| `add_track` | `track, index?` | 插入位置即叠放顺序，默认置顶；`locked` 缺省 false |
| `edit_track` | `track_id, locked?, name?, duck?` | 锁定/解锁/改名；`duck` 为对象时设置、为 null 时清除自动闪避（锁定轨道不能改 duck） |
| `add_item` | `item` | 完整 item（含 `kind: "graphic"`）；不能放进锁定轨道 |
| `remove_item` | `item_id, ripple?` | 同时删除链接到它的字幕；`ripple` 把同轨后续 item 前移 |
| `move_item` | `item_id, track_id?, start_frame?` | 只能移到同类轨道；link 字幕只能改轨，不能改起点 |
| `trim_item` | `item_id, head_frames?, tail_frames?, slip_seconds?` | 正数剪掉头/尾、负数延长；剪头同步推进源入点；`slip_seconds` 只移源入点、时序不变 |
| `split_item` | `item_id, at_frame, new_item_id` | 在输出帧处切开，后半段取新 id 并顺延源入点 |
| `replace_media` | `item_id, asset_id, source_in_seconds?, captions?` | 保持时序；未给 `captions` 时移除旧 link 字幕；`captions` 为 `{id, track_id, text, style?, source_from, source_to}` |
| `set_item_props` | `item_id, props` | `volume/fit/opacity/transform/text/style/speed/fade_in_frames/fade_out_frames/transition_in/vars`；值为 null 表示移除（volume/text/vars 不可移除） |
| `revert_to` | `revision` | 以旧修订内容发布新修订，**必须单独成批** |
| `rebind_template` | `template` | 把该模板的绑定升级到当前执行层模板字节，**必须单独成批**；模板未被任何 graphic 使用、当前执行层字节与本修订实际渲染所用字节相同（已绑定该字节，或本修订是未绑定的历史修订）即无变化、或使用该模板的 graphic 位于锁定轨道时拒绝 |

规则：

- **整批原子**：先在内存中按序应用全部操作并对结果做完整 `validateV2`，任一失败则不复制素材、不发布。`base_revision` 不是最新修订直接拒绝（需重读），不自动合并。发布沿用硬链接无替换写入，并发写只有一个成功。
- **dry-run** 返回 `diff`：新增/删除/变更的 item id、轨道变化、新增素材 id、新旧成片帧数、模板绑定变化 `graphic_templates {added, removed, changed}`；`add_asset` 只 ffprobe 探测，不复制；不复制模板文件。批次结果另有 `notes`（如历史修订首次获得模板绑定的说明）。
- **锁定轨道**：锁定轨道上的 item 不能被修改、删除或作为移动目标；`split/replace_media/remove_item` 需要改动的 link 字幕所在轨道也必须未锁定。link 字幕的存储数据不变，只随其 media item 的位置自然换算，这不算修改。`revert_to` 若会改变当前任一锁定轨道上的 item（或目标修订缺少该轨道）也被拒绝。锁定轨道上的 graphic 所用模板字节同样冻结：任何批次（`rebind_template`、`revert_to` 等）若会改变它们实际渲染所用的模板字节即被拒绝。锁定冻结的是该轨道自身的 item 与设置（含 `duck` 配置与名称）：`revert_to` 时锁定轨道整体保持当前定义，不被目标修订的轨道对象覆盖。锁定不冻结由被参照轨道派生的闪避包络——被参照轨道（如未锁定的口播轨）的 item 变化时，锁定音乐轨的实际音量曲线会随之重新计算。
- **split 的字幕归属（确定规则）**：link 字幕归属到**源区间起点 `source_from` 落在哪一半**（`source_from ≥ 切点源时间` 归后半，否则留在前半）。不复制字幕：跨越切点的字幕只在其所属那一半内显示相交部分，切点之后的部分不再显示；如需两半都显示，在后半段另加一条 link 字幕。
- **trim/move**：link 字幕按源时间自动跟随，不存输出时间；裁掉的源区间内的字幕自然不再显示。
- **P2 下的 split/trim/move（确定规则）**：
  - 变速：split 两半都保留 `speed`；后半源入点 = 原源入点 + 前半帧数/fps × speed。`trim_item` 剪头同样按 `head_frames/fps × speed` 推进源入点；`slip_seconds` 是源秒，不乘 speed。
  - 淡变与转场：split 后**前半保留 `fade_in_frames` 与 `transition_in`，后半保留 `fade_out_frames`**，新切点是硬切（前半去掉 fade_out，后半去掉 fade_in 与 transition_in）。原 item 若是下一个 item crossfade 的前驱，重叠落在后半上，后半长度须 ≥ 转场帧数。
  - trim/move 不自动改写淡变与转场：结果必须仍满足规则（淡变之和 ≤ 长度；crossfade 重叠恰好等于帧数），否则整批拒绝；需要时在同一批次里用 `set_item_props` 调整或删除 `transition_in`/淡变。
  - split 遇到淡变长于所在半段时整批拒绝（例如 fade_in 10 帧、在第 5 帧切），不做截断。
- **duck 变更不是锁定变更**：`edit_track` 只有改 `locked` 时必须单独成批；设置/清除 `duck` 可与其他操作同批。
- `change.operations_sha256` = 批次 `operations` 规范化 JSON（对象键递归排序、无空白、UTF-8）的 SHA-256。批次 `author` 只能是 agent/human/system（`migration` 保留给迁移）。
- 字幕字体：批次首次引入字幕时绑定固定字体（见下）；已绑定的工程每次编辑都校验新字幕字形覆盖。

## 图形模板

模板是执行层资源，位于 `templates/<id>.json`（`schema_version: creative-craft.graphic-template.v2`、整数 `version`、命名位置 `placements` 与 `default_placement`、带类型变量、固定 `html`/`css`），加载时逐项校验，不合格的模板直接使模块加载失败：

- `placements`：一个或多个命名位置（名称 `^[a-z][a-z0-9_]{0,31}$`），每个是一个 `box`（画布比例 left/top/width/height），**每个**都必须完整位于 5% 安全区内（left/top ≥ 0.05，right/bottom ≤ 0.95）；`default_placement` 必须是其中之一。
- 变量类型：`string`（`max_length` 1–200、`font_em`、`weight`，可选 `optional`）、`color`（`#rrggbb`）、`boolean`、`number`（`min/max`）；可选变量可带 `default`。`placement` 是保留变量名，模板不得声明。按最坏情况（每个字符 1 em 全角）对**最窄的位置框**校验 `max_length × font_em ≤ 100 × box.width × 0.95`，保证最长文本在任一位置都放得下。
- **最小字号**：任何文本变量渲染字号 ≥ 3 em = 画布短边的 3%（竖屏 1080 宽 ≥ 32.4 px，720 宽 ≥ 21.6 px）。加载时 `font_em` 小于 3 的字符串变量先被抬到 3 再做上面的放得下校验（抬高后放不下则加载失败）；CSS 里的字号只能写 `font-size:var(--fs-<变量名>)`，编译时由 `font_em` 生成 `--fs-<变量名>:<font_em>em`，且模板 CSS 不得出现 `font` 简写、`zoom`、`transform`/`scale` 属性（含厂商前缀）、`scale()`/`matrix()`、`font-size-adjust`/`text-size-adjust`、对 `--fs-*` 的再定义以及 CSS 注释与转义，因此 CSS 不能绕过该下限。说明：需求表述为“画布宽度的 3%”，竖屏与方形画布上两者相同；横屏若按宽度计（1920 宽需 57.6 px ≈ 5.3 em），现有模板的最长文本放不进框，所以统一按短边计，横屏实际下限为高度的 3%。
- `html` 只能含 `<span class="…">`（HyperFrames lint 会把计时元素内嵌套的块结构标为 warning），每个字符串变量以 `{{name}}` 恰好出现一次；`html`/`css` 禁止 script、事件属性、`url(`、`@import`、`src/href` 等；CSS 每条规则必须以 `.gfx-<id>` 作用域开头。
- 编译：字符串值 HTML 转义后填入；颜色/数字写成根元素内联 CSS 自定义属性（`--accent:#2f9e8f`），字号写成 `--fs-<name>`；布尔写成固定 `data-<name>="true|false"`；所选位置写成 `data-placement="<name>"`。不接受任意 HTML、URL 或脚本。根元素字号 = 画布短边 / 100 px（1 em = 短边 1%），各平台比例下同一模板文本相对尺寸一致；文本 `nowrap + ellipsis`，最坏情况仍在框内。
- 位置选择：graphic item 用保留变量 `vars.placement`（字符串，取该模板声明的位置名）选择位置；缺省为模板的 `default_placement`，与旧文档（无 placement）的位置一致。Node 校验 placement 必须是该模板的位置名（不是则拒绝并列出可选名）；Python 侧只校验 vars 为原始值，`placement` 是字符串，无需改动。`graphic-safe-area` 与采样都使用所选位置的框。
- 字体：图形与字幕共用已绑定的字幕字体（`.caption,.gfx` 同一 `@font-face`），存在 graphic item 时与字幕一样触发字体绑定、字形覆盖检查和运行时字重加载门槛。没有字体绑定却已有系统字体字幕的旧工程不能加图形（否则会改变原字幕字体），须新建工程。

当前模板（v2；与 v1 相比：位置可选；`lower-third` 副标题从 2.4 em 提到 3 em 以满足最小字号，框宽从 0.62 放宽到 0.78 以容纳最长副标题；默认位置不变）：

| id | 位置（placements，默认加粗） | 变量 |
| --- | --- | --- |
| `lower-third` v2 | **`bottom`** 左下 0.06/0.70，宽 0.78 × 高 0.20；`upper` 0.06/0.14，宽 0.78 × 高 0.20（高度 14–34%，避开底部烧录字幕与免责声明） | `title` 字符串 ≤16（3.6 em, 700）、`subtitle` 可选 ≤24（3 em, 400）、`accent` 可选颜色（默认 #e3b341） |
| `title-card` v2 | **`center`** 0.10/0.30，宽 0.80 × 高 0.40；`top` 0.10/0.08，宽 0.80 × 高 0.20（高度 8–28%，避开竖屏居中人脸） | `title` ≤12（6 em, 900）、`subtitle` 可选 ≤24（3 em）、`background`/`text_color` 可选颜色、`panel` 可选布尔（false 时面板透明） |

示例：`{"template": "lower-third", "vars": {"title": "主讲人", "placement": "upper"}}`。

## v1 工程兼容与迁移

`creative-craft.local-edit.v1` 修订保持可读、可渲染；对 v1 工程，旧 CLI 形式 `edit PROJECT EXPECTED_REVISION OPERATIONS.json` 与 `reorder/update_clip/replace_clips/set_audio` 行为不变。v2 工程收到 v1 操作时明确报错。

对 v1 工程首次提交 v2 批次时，先发布一个**纯迁移修订**（`change.author = "migration"`，不含任何编辑），再在其上发布本次编辑修订；旧文件不改写。迁移映射：clips → `v_main` 视频轨按顺序排列的 item（id 不变）；clip 内 captions → `c_main` 字幕轨 link 字幕（id 为 `cap1…`，避开已有 id）；audio → `a_bed` 音频轨 item（v1 允许重叠的音轨，重叠者依次放入 `a_bed_2…`）；assets 补 `origin.kind = "import"`。v1 音轨超出最后一个片段的部分在渲染时本就被截断，迁移把截断写实（完全落在片尾之后的音轨被丢弃），以免 v2 成片被拉长。smoke 实测迁移修订与原 v1 修订的导出逐帧画面 MAE 为 0、音频 RMS 相同。迁移修订与编辑修订分两次无替换发布：极端并发下若编辑修订冲突，已发布的迁移修订仍是合法且等价的 v2 版本。

## 渲染与 lint 关卡

渲染必须使用新的、工程目录外的输出目录；失败目录也不自动覆盖。输出 `project.json`、`index.html`、复制的素材、`captions.vtt`、`video.mp4` 和 `receipt.json`。多轨编译：视频轨按数组顺序叠放（显式 z-index，字幕始终在画面之上），每条轨道独立 `data-track-index` 通道；视频 item 的素材含音频且 volume>0 时输出独立 `<audio>`；音频轨 item 输出 `<audio>`；link 与非 link 字幕均生成 WebVTT。

**P2 编译映射**（按已安装的 `@hyperframes/*` 0.8.108 dist 实测，而非文档推断）：

- 变速：`<video>`/`<audio>` 写 `data-playback-rate="<speed>"`（core `readPlaybackRate` 读取并限制在 0.1–10；engine 抽帧按 `sourceTimeAt` 换算画面源时间，混音用 `atempo` 变速不变调）。`data-media-start` 仍是源入点。
- 音量：所有随时间变化的音量（淡入淡出、crossfade 两侧、闪避）合成为每个 `<audio>` 上**一条** `data-automation` volume lane，此时不再写 `data-volume`，也不生成任何 GSAP 音量补间，因此不会出现 `audio_volume_double_automation`。实测语法：`data-automation='{"version":1,"lanes":[{"target":"volume","points":[{"t":0,"v":0},{"t":0.333333,"v":1},…]}]}'`（HTML 属性内转义为 `&quot;`）；`t` 为**相对该元素 data-start 的秒数**（clip-local），`v` 为**绝对线性增益**（替代而非乘以 data-volume；engine `volumeLaneKeyframes` 把首点之前保持首值、末点之后保持末值，再逐样本乘入 PCM），点间线性插值，每条最多 512 点：`create` 与编辑批次（含 dry-run）用与编译相同的包络函数（`timeline.mjs` 的 `volumeEnvelope`）逐条计算，超出即拒绝并指明 item 与轨道，不会留到渲染才失败。音量恒定的 item 仍只写 `data-volume`（0.8.0 起，切入源中间的硬切边带 4 ms 微淡变，因此有可听音频的 item 通常都写 lane）。
- 包络计算：增益 = volume × 淡入斜坡 × 淡出斜坡 × crossfade 入（后一段 0→1）× crossfade 出（前一段 1→0；两侧为同一段源声音时线性等增益，否则 sin/cos 等功率，见“剪辑点音频”）× 剪辑点微淡变 × 闪避；在所有斜坡端点精确相乘，端点之间线性。闪避：参照轨上有声 media（volume>0 且素材有音频）的输出区间；相邻区间若“释放 + 下一次起音”会相接则合并；每段在说话开始前 attack 帧内降到 `10^(depth_db/20)`（时间线已知，提前起音），说话结束后 release 帧内回到 1；0 帧按 1 ms 斜坡处理以免爆音。
- 画面：有淡变/转场的视频与图形以 `opacity:0` 编写，再按包络生成首尾相接的 `tl.fromTo("#id",{opacity:a},{opacity:b,duration,ease:"none",immediateRender:false},t)`；首段之后的恒定段不再生成补间（完成的补间保持终值）；起点与 clip 边界一样提前 1 ns，时长再缩 2 ns，避免相邻补间被 lint 判为重叠。crossfade 时前一段保持不透明，后一段在上层 0→1，所以重叠中点是 50/50 混合。
- 同轨 crossfade 的两段处于重叠，会在 HyperFrames 中被判为同一 `data-track-index` 上的重复音轨，所以链式 crossfade 的 item 在两个“卷”之间交替：视频 `n`/`n+40`、声音 `100+n`/`140+n`，叠放（z-index）不变，后一段在 DOM 中位于前一段之后。
- 回执新增 `audio_limiter: {ceiling_dbtp: -1, engaged, audio_lowered_db, source: "RenderJob.audioLoweredDb"}`：producer 的 AAC 真峰值限幅只在需要压低整段混音时在 RenderJob 上写 `audioLoweredDb`（缺省即未触发，记为 0）。

编译 HTML 后用 `@hyperframes/lint` 的 `lintHyperframeHtml` 检查，按 `shouldBlockRender(strictErrors=true, strictAll=false, …)` 判定：存在 error 级发现即中止，回执 `failed`、不产出视频；结果（版本、计数、发现）写入 `receipt.lint`。v2 字幕带 `class="clip"`，编译结果无 lint 警告；v1 编译保持原样（字幕缺 clip 类会产生 warning，不阻断）。

回执还记录 `document_schema`、`revision_sha256`（工程修订文件摘要，QA 据此绑定修订）、`project_sha256`、`composition_sha256`。实际文件通过结构（含“工程有可听音频 ⇔ 输出有音轨”）与全文件解码检查后才能记为 completed；失败/取消有不同状态，半成品不应当作交付。SIGINT/SIGTERM 请求取消；强制杀进程可能留下 running 回执，重开不会把它升级为成功，也没有后台自动恢复服务。

预览是相同语义工程编译出的低分辨率 MP4（最长边最高 640），非交互式 HTML 编辑器。正式导出使用项目画布。每次固定工程 revision 和素材 hash；执行前、复制时均核验素材。

## 剪辑点音频（0.8.0）

硬切处两段波形不连续会产生咔哒声；真实口播为画面干净常把入点切在起音之后（约 20 ms）。0.8.0 在执行层（`timeline.mjs` 的同一包络函数，编译与 `create`/编辑批次校验共用）加入两项处理，并在 QA 中检查成片。两项都是执行层常量，**不是文档字段**，schema 与共享样例不变；改常量会改变所有修订的编译结果，需要随版本说明。

**剪辑点微淡变**（`CUT_DECLICK_SECONDS = 0.004`）：对每个可听 media item（volume>0 且素材有音频）的两条边分别判定：

- 边上已有显式淡变（`fade_in_frames`/`fade_out_frames`）或 crossfade（入边 `transition_in`、出边有 crossfade 后继）时不加，显式处理优先。
- 入边：`source_in_seconds > 0`（切进源素材中间）时加 4 ms 0→1 斜坡；`source_in_seconds = 0`（从素材自身起点开始，不是剪进波形）时不加，保留原始起音。源起点 0 是帧起点，源帧对齐不会修正它，所以校验与编译判定一致。
- 出边：没有显式淡变/crossfade 时一律加 4 ms 1→0 斜坡（包括用到素材末尾的 item：录音末尾 4 ms 的衰减听不出，规则也不依赖探测到的素材时长）。
- 拆分接缝不加：同轨首尾相接（前段结束帧 = 后段起始帧）、同一 `asset_id`、同一 volume 与 speed、两侧都是硬边（无显式淡变/crossfade），且源时间连续（后段 `source_in_seconds` ≈ 前段 `source_in_seconds` + 帧数/fps × speed，误差 ≤ 1 个源帧：素材有 `frame_rate` 时按它，否则按画布 fps），视为同一段波形继续播放，**两侧都不加**（`timeline.mjs` 的 `sourceContinuous`）。`split` 之后接缝处包络无下凹。
- 其余情况不看相邻是否有声音：从静音直接跳进波形中间、或在时间线末尾截断，同样是阶跃；轨道首尾、空隙两侧与同轨/跨轨相邻都用同一规则。
- 斜坡长度取 `min(4 ms, item 时长/2)`。4 ms：引擎把 lane 逐样本乘进 PCM（`applyVolumeEnvelopeToWav`，48 kHz 下 192 个样本），足以消除阶跃；又短于 5–10 ms 这一开始被听成“淡入”的量级，几乎不削起音（入点已削掉约 20 ms 时更不应再多削）。需要更长的柔化时用显式 `fade_in_frames`/`fade_out_frames`（按帧）。
- 每条硬切边增加 1 个 lane 点（斜坡端点；边界点本来就在 lane 中），计入 512 点上限。某条 lane 加微淡变后会超过 512 点时，**该 lane 不加微淡变**（不报错；其他 lane 照常），并在编译结果与渲染回执的 `declick.skipped_lanes`（`item_id`、`track_id`、`points`、`points_without_declick`）以及编辑批次结果（有跳过时的 `declick`）中记录；不加微淡变仍超过 512 点时拒绝。`create`/编辑批次（含 dry-run）与编译走同一函数（`volumeLane`）同一常量。测试可经 `envelopeIndex(doc, { declickSeconds })` 或 `compose(doc, canvas, { declickSeconds })` 注入（0 = 关闭）；渲染与校验不暴露该参数。
- 已发布修订：微淡变不改文档，但重新渲染 0.8.0 之前发布的修订时硬切处会多出 4 ms 淡变，音频与 0.7.0 渲染不逐字节一致（画面不变）；无需迁移文档。

**按源时间连续性选择 crossfade 曲线**（执行层规则，不是文档字段，schema 不变）：

- 两侧同一 `asset_id`、同一 speed，且重叠区间两侧播放的源时间一致（重叠起点处后段源时间与前段源时间相差 ≤ 1 个源帧，`sourceContinuous`）：视为相关信号（同一段声音），用**等增益**曲线，即线性互补（前一段 1→0、后一段 0→1，各 2 个 lane 点）：两侧振幅和恒为 1，相关信号中点不升高。单元测试中同一 400 Hz 素材源时间连续的两段 crossfade，中点功率与两端偏差 ≤0.5 dB。
- 其余（不同素材，或同一素材但重叠处源时间不同）：视为不相关信号，用下面的等功率曲线。

**等功率 crossfade**（`CROSSFADE_SEGMENTS = 8`，两侧不是同一段源声音时使用）：后一段 `sin(π/2·x)`、前一段 `cos(π/2·x)`，每侧用 8 段折线（9 个 lane 点，中点 x=0.5 是端点，取值精确为 0.7071）。折线在凹曲线下方，两侧功率和最多低约 (π/2N)²/4：N=8 时整个重叠区内最大偏差 0.042 dB（数值扫描；N=4 为 0.17 dB，N=16 为 0.01 dB 但每侧多 8 个 lane 点，8 段已远低于 0.5 dB 的验收线）。真实渲染（440 Hz 交叉进 660 Hz，6 帧）中点功率与两端相差 −0.004/−0.04 dB。不相关信号（两段不同的口播/音乐）功率保持恒定；不同素材之间如果实际是相关信号（例如两份同一录音的副本），中点仍会高约 3 dB。视频透明度不变：仍是后一段线性 0→1 叠在不透明的前一段上。

**QA：剪辑点咔哒**（`cut-point-clicks`，category audio，见 `audio-clicks.mjs`）：剪辑点 = 每个可听 item 的起点与终点（严格在 0 与成片时长之间，同一时刻合并并列出全部 item 与 in/out）。对成片音轨**一次顺序解码**（单声道 48 kHz；不按剪辑点 `-ss` 跳读：ffmpeg 9.0.1 对 AAC 输入跳读会早落约一个 1024 样本的帧，点击会被移出窗口），对每个剪辑点取二阶差分 `|x[n] − 2x[n−1] + x[n−2]|`：阶跃时它与阶跃同量级，平滑内容随 (2πf/48000)² 衰减（440 Hz 只有振幅的 0.3%）。窗口内（±10 ms）峰值 ≥ 两侧各 50 ms 参照环峰值的 **6 倍**，且绝对值 ≥ **0.02**（−34 dBFS），记该点为咔哒，任一点 → warn，`refs` 列出时间与 item；否则 pass；无可听剪辑点 not_applicable，无音轨 unknown/not_applicable。±10 ms 窗口不完全落在解码出的音频内（剪辑点超出音频末尾，例如音频短于画面的成片）时该点无法判定，记 `unknown`（无咔哒时整项为 unknown 而不是 pass，observation 列出这些点）；解码失败或超时则整项 unknown 并写明原因，其余 QA 检查照常输出（`clickCheck`）。`measured.cut_points` 记录每点的 peak、context、ratio、peak_dbfs（无法判定的点为 `click: null` 与 `unknown` 原因）。

- 阈值实测：合成 440 Hz 相差 1/4 周期的硬拼接，经 AAC 后 ratio 约 270–310、峰值 0.13–0.53；同相位反转（只有斜率不连续）约 10；2 kHz 阶跃 8–14。开启 4 ms 微淡变后 ratio 约 2–2.6、峰值 ≤ 0.004。两段 4 ms 斜坡在剪辑点相接时二阶差分最大为 2/192 ≈ 0.0104（满幅），低频满幅音的 ratio 可达 30，所以绝对下限取其两倍 0.02。真实素材误报率：`byq-foundation-02` 源音频（137 s 口播与环境声）以 10 ms 步长扫描 13 680 个位置，6 倍/0.02 下 6 个位置（0.04%）被判为咔哒（源内瞬态，如爆破音），4 倍/0.01 下 19 个，所以取 6 倍。
- 真实素材复验（`byq-foundation-02` 修订 3，临时副本渲染预览后 QA，只读）：3 个剪辑点 ratio 0.67/1.32/0.63（峰值 −28/−17/−25 dBFS），pass；0.7.0 时的同修订预览（无微淡变）为 0.94/1.25/2.77，同样无咔哒（剪辑点落在停顿或低电平处）。
- 可选集成测试（真实 Chrome）：`tests/audio-clicks.integration.mjs` 渲染 1/4 周期错相的硬切与一段等功率 crossfade：QA `cut-point-clicks` pass（ratio 1.9/0.6/0.9），crossfade 中点功率偏差 ≤0.5 dB；把同一成片的音轨换成无淡变的硬拼接（并改写回执摘要）后 warn，引用 1.0 s 的两侧 item 与 2.0 s 的频率跳变（ratio 约 307/136）。
- 局限：启发式，不是听检。剪辑点 ±10 ms 内恰有爆破音、打击乐、噪声起始时可能误报（音乐素材比口播更容易）；剪辑点两侧本身有更强高频内容时，被掩蔽的咔哒不报；只看可听 item 的边，素材内部的咔哒不检查；立体声先混为单声道（左右反相的阶跃会抵消）。

## 技术检查（QA）

```sh
node cli.mjs qa /absolute/project /absolute/render-dir /absolute/new-qa-dir [--caption-band 0.62:0.86] [--scene-threshold 0.3] [--production /absolute/production] [--analysis /absolute/analysis.json]（每个素材一个 `--analysis`，可重复） [--decisions /absolute/applied.json]
```

可选参数：`--caption-band TOP:BOTTOM` 覆盖烧录字幕带（源画面高度比例，默认 0.62:0.86，带高 ≥ 0.05）；`--scene-threshold N` 覆盖成片镜头检测阈值（0–1，默认 0.3）；`--production DIR` 是 production.json 所在目录，写进同时生成的审片报告页的签字命令（与 `review-page --production` 相同；不给时签字命令里留 `<production>` 占位）。模块调用为 `qaRender(root, renderDir, qaDir, { captionBand: {top, bottom}, sceneThreshold, production })`。

读取渲染目录回执与工程快照：回执必须 `completed`，`revision_sha256` 与工程修订文件一致，快照与修订内容一致，视频 SHA-256 与回执一致；否则拒绝检查。QA 目录必须是新目录且在工程外。生成符合 `render-qa.schema.json` 的 `qa.json`，并同时写出审片报告页 `review.html`（见“审片报告页”）：

- **structure**：时长与修订帧数相差 ≤1 帧（取视频流时长）、分辨率（导出=画布，预览=缩放尺寸）、帧率、音轨（工程有可听 item 而无音轨为 fail）。
- **video**：ffmpeg `blackdetect`（d=0.5, pix_th=0.10）与 `freezedetect`（-60dB, d=2）。与时间线空隙重叠的部分视为预期黑场/静止，只有落在有画面区间内的 >0.5 s 黑场、>2 s 静止记 warn。
- **audio**：`silencedetect`（-50dB, d=2）只统计工程有声音区间内的 >2 s 静音（warn）；`ebur128=peak=true` 积分响度超出 -14±3 LUFS 记 warn，真峰值 > -1 dBTP 记 warn。真峰值检查的 `measured` 同时引用回执的限幅证据：`audio_lowered_db`、`limiter_engaged`、`limiter_ceiling_dbtp`（旧回执无记录时为 null，observation 注明）。无音轨时为 unknown/not_applicable。剪辑点咔哒检查见“剪辑点音频（0.8.0）”。
- **captions**：每条可见字幕在显示区间中点采样合成帧，帧存在记 pass（不判断文字是否可读）。
- **安全区**（`caption-safe-area`，category captions；`graphic-safe-area`，category video）：在字幕采样帧与图形中点采样帧上检查元素框是否距四边 ≥5%，都不是像素检测。图形（`measured.method = template-load-guarantee`）：框即模板框，模板加载校验已保证其在安全区内，该检查只是把这一保证记入 QA 并给出采样引用，observation 明确写明“由模板加载校验保证、非像素检测、不测量文字是否放得下”；不再做文字截断估算。字幕（`compiled-layout-estimate`）**按编译布局计算**：按编译 CSS 推算（默认样式：7%–93% 宽、底边 8%、行高 1.35、8 px 内边距；显式样式：以 centerY 为中心、行高 1.1、加描边），文本宽度按字符估算（全角 CJK/符号 1 em、其他 0.55 em、空格 0.3 em）推算换行行数。越界 → fail。`measured.boxes` 记录每个框。局限：字宽为估算，不是浏览器实测；不检测画面内容本身（如素材里已有的贴边文字）；图形检查不提供模板加载之外的新证据。
- **lint**：引用渲染回执的 lint 结果（error→fail，warning→warn，旧回执无结果→unknown）。
- **烧录字幕剪辑点**（`burned-caption-cut-points`，category captions）：素材自带的烧录字幕常比语音晚切换，按语音间隙选的入点可能仍显示被剪掉那句的字幕。对视频轨每个 media item 的**源入点与源出点**，在**源素材**上解码附近帧（灰度、短边缩到 360 px），检测字幕带（默认画面高度 62%–86%）的“阶跃”变化：
  - 判据：某像素在变化前 3 帧内稳定（极差 ≤ 12 灰度级）、变化后 3 帧内也稳定，且均值变化 ≥ 40，记为阶跃像素。烧录字幕在两次切换之间静止、在一帧内整体切换，字形像素会同时阶跃；手、脸、运镜不稳定，不产生阶跃。在带内取一行字幕高的窗口（画面高度 5%），阶跃像素占比 ≥ 10%，且其中“亮字形”阶跃（变化前或后的均值 ≥ 200，即白/黄字）占比 ≥ 5%，判为字幕变化。若同一时刻带外整帧平均绝对差 ≥ 30（灰度级），判为整帧镜头切换，视为对齐，不算字幕变化。
  - 剪辑点按编译视图的入点判断（见“源素材帧对齐”）：素材带 `frame_rate` 时，低于帧起点不超过 2 ms 且不足 0.1 帧的截断入点已在编译时修正，不再出现下面所述“截断入点显示上一帧”的情形（低于帧起点更多的入点仍按渲染器口径判断）；其余入点与无 `frame_rate` 的素材按以下口径判断。
  - 显示帧口径与渲染器一致：输出第 j 帧显示源时间 `入点 + j × 速度/fps` 处、时间戳 ≤ 该时间的源帧。所以入点显示的是“时间 ≤ 入点”的那一帧——写成 24.4333 的入点（略小于 733/30 = 24.433333…）仍显示第 732 帧；出点（不含）之前最后显示的是“时间 ≤ 出点 − 速度/fps”的帧。比较严格按此口径：入点哪怕只比某帧起点早 1e-7 s 也判为显示前一帧，容差只有 1e-9 s（吸收浮点误差，不向后放宽）。源帧时间不读 showinfo 打印的 `pts_time`（小数位随 ffmpeg 版本变化），而是用每帧的整数 `pts` × ffprobe 读到的视频流 `time_base`，减去各流 `start_pts × time_base` 的最小值（媒体时间零点，同 data-media-start），与 ffmpeg 版本无关。
  - 入点：入点帧之后、入点后 ≤0.5 s（源时间）内出现字幕变化，而入点帧本身不是变化帧 → warn（入点时仍显示上一行字幕）；入点帧正好是变化帧记 aligned。出点：出点前 ≤0.5 s 内、仍会显示的帧上出现字幕变化，而出点后第一帧不是变化帧 → warn（下一行字幕在出点前闪现）；变化帧正好是出点后第一帧记 aligned。已对齐在**字幕**变化帧上的边，窗口内侧再有一次变化**不报 warn**（入点：那是下一行；出点：那是正在说的这一行的换行，移过去会切掉它的语音，与 `suggest-cuts` 一致）：结果仍为 aligned，在该点记 `short_line: {source_seconds, frame_mid_seconds, shown_seconds}`（离边最近的那次变化与边上这行显示的时长），observation 末尾写明这类短行的数量与位置，供审片人看一眼。边上只是整帧镜头切换（`kind: shot`）**不算字幕对齐**（新镜头可能延续上一行字幕）：内侧有字幕变化时照旧 warn，该点另记 `edge_on_shot_change: true`，observation 提示“这类 warn 可能只是新一行随镜头切换开始，请目测”。真实素材（`byq-cushion-05` 修订 1）：hook 出点 60.116666 s（出点后第一帧是 60.1 s 的字幕变化，59.633 s 的变化是当前句换行）原来报 warn，现在记为 aligned + `short_line`；test 入点 111.683333 s（入点帧是镜头切换，0.4 s 后字幕再变）仍报 warn，带 `edge_on_shot_change`。入点/出点都不在变化帧上、窗口内有变化的情形仍报 warn。`suggested_source_seconds` 是**变化后首帧的帧中点**（该帧与下一帧时间的中点，按源素材帧率，保留到微秒、不再截成 4 位小数）：作入点时首帧就是变化帧，作出点时最后显示的是变化前一帧；写在帧边界或截成 4 位小数的时间可能落在目标帧之前、仍显示上一帧，帧中点没有这个问题。`measured` 记录 `method`、字幕带、阈值和每个剪辑点（item、in/out、源时间、成片时间、结果、附近的字幕变化与镜头切换、`suggested_source_seconds`/`suggested_shift_seconds`）；`refs` 指向成片剪辑点时间、item 与剪辑点采样帧。
  - 阈值实测（`byq-cream-01` 真实口播/实测/促销素材，竖屏 1080×1920 30 fps，只读）：人工核对过的字幕切换 `line_share` 0.11–0.41、亮字形占比 0.066–0.19；手和刷子掠过字幕带的误检 `line_share` 可达 0.12，但亮字形占比 ≤ 0.023，所以亮字形判据取 0.05；真实镜头切换的带外平均差 41–133，同一机位的跳切（字幕同时切换）约 17，所以镜头阈值取 30。在该素材修订 1 上，recap 入点（源 31.47 s）被 warn 并建议 31.60 s；修订 2（入点 31.60 s）记为 aligned，全片 8 个剪辑点无 warn。smoke 中无字幕的测试图案素材不报。
  - 局限：这是帧差启发式，不是 OCR：不能读字幕内容、不能判断字幕与语音是否对应；只识别亮色（白/黄）字幕，深色或彩色字幕、字幕带外的字幕会漏报；字幕淡入淡出、滚动字幕不是一帧阶跃，可能漏报；字幕带内持续静止后突然变化的亮色画面元素（如贴纸、产品特写）可能误报；字幕消失（变为空白）通常不触发。窗口在源时间上计（变速 item 同样按源秒 0.5 s）。无字幕素材应基本不报。解码失败、解码帧数与 showinfo 帧行数不一致、帧行缺少整数 `pts` 或帧尺寸、showinfo 输入时间基与流时间基不符（帧时间不可信）的剪辑点记 unknown，错误写明缺失的字段；解码用 `-fps_mode passthrough`，变帧率素材每帧对应自己的源时间。汇总：任一剪辑点 warn → 检查 warn；否则任一 unknown → 检查 unknown（observation 写明未检查的数量、剪辑点与原因）；全部分析完且无 warn 才 pass。剪辑点窗口默认 4 路并发解码。
- **剪辑点相邻镜头碎片与压暗过渡**（`cut-boundary-fragments`，category video）：入点比源素材自己的镜头切换略早，成片开头会带上一个镜头的尾巴（真实素材：入点 22.68 s 而源镜头 23.23 s 才切换，开头 0.55 s 是旧镜头；入点 24.4333 s 略小于 733/30，第 0 帧是旧镜头末帧）；入点落在闪白转场里，开头是几帧白场；出点比源切换略晚，结尾会闪出下一个镜头的开头。对视频轨每个 media item 的源入点与源出点，在**源素材**上解码前后各约 1.5 s（灰度、短边 360 px）。两项剪辑点检查共用一次遍历（`cut-checks.mjs`）：每个剪辑点只解码一次，范围取两项检查所需窗口的并集，各检查只判断自己窗口内的帧；每个源文件只 ffprobe 一次；状态、observation 与 refs 的汇总规则由同一函数 `summarizeCutChecks` 产出，逐帧算整帧平均绝对差 MAD 与平均亮度：
  - 镜头切换判据（阈值与现有检查一致，写入 `measured.thresholds`）：MAD ≥ `shot_mad` = 30（烧录字幕检查的整帧镜头阈值，灰度级），且满足其一：MAD 比上一帧跃升 ≥ `scene_jump` = 场景阈值 × 100 = 30（与成片镜头检测 `--scene-threshold 0.3` 同口径：ffmpeg 场景分数即 min(MAD, ΔMAD)/100），即从运动中突出的硬切；或平均亮度阶跃 ≥ 30，即闪白/淡变帧。快速运镜 MAD 高但平稳、亮度不变，不算切换；ffmpeg 场景分数漏掉的闪白转场（真实素材 126.77–127.00 s）在进、出闪白时亮度阶跃，可以检出。
  - 判定（显示帧口径同上一条）：入点帧之后、入点后 ≤1.0 s 内（且在 item 内）有切换时，只有入点所在镜头**有一部分在入点之前**（入点不在该镜头首帧），且它**大部分在 item 之外**（入点前的部分长于 item 内显示的部分；向前 1 s 内没有切换即视为更长）或该镜头短于 0.5 s（闪场），才记 warn「开头含相邻镜头碎片 N 帧」，`suggested_source_in_seconds` = 切换后首帧的帧中点；紧随其后的短于 0.5 s 的镜头（闪白的出场）一并跳过，`kind` 记 `flash`。出点前 ≤1.0 s 内、仍会显示的帧上有切换时，只有出点所在镜头**有一部分在出点之后**（出点后第一帧不是下一次切换），且大部分在出点之后或短于 0.5 s，才记 warn「结尾含下一镜头碎片 N 帧」，给出 `suggested_frames`（保留到切换前末帧的输出帧数）、`drop_output_frames` 与 `suggested_source_out_seconds`（切换帧的帧中点，作出点时最后显示切换前一帧）。入点帧正好是切换帧（含入点写在该帧帧中点）、或切换帧正好是出点后第一帧，记 aligned：从首帧起显示的镜头（入点前没有它的部分）或显示到末帧的镜头（出点后没有它的部分）即使短于 0.5 s 也是完整的剪辑选择，不报。帧数口径：`fragment_frames` 是**成片**中显示碎片的输出帧数（按渲染器口径，第 j 个输出帧显示源时间 `入点 + j × 速度/画布 fps` 处的源帧，已计入变速与源/画布帧率差异），`source_frames` 另列碎片跨越的源帧数。observation 与建议中的时间一律是帧中点、6 位小数（出点碎片同时给出切换帧帧中点 `change_mid_seconds`；`change_seconds` 是切换帧起点，只作测量记录）。`measured.points` 记录每个剪辑点的源时间、成片时间、结果、附近切换时间与建议；`refs` 指向 item、成片剪辑点时间与剪辑点采样帧。
  - **压暗/黑场过渡（dip）**：同一次解码上按 `analyze` 的 dip 判据（`lumaDips`，阈值记入 `measured.thresholds.dip`；剪辑点外侧窗口放宽到 1.5 s，让整段 dip 两侧的稳定亮度都在解码范围内）找源素材 dip。入点首帧、或出点前最后显示的帧是 dip 的压暗帧 → warn（没有碎片时 `kind: dip`），该点记 `dip: {start_seconds, min_seconds, end_seconds, ref_luma, min_luma, output_frames, output_duration_seconds, suggested_source_seconds}`：`output_frames` / `output_duration_seconds` 是成片里处于淡入/淡出的输出帧数与时长，`suggested_source_seconds` 是第一帧恢复帧（入点）或第一帧压暗帧（出点）的帧中点；observation 写成片时间、淡入/淡出时长与 dip 区间。真实素材（`byq-cushion-05` 修订 1）：wear 入点 124.95 s（成片 10.333 s）报 warn，开头 6 帧（0.2 s）从黑场淡入，建议入点 125.15 s。
  - 真实素材复验（`byq-foundation-02`，只读）：修订 1 报 hook 入点 17 帧碎片（建议 23.25 s）与 cta 入点闪场 2 帧（建议 127.016667 s）；修订 2 报 hook 入点 1 帧碎片（建议 24.45 s）；修订 3 不报（hook 出点前 0.88 s 的同人跳切是 0.93 s 的完整短镜头，只少 1 帧，不算碎片）。`byq-cream-01` 修订 2 不报。
  - 局限：帧差启发式，不理解画面内容：低于阈值的同机位跳切、缓慢叠化不检出（dip 只认“压暗再亮起”，不认叠化）；大面积快速亮度变化（如闪光灯）可能误报为闪场。窗口在源时间上计。解码失败的剪辑点记 unknown；汇总规则同烧录字幕检查（任一 warn → warn，否则任一 unknown → unknown）。
- **剪辑决定（`--decisions APPLIED.json`，0.13.0）**：`apply-cuts` 的输出列出每个已定的冲突（`decisions`：`beat`、`edge`、`asset_id`、`option`、`by`＝`prefer`（BEATS.json 事先决定）或 `choice`（`--choose`）、`frame`、`seconds`、`accepts`）。`keep_speech` 的 `accepts` 是它在保留的那一帧上为保住语音而接受的那条剪辑规则（`caption` 字幕、`shot` 镜头碎片、`dip` 压暗过渡；`suggest-cuts` 记在该选项上，只记从这一帧移走的那一步，之后的移动发生在别的帧上、不算），其他选项为 `[]`。QA 给了 `--decisions` 时，`burned-caption-cut-points`（规则 caption）与 `cut-boundary-fragments`（镜头碎片/闪场为 shot，压暗为 dip，两者兼有则都要）里某个剪辑点的警告，若同一 item 同一边、同一素材有决定、源时间仍相同（半个输出帧 + 半个源帧之内：item 长度取整到输出帧会让出点偏移至多半个输出帧）且 `accepts` 覆盖该警告的全部规则，则记为 `accepted`（`accepted: {by, option, rules}`），不计入 warn；observation 写明哪些已按决定接受，审片页显示“已接受（保留整句，BEATS.json 事先决定）”。剪辑点之后被改过（时间对不上）、或选项不接受这类问题时照常 warn；`caption-speech-sync` 不由剪辑决定接受（保住语音并不等于接受字幕与口播错位）。以下都报错、不静默当作“没有可接受的”：文件不是 apply-cuts 输出或没有 `decisions`（0.13 之前）；某条决定字段不全或类型不对；`accepts` 为 null（由 0.13 之前的 suggest-cuts 结果得到，需重跑 suggest-cuts 与 apply-cuts）；决定的 item 在本修订中不存在，或它现在用的是另一个素材。v1 工程按迁移后的 item 对应。真实素材（`byq-velvet-03`）：收尾段两处 `prefer: keep_speech` 接受的镜头碎片记为 accepted，`cut-boundary-fragments` 由 warn 变为 pass，`caption-speech-sync` 仍 warn。
- **字幕与口播同步**（`caption-speech-sync`，category captions，0.11.0，只在给了 `--analysis` 时运行）：入点开头画面上的烧录字幕，是不是入点之前那句口播的字幕（成片开口说新的一句，屏幕上还是上一句）。帧差检测读不出字，而且字幕在手部动作、渐变中换行时它会漏检切换时刻，所以这里不依赖切换时刻，直接比较字幕带：取入点显示的第一帧，与入点前 1 s 内最后一段**已说完**的口播（≥ 0.15 s，ASR 短语来自 `--analysis`；入点落在某句话中间时那句就是开口的话，不算“之前的口播”）中间的一帧，各自算“描边亮笔画”掩码（灰度 ≥ 200 且 2 px 外有 ≤ 70 的暗边：烧录字幕是浅色字加深色描边/阴影；短边 360 px），两帧都有文字（笔画占字幕带 ≥ 0.3%）且入点帧的笔画有 ≥ 80% 在前一帧 ±1 px 内也有 → warn。每个点记 `coverage`、`text_share_cut`、`text_share_earlier`、`earlier_speech`、`earlier_sample_seconds`、`opening_speech`（入点所在的那句或入点后 1 s 内开始的一句；都没有为 null，说明开口处没有口播）；出点、没有分析的素材记 `not_applicable`（`reason`），不为它们解码、解码失败也不记 unknown、不计入 observation 的计数（没有分析的入点数另附一句）；入点前 1 s 内没有说完的口播或任一帧没有文字为 `clear`（`reason`）。与另两项剪辑点检查共用同一次解码。
  - `--analysis` 可重复，每个文件是 `analyze --asr`（或 `--transcript`）的输出，按其 `media.sha256` 对应工程素材；不是本修订素材、同一素材给两次、没有 ASR 短语都报错（静默跳过会被当成通过）。每条短语须有数值 `start` < `end` 与文字，否则报错（坏短语会让每个入点都静默通过）；这些校验在写任何证据之前完成。没有任何可判断的入点时该项为 `not_applicable`。
  - 标定（5 条 30 fps 真实整片，只读；每个 ASR 短语起点前 0.1 s 当作入点，两帧都有文字的 427 个）：按 `coverage` 分段各随机抽 6 帧人工看字：≥ 0.9 → 6/6 是前一句的字幕，0.8–0.9 → 4/6（一处其实已换行，一处是图形标签），0.7–0.8 → 2/6，0.6–0.7 → 1/6；不同的字幕行在同一位置约有一半笔画重合。有文字的帧笔画占比 0.4–4.0%，没有文字（转场、手机画面、手挡住）0.00–0.07%。真实工程（`byq-cushion-05` 修订 1）：质地段入点 `coverage` 0.91 报 warn（画面仍是“你看”，口播已是“哇哦”），其余三个入点 0.48–0.68 不报。
  - 局限：比较笔画，不是 OCR；无描边的浅色字、彩色字、标题图形可能被当成没有文字或误判为同一行；只看入点（出点“最后一句的字幕来不及出现”与“字幕已合并在前一行”分不开）；标定时约六分之五判对，审片页提示目测。
- **按镜头采样**（`shot-sampled`，category video）：对渲染成片做镜头检测（ffmpeg `select='gt(scene,T)'`，T 默认 0.3，可配置），把成片切成镜头；每个镜头若已有采样帧（item 中点、剪辑点、字幕）则不重复，否则在镜头中点加一帧 `reason: "shot"` 的采样，短镜头（<1 s）同样覆盖。`measured.shots` 记录每个镜头的起止与采样 id；有镜头取不到帧记 fail。局限：crossfade/淡变等渐变转场不产生场景分数峰值，渐变中的镜头边界由剪辑点采样覆盖；阈值以下的跳切（同机位小变化）不单独成镜头。

采样合成后的成片帧（不是源素材帧）：每个 media 与 graphic item 中点、每个视频剪辑点前后各一帧、每条字幕中点、每个尚无采样的镜头中点，PNG 写入 `frames/` 并记 SHA-256。采样按帧号精确提取：粗定位到目标帧前 2 帧后，用 `-copyts` 保留原时间戳、`select='gte(t, (n−0.5)/fps)'` 取第 n 帧并 `-fps_mode passthrough` 原样写出（单纯 `-ss <秒>` 在剪辑点附近会差一帧）；`time_seconds` 记录该帧的帧中点时间 `(n+0.5)/fps`，`s-cut<n>-before`/`s-cut<n>-after` 分别是剪辑点前最后一帧（n−1）与剪辑点后第一帧（n）。用 ffmpeg `tile` 把采样按时间顺序拼成 `contact-sheet.png`：最多 40 张（镜头多于 40 个时为镜头数），超出时先保证每个镜头一张，再均匀抽取其余采样；每个剪辑点前后各 1 秒导出 `clips/cut-<帧号>.mp4` 供听看。

`verdict`：任一 fail → fail；否则有 warn → pass_with_warnings；否则 pass。`review` 初始为 `{status:"pending", reviewer:null, decision:"pending", findings:[]}`，由 Agent 或人工依据采样填写；`unverified` 固定声明人工听检、创意质量、合成画面评审、字幕可读性未验证，以及烧录字幕检查只是帧差启发式、剪辑点咔哒检查只是二阶差分启发式。自动检查只反映技术信号：不检测音画同步、字幕与语音是否对应、画面内容是否正确，也不替代对合成画面的评审。

## 审片报告页（0.9.0）

`qa` 在写出 `qa.json` 的同时在 QA 目录写出 `review.html`：给审片人（剪辑、品牌负责人）看的单文件静态页，用浏览器直接打开（`file://`）即可，CSS/JS 全部内联，不加载任何外部资源（页面带 `default-src 'none'` 的 CSP，内联样式与脚本按哈希放行），不执行任何命令。评审填写 `qa.json` 的 `review` 之后，用下面的命令按当前 `qa.json` 重新生成：

```sh
node cli.mjs review-page /absolute/qa-dir [--video /absolute/render-dir/video.mp4] [--production /absolute/production-root]
```

- **只覆盖 `review.html`**：QA 目录的其他内容（`qa.json`、`frames/`、`clips/`、`contact-sheet.png`）是证据，从不改写；`review.html` 是由 `qa.json` 派生的查看方式，不是证据，评审写入 `qa.json` 后旧页面就过时了，所以允许原子替换这一个文件（临时文件 + rename；`review.html` 是符号链接或非普通文件时拒绝；与 `qa` 相同，QA 目录路径中含符号链接时拒绝）。`qa` 先写 `review.html`、最后发布 `qa.json`，因此存在 `qa.json` 即表示整次检查（含页面）已完成。页面脚注与内嵌的摘要 JSON 记录 `qa_id`、生成时 `qa.json` 的 SHA-256、修订摘要与生成器版本，可追溯到具体的 `qa.json` 字节。`qa.json` 的 schema 不变。
- **成片**：默认取 `qa.json` 的 `render.file`；QA 目录或渲染目录被移动/复制后用 `--video` 指定。页面以**相对 `review.html` 的路径**引用成片、采样帧、边界片段与缩略图墙；生成时核对成片 SHA-256 与 `qa.json` 是否一致，不一致或找不到文件时页面明确提示（找不到时跳转按钮不可用）。
- **页面结构**：头部摘要（工程、修订、预览/导出、时长、分辨率、帧率；结论框的主标题区分人工签字与评审（见下条“签字核对”），其下是自动检查结论与各状态计数，自动检查有失败项时另行醒目提示、不会被“接受”掩盖；积分响度与真峰值、评审状态与决定、成片 SHA-256 可展开复制）；主区左侧播放器、右侧「需要查看的问题」（全部 warn/fail/unknown 检查与评审 findings，按严重 > 失败 > 主要 > 警告 > 次要 > 未知、再按时间排序，每条带「跳到 m:ss.ss」按钮：只定位并聚焦播放器，不自动播放）；剪辑点（按成片时间合并各 item 的入点/出点：前后 item、前后 1 秒片段、剪辑点前最后一帧与后第一帧、烧录字幕/相邻镜头碎片/咔哒三项检查在该点的结果，缺数据时写明“无数据”）；缩略图墙与全部采样帧（点击跳转）；全部检查表（`measured` 折叠为格式化 JSON，refs 时间可跳转）；签字区（签字状态、评审决定与 findings、可复制的 `python3 …/scripts/creative_craft.py video-approve --root <production> --stage inspect --by <name>` 命令文本，未提供 `--production` 时保留占位并说明；决定为需修改/拒绝时提示不应签字；`unverified` 列表）。
- **签字核对**：只有 `production.json` 能证明人工签字。给了 `--production` 时页面只读 `<production>/production.json`：inspect 阶段已由 `video-approve --stage inspect` 签字（`approval` 记录签字人与时间），且本 `qa.json` 字节的 SHA-256 是 inspect 阶段最后一次记录的 render-qa（签字人审看的就是这一份），主标题才是“人工已签字：<签字人> · <时间>”，副行是评审决定（接受为通过色）。否则：评审为“接受”时主标题是“等待人工签字”（待定色，不用通过的绿色），副行写明评审来源（“Agent 评审：接受”；`reviewer_kind` 缺失按 Agent 计；自报 `human` 写“人工评审：接受”，同样不算签字）；需修改/拒绝以决定为主标题；未完成为“待评审”。主标题下一行说明原因：未提供 `--production`、`production.json` 无法读取、inspect 尚未签字、签字记录的是另一版本的 `qa.json`（同一路径记录的 SHA-256 与当前文件不同：`qa.json` 在记录后被修改）、签字属于之后一轮的 `qa.json`，或 inspect/export 都没有记录本文件。export 阶段记录的导出检查是签字之后做的，签字人没有审看过：主标题为“导出检查：签字人未审看本文件”（待定色），说明行写出签字针对的检查版本，提示对照两份检查结果。评审人显示为“名字 · 类型”（如“Claude · Agent 评审”），名字已以 `(agent)`、`（人工）` 等括注结尾时只显示名字；自报人工时该项标为“评审人（人工）”。签字状态也写入内嵌摘要 JSON 的 `sign_off`。`renderReviewPage` 保持纯函数：读取 `production.json` 在文件包装里完成，结果以 `signOff` 选项传入。
- **自动检查中文摘要**：`qa.json` 的 `observation` 由 `qa` 用英文写出。已知检查（时长、分辨率、帧率、音轨、黑场、静止画面、有声区间静音、积分响度、真峰值、剪辑点咔哒声、字幕采样、字幕/图形安全区、按镜头采样、烧录字幕剪辑点、剪辑点相邻镜头碎片、HyperFrames lint）在问题列表与全部检查表中以按 `status` 与 `measured` 生成的中文摘要为正文，英文原文折叠在“原文”里；成片时间写 m:ss.ss，源素材时间注明“源时间”。未知检查 id 或缺少所需 `measured` 字段时直接显示英文原文。
- **数据与安全**：旧版或缺字段的 `qa.json`（无剪辑点检查、无 `contact_sheet`、无 `review` 等）各区块显示明确的空状态，不报错。所有来自 `qa.json` 的文本都做 HTML 转义；内嵌 JSON 把 `<`、`>`、`&`、U+2028/2029 转成 `\uXXXX`，`</script>` 无法闭合脚本元素。
- **设计**：系统字体（PingFang SC / Noto Sans CJK SC / Microsoft YaHei），正文 16 px、数字等宽对齐（tabular-nums），等宽字体只用于哈希与命令；颜色用 CSS 变量，浅色/深色随 `prefers-color-scheme` 切换，正文与状态色对比度 ≥ 4.5:1；每个状态都有文字与不同形状的图标（通过/警告/失败/未知/不适用），不只靠颜色；按钮是 `<button>`，点击区域 ≥ 44×44 px，`:focus-visible` 描边清晰；无动效。宽屏两栏，≤ 900 px 单栏；竖屏成片限制最大高度（70vh / 720 px）并居中。
- 模块调用：`renderReviewPage(qa, options)` 是纯函数（数据 → HTML 字符串），`reviewPage(qaDir, { video, production })` 是写文件的包装。测试见 `tests/review-page.test.mjs`。
- 剪辑点的前后 1 秒片段不带原生控件，每段只有一个「播放片段 / 暂停片段 / 重播片段」按钮（点击画面也可切换），整页 Tab 顺序里每段只占一个位置；一个视频开始播放时，页面上其余视频（含主播放器）自动暂停。
- 浏览器可能推迟加载后台标签页里的视频，这由浏览器决定，页面无法绕过。成片加载完成前点「跳到」时，页面提示“成片加载中，加载完成后定位到 …”，只保留最后一次跳转，等加载完成后再定位；成片加载失败时提示无法定位。
- 写评审意见：使用签字人的语言；时间一律写成片时间（与 `refs[].time_seconds`、跳转按钮一致），修改需要源素材时间时注明“源时间”；写入 `qa.json` 后运行 `review-page` 重新生成页面。
- 局限：页面只是证据的查看方式，不替代完整看片与听检；`reviewer_kind` 不是人工签字的证据，签字仍由 `video-approve` 记录。在已等待批准（`awaiting_approval`）的阶段再 `video-record` 会把它重新打开为 `in_progress`（命令会提示），需要再次 `video-complete --stage <阶段>` 后才能 `video-approve`。

## 验证与限制

`npm test` 覆盖：共享样例（valid 全部通过、invalid 逐文件按违反规则拒绝）、Python 侧附加规则的内联负向用例、11 个操作、批次原子性、过期修订、锁定轨道、dry-run 零写入、split 字幕归属、replace_media 字幕规则、revert_to 单独成批、规范化 operations 摘要、v1 迁移（时序/字幕/音轨分道与截断）与 v2 工程拒绝 v1 操作、多轨编译（z 序/transform/opacity/独立音频/转义）、lint 关卡放行与阻断；P2：16 个新增共享 invalid 样例的拒绝原因、与 Python 对齐的附加规则内联负例（graphic 字段白名单、duck 指向字幕轨、crossfade 起点须严格晚于前驱、全量重叠扫描）、P2 编译（playback rate、volume lane 用 HyperFrames engine/core 解析并取样核对增益、透明度补间、图形转义、变速字幕换算、lint 零发现）、模板与变量类型校验、P2 编辑操作（props、graphic、duck、split/trim 规则、锁定轨道 duck、revert_to 保持锁定轨道的 duck）、512 点 volume 自动化上限在 create 与编辑（含 dry-run）时即拒绝、约 1000 item/100 crossfade/400 段被闪避音乐的编译耗时、安全区布局估算；P2.1：模板命名位置（缺省=旧位置、非法 placement 拒绝、lint 零发现）、最小字号（加载时抬高、抬高后仍须放得下、CSS 只能用 --fs 变量）、烧录字幕剪辑点判定（入点晚于字幕切换 warn 并给出变化时刻、对齐不报、出点前闪现 warn、无字幕素材与错位字幕带不报、整帧镜头切换不算字幕变化）与镜头检测（文件内 0.6 s 短镜头被切出、阈值可配置）；模板固定（0.5.0）：4 个新增共享 invalid 样例的拒绝原因、创建/编辑自动绑定与内容寻址复制、dry-run 只报告不写文件、删除最后使用者时移除绑定、执行层模板变化后旧修订仍按绑定字节编译出相同 HTML、`rebind_template` 的单独成批/未使用/无变化拒绝与升级后使用新字节、绑定文件缺失/篡改/符号链接/校验失败时读取与渲染失败、旧版原始字节绑定的规则差异拒绝、提高最小字号后旧绑定修订 HTML 不变、`revert_to` 恢复目标修订的变量与模板字节（HTML 一致）及未绑定目标的说明、锁定轨道上 graphic 的 rebind/revert 拒绝、未绑定历史修订上的无变化 rebind 拒绝、缺模板集时校验与编译拒绝、编辑批次每个绑定文件只读一次、写一次辅助函数、历史修订用执行层模板（`pinned: false`）且编辑后获得绑定、渲染目录复制绑定文件；源素材帧对齐（0.6.0）：`truncatedFrame`/`correctedSourceIn` 在 30/1、30000/1001、24/1 与 60/1 下只修正低于帧起点不超过 2 ms 且不足 0.1 帧的入点（修正为帧起点 + 0.1 ms；30/1 下 24.433、24.4327、24.4333 均为第 733 帧，恰低 2 ms 修正，24.430 等低于 2 ms 以上与 60/1 下达到 0.1 帧的不修正），帧起点、帧中点与帧内入点保持原值，帧率字符串与解析结果行为一致；帧率解析/约分与导入规则（可变帧率、视频晚于音频开始、音频起点为负、缺 `start_pts`、纯音频、封面图均不记录；所有流同一非零起点（不同 time_base 精确比较）、音频晚于视频开始时记录；封面图在前时 QA 分析第二条视频流、但不记录帧率；`rational`/`streamStart` 共用）；共享 invalid 样例的拒绝原因；编译只修正视频轨 item（同 item 声音同起点、音频轨 item 不修正、link 字幕随修正后入点换算、文档不被改写、无 `frame_rate` 保持原值）；编译视图单点计算（视图再次传入返回自身、剪辑点与视图 item 及原 item 对应、字体可见字幕随视图）；剪辑点出点的 `document_source_seconds` 为写定出点、剪辑点不携带原 item（写定值经 `correctionOf` 取得）；QA 建议以写定值为基准（`judgeCutPoint`/`judgeFragment` 的 `written`；修正入点 1.2999 的碎片与烧录字幕检查报告 `source_seconds` 1.2999、`compiled_source_seconds` 1.3001，写定值 + shift = 建议的帧中点，文本写 “source in 1.299900 s (compiled 1.300100 s)”）；24/1 素材在 60 fps 画布第 1 帧处拆分后尾段起点等于头段结束处；用到最后一帧的 item 修正后不超出素材时长容差，超出时不修正；`create`/`add_asset` 导入记录 `frame_rate`（含唯一视频流起点 0.5 s 的 mp4），而纯音频、带封面图的音频（与以前一致为 `video: true`、封面宽高，v1 工程仍可用作 clip）、音频起点 −44 ms 的合成 mkv、视频晚于音频 0.5 s 的 mkv 与 v1 不记录；渲染尺寸（0.7.0）：预览长边 640 且不超过画布、低于截图高度下限时取最小整数倍截图、遍历全部合法画布核对高度下限/偶数尺寸/截图上限/预览截图不大于导出截图/最窄输出 10 px、合成按截图尺寸编译（字幕字号同比放大）、缩回失败与取消时删除 `capture.mp4` 与不完整的 `video.mp4`（以替身 ffmpeg 模拟）；同进程截图串行（0.7.0）：排队顺序、失败不阻塞、等待中取消立即返回且任务不再运行、运行中的任务不被放弃、锁被占用时取消的 `renderProject` 立即写 `cancelled` 回执；帧对齐复核（0.7.0）：`loadProject` 一次性决定并绑定（模拟 0.6.0 工程的过期 `frame_rate` 不应用并给出原因、有效的照常修正、未绑定文档只做结构计算、工程文件不变）、绑定校验、编辑批次沿用决定、QA 取回执或旧回执默认值、先校验摘要再用探测缓存（并发加载被篡改副本与原工程互不影响）、`verifyAssets` 复用已校验文件；`streamStart`/`earliestStart`/`mediaZeroProblem` 的精确起点；剪辑点音频（0.8.0，`tests/audio-clicks.test.mjs`）：微淡变规则（切入源中间的两边加、源起点入边不加、显式淡变/crossfade 优先、画面不受影响、注入 0 时恒定 lane 仍写 `data-volume`）、两段相差 1/4 周期的 440 Hz 硬拼接按引擎同口径采样 lane 并经 AAC 往返后，关闭微淡变 QA warn 并引用两侧 item、开启时 pass、满幅 100 Hz 经斜坡不过下限、静音后直接起音判为咔哒、等功率 crossfade 中点功率（不同频率正弦与两段独立噪声）与两端相差 ≤0.5 dB 且 lane 本身偏差 <0.05 dB、微淡变的 lane 点计入 512 上限（不加微淡变恰为 512 点的 lane：`checkVolumeAutomation` 与编译都跳过该 lane 的微淡变并记录 `declick.skipped_lanes`、其他 lane 照常；不加也超限时以同一消息拒绝）、crossfade 每侧 9 点、同一素材相邻两段（源时间连续的 400 Hz）crossfade 用线性等增益曲线（振幅和恒为 1，中点功率偏差 ≤0.5 dB），同一素材不同源时间与不同素材用等功率、拆分接缝（源时间连续，含 1 帧内误差与变速）两侧不加微淡变且包络无下凹，源跳变、不同素材/音量/速度、空隙或一侧有淡变时照常加；以及原有的字幕重定位、路径约束、版本冲突、并发发布、父版本变化、输入变化与取消。

`npm run smoke` 用自有测试图案和测试音（无客户素材），输出在根 `dist/local-production/<timestamp>/`：

1. v1 旧流程（以 `createProject(…, { legacyV1: true })` 建立 v1 工程，仅供兼容验证）：五个版本、旧 CLI `edit` 形式、画面/音调信号核对、静音导出与独立音轨。
2. 对该 v1 工程提交 v2 批次：迁移修订 + 编辑修订，迁移修订导出与 v1 导出逐帧比对。
3. v2 多轨：主轨 + 补导入 B-roll（transform 叠放）+ 音乐轨 + link 字幕 + 非 link 字幕；dry-run 不发布不复制、过期修订拒绝、锁定轨道拒绝、split、revert_to；导出后核对 B-roll 框内为 B-roll、框外为主画面、开始前不可见，以及主轨音调与 660 Hz 音乐同时存在。
4. CLI `qa` 生成 `qa.json`（`cut-point-clicks` 在 2 s 的 talk1→talk2 硬切处 pass）。再复制该导出、剥离音轨并改写回执摘要，模拟“声称完成但丢音轨”的导出器，QA 必须给出 `verdict = fail`（`cut-point-clicks` 为 unknown）。
5. P2 品牌包装（`packaging/`，24 fps 1280×720）：标题卡（0–36 帧）+ 下三分之一（76–116 帧）、两段主画面 crossfade（口播 0–72 淡入，色条 60–120 以 12 帧 crossfade 进入）、一段 1.5× 变速（口播源 2.5 s 起）带淡出、音乐轨在主画面轨下 −12 dB 闪避并淡入淡出、变速段上的 link 字幕。断言：lint 0 error/0 warning 且无 `audio_volume_double_automation`、三个 `<audio>` 全为 volume lane、VTT 中变速字幕为 5.667→6.333 s（口播素材记录 `frame_rate: "24/1"`，入点 2.5 s 恰为第 60 帧起点、不是截断小数，编译保持原值）。信号检查：变速段第 132 帧与源 3.25 s 的画面 MAE 远小于与 1× 位置 3.0 s；crossfade 中点（第 66 帧）与两源平均帧的 MAE 远小于与任一单源；淡入首帧为黑、淡出末帧亮度降到 20% 以下；660 Hz 音乐能量在口播区间相对非口播区间约为 depth_db（±2 dB）；音乐淡入首窗明显更低；标题卡与下三分之一区域与下层画面显著不同且含白字与深色底。导出 QA 的 `graphic-safe-area`/`caption-safe-area`/lint/`cut-point-clicks` 为 pass（0.8.0 的微淡变与等功率 crossfade 未改变上述信号断言：闪避 −12 dB±2、淡入首窗等照旧通过），`true-peak` 引用 `audio_lowered_db`。人为失败：新增一条 fontHeight 0.08、centerY 0.9 的两行字幕，预览 QA 必须在 `caption-safe-area` 上 fail。
6. P2.1 竖屏 QA（`portrait/`，30 fps 360×640 预览）：合成素材 `captioned.mp4`（移动测试图案 + 约 70% 高度的白色“字形”方块与深色描边，1.5 s 时从 A 行切到 B 行）与 `short-shot.mp4`（0.6–1.2 s 为一段色条短镜头）。item `late` 入点 1.3 s（字幕晚 0.2 s 切换，正例）、`shots` 含短镜头（成片 1.6–2.2 s，远离 item 中点与剪辑点）、`aligned` 入点 1.5 s（负例）；`title-card` 用 `placement: top`、`lower-third` 用 `placement: upper`。断言：lint 0/0；编译 HTML 的位置与 `--fs-*` 字号；`burned-caption-cut-points` 为 warn 且只有 `late` 入点 warn、建议 1.5 s，`aligned` 入点为 aligned；`shot-sampled` pass 且有一帧 `reason: "shot"` 落在 1.6–2.2 s，该帧高饱和像素（色条）占比 > 30%；`graphic-safe-area` pass；`cut-boundary-fragments` pass（`shots` 从文件首帧开始、完整显示 0.6 s 色条短镜头，不算碎片）。前面几个场景的测试图案素材在该检查上都是 pass（无字幕不报）。
7. 源素材帧对齐（`frame-snap/`，30 fps 320×180 预览）：合成素材在第 22 帧（22/30 = 0.7333… s）由红变蓝，入点写成 0.7333。v2 工程导入记录 `frame_rate: "30/1"`、文档保留 0.7333、编译 `data-media-start="0.733433333"`（第 22 帧起点 + 0.1 ms），成片用 `select=eq(n\,0)` 取第 0 帧为蓝（新颜色），`cut-boundary-fragments` 为 pass、入点 `source_frame = 22` 且 aligned（报告写定值 `source_seconds` 0.7333 与 `compiled_source_seconds` 0.733433）；同一素材的 v1 工程（无 `frame_rate`，历史口径）第 0 帧为红（旧颜色），该检查 warn。
8. 以带 jsonschema 的 Python（`CREATIVE_PYTHON`，默认仓库根 `.venv/bin/python`）按 Draft 2020-12 校验全部 v2 修订文件（含品牌包装、竖屏与帧对齐工程）与 7 份 qa.json，缺少 Python/jsonschema 时 smoke 直接失败。

合成样例不能证明真实口播语义、品牌一致性、商业表现或专业剪辑效果；样例响度（约 -19.7 LUFS）落在目标外，QA 如实给出 pass_with_warnings。输入时长上限 30 分钟，成片上限 10 分钟是当前合同限制，尚非长时长性能验收结果；QA 对每个采样单独调用 ffmpeg，长工程/大量 item 时耗时随采样数线性增长。无生成、云凭据、上传、发布、自动剪辑决策；用户/Agent 自行给出合法选片和已获授权素材。

P2 的已知限制：闪避依据参照轨上**有声 item 的区间**，不是语音活动检测（item 内部的停顿同样被压低）；crossfade 的音量自 0.8.0 起按源时间连续性选择曲线：两侧是同一段源声音时用等增益，否则用等功率；按素材与源时间判断相关性只是近似，见“剪辑点音频”；包络在斜坡端点精确、端点之间线性，两个斜坡同时变化时略偏离精确乘积；smoke 样例真峰值约 −19.9 dBTP，限幅器未触发，`audio_limiter.engaged = true` 的路径只按 producer 源码确认字段位置，尚无真实触发样例；安全区为布局估算或模板加载保证（见上）。遗留：模板加载时的“max_length 文本放得下模板框”估算按框宽 95% 计算，**未计入模板 CSS 的内边距**，极端长文本可能仍被省略号截断，QA 不再对此给出估算证据，需看采样帧。

### 可选的源字幕样式

字幕可带 `style: {fontHeight, centerY, color, strokeWidth, weight}`。fontHeight 为画布高度比例0.015–0.08，centerY 为高度比例0.1–0.9，strokeWidth 为高度比例0–0.004，color 为六位十六进制色，weight 为400/600/700/900。显式样式使用透明背景与深色描边；预览按输出尺寸同比缩放。不接受任意 CSS、外部 URL 或字体路径。不传 style 时保留默认排版；新建含字幕工程的实际字体按下述固定制品绑定。

### 固定字幕字体

新建且含有效字幕的工程（以及首次通过批次引入字幕的 v2 工程）复制 `fonts/NotoSansSC.ttf`，将 `caption_font` 的 profile、SHA256 和内容寻址路径写入不可变工程修订；渲染时再次核对并复制同一字节。来源为 Google Fonts 固定 revision，见 `fonts/manifest.json`；OFL-1.1 原许可随 `fonts/OFL.txt` 交付。文件约17.8MB，运行时不下载、不安装到系统，也不依赖系统字体名。400/600/700/900 使用同一可变字体的对应字重，禁用合成粗体。

缺文件、摘要不符、符号链接及字体未覆盖的字符均拒绝；未知字体/profile 不回退。字形覆盖直接检查已验证文件的 Unicode cmap；Chromium 必须成功加载请求的字重才解除 producer 就绪门槛。仅等待 `document.fonts.ready` 不足以发现加载失败。`receipt.caption_font` 分开记录制品完整性、字形覆盖与运行时加载；`source_match` 始终 `unverified`，这套绑定不证明所选字体就是原片字体。

没有 `caption_font` 且已有字幕的既存工程（含迁移而来的此类 v1 工程）仍按原来的系统字体行为渲染，并标记 `legacy-system-fonts/unverified`；不自动重写旧修订，后续编辑也不改绑。要使用固定字体，须显式创建新工程。无新增字幕的原画面不会被重打字幕。制品升级必须保留旧 profile 的兼容支持，或明确拒绝旧绑定，不能用新字节冒充相同 profile。AIOS Run 冻结前对整套能力包版本的绑定与升级调度仍由宿主负责；本模块只验证已保存的渲染工程。

这是一份经宿主确认并冻结的样式参数，不是自动识别原片字体的能力。原片已有烧录字幕在保留画面时直接保留，无需擦除再重做；当前系统字体回退不保证原片字形一致或跨主机字体一致。样式进入工程和摘要，可随编辑保存；消费者若无法携带样式，应拒绝转换而不是静默丢弃。

时间边界按半开区间 `[start, end)` 执行：画面、字幕与音轨的 HTML 时间边界统一提前 1 纳秒以吸收浮点误差，避免小数序列化向上舍入造成整帧延迟。保存的工程帧数、源媒体裁切点、VTT 语义时间均不变；媒体 seek 使用完整数值精度。该容差远小于支持的24/30/60 fps一帧，属于输出序列化约定，不是整体提前字幕或修改原片。

实际浏览器故障回归：配置已安装的 `PRODUCER_HEADLESS_SHELL_PATH` 后运行 `node --test tests/font-render.integration.mjs`。使用1秒合成黑色视频验证400/900字重，再故意让字体URL不存在；必须失败，不能输出可交付结果。producer 0.8.53会覆盖内部tween-building标志，且把已拒绝的buildReady当作结束，因此字体门槛使用独立buildReady项，加载失败后保持未就绪，交给其有界超时中止；该门槛在 0.8.108 上经同一回归测试复核通过。不要以`document.fonts.ready`已完成替代加载成功检查。

### 同进程渲染串行

实测同一进程内并发调用 `renderProject` 会互相破坏截图（画面只占上部、下部为黑）。因此进程内的**浏览器截图阶段**（producer `executeRenderJob`）排队依次执行（`withRenderLock`）；加载与素材校验、合成、lint、缩回与解码检查都在锁外，可以并行。排队等待截图时被取消（`signal` 中止）的渲染**立即**走取消路径、写 `cancelled` 回执并返回，不等前面的截图结束，轮到它时也不会再启动；已经开始截图的渲染不会被提前放弃，锁一直保持到它自己结束（producer 观察同一个 `signal`）。`tests/render-lock.test.mjs` 覆盖排队顺序、失败不阻塞、等待中取消立即返回（含真实 `renderProject` 在锁被长任务占用时取消）；`tests/render-concurrency.integration.mjs` 实测同进程两路并发渲染（红/蓝素材），两个成片第 0、15、29 帧的上、中、下区域都是各自素材的颜色。需要更高并行度时请使用多个进程或 worker，并为每个渲染使用独立输出目录。

### 模板版本与回执

图形模板随修订固定（合同见 `docs/content-production-architecture.md`“图形模板固定到修订”）。做法与固定字幕字体相同：按内容寻址把模板 JSON 原始字节复制进工程。

- **绑定**：`create` 与编辑批次产生的新修订只要含 graphic，就为所用模板写入 `graphic_templates` 绑定 `{id, version, sha256, file: "templates/<sha256>.json"}`；首次使用某模板时把执行层模板经最小字号规范化（`enforceMinimumText`）后的确定性序列化字节写入工程 `templates/<sha256>.json`，`sha256` 即这些字节的摘要（临时文件 + 硬链接、不覆盖，已存在且字节相同则复用，写后核对摘要；`templates/` 目录或文件为符号链接即拒绝）。随附模板的源文件本身已是规范化形式，因此与旧版按原始字节绑定的摘要相同。dry-run 不写文件，只在 `diff.graphic_templates.added` 里列出将新增的绑定。
- **不变性**：已有绑定在后续编辑中保持不变，执行层模板升级或规范化规则（如最小字号）变化也不影响；`revert_to` 恢复内容的同时恢复目标修订的绑定（绑定文件仍在工程内，读取目标修订时核对存在与摘要），目标修订是未绑定的历史修订时，其模板绑定到当前执行层字节并在 `notes` 中说明；锁定轨道上的 graphic 因此会改变模板字节时拒绝。删除最后一个使用某模板的 graphic 时移除该绑定（文件留在工程中）；绑定全部移除后字段保留为空数组。
- **升级**：只有 `rebind_template {template}` 能把绑定换成当前执行层字节，必须单独成批；新模板定义下现有 graphic 的变量须仍然合法，否则整批拒绝。
- **历史修订**：没有 `graphic_templates` 的旧修订不被改写，渲染与校验使用当前执行层模板。在其上提交编辑时，若结果含 graphic，新修订为其绑定当前模板字节，并在批次结果 `notes` 中说明。
- **读取与渲染**：`read`/`render`/`qa` 对有绑定的修订只从工程内绑定文件加载模板：核对 sha256、重新执行安全与结构校验（`validateTemplate`，不再做会改写内容的规范化）并核对 version，graphic 变量按绑定的模板定义校验；文件缺失、摘要不符、符号链接或校验失败即失败（读取即失败，因此也无法渲染）。旧版按原始字节写入、且不是规范化序列化的绑定：若当前规范化会改变其内容，按“规则差异”失败而不静默改写，否则按原字节使用。模块接口上模板集是显式的：`loadProject` 返回 `{doc, templates}`，`compose`/`validateV2` 等对有绑定的文档必须传入模板集（`validateV2` 仅在显式 `{structuralOnly: true}` 时只做结构校验）；`read` CLI 输出不变。渲染把绑定文件复制进渲染目录 `templates/`，渲染目录可独立重放。
- **回执**：`templates` 每项为 `{id, version, sha256, pinned, source}`。固定的修订为 `pinned: true, source: "project"` 并带 `file`；历史修订为 `pinned: false, source: "runtime"`（sha256 为执行层模板原始字节摘要），与 `composition_sha256` 一起用于追溯差异。
- Python 侧只校验结构与覆盖规则（同一组共享样例）；模板内容与变量类型仍由 Node 校验。

## 本地语音转写

`transcribe` 用本机 whisper.cpp 把素材口播转成带句级时间戳的 JSON，作为 production-plan 选片证据（evidence modality `asr`）。客户音频不离开本机：ffmpeg 抽取 16 kHz 单声道 PCM 到私有临时目录，转写结束（含失败）即删除；不调用任何云端服务。

```sh
brew install whisper-cpp            # 提供 whisper-cli；或用 CREATIVE_WHISPER 指向其他构建
npm run fetch-asr-model             # 下载固定模型到 ~/.cache/whisper-cpp/（CREATIVE_WHISPER_MODEL_DIR 可覆盖）
node cli.mjs transcribe MEDIA NEW_OUT.json [--lang zh] [--model PATH] [--clean auto|on|off]
```

模型固定为 `ggml-large-v3-turbo.bin`（1624555275 字节，SHA-256 `1fc70f77…e2bc69`，来源 `huggingface.co/ggerganov/whisper.cpp`，清单见 `asr.mjs` 的 `ASR_MODEL`），不入库。下载先写 `.partial`，大小与摘要均吻合后原子 rename；已存在且吻合则跳过，不吻合直接拒绝。每次转写前都核对模型：文件名必须是固定模型、大小与摘要必须吻合，否则报错（缺失时提示 `npm run fetch-asr-model`）；为免每次散列 1.6 GB，校验通过后在模型旁写 `*.sha256-verified.json`，仅当大小、inode、mtime、ctime 都未变时复用（ctime 无法由用户态改回，原地覆盖后即使恢复大小与 mtime 也会重新散列）。转写期间收到 SIGINT/SIGTERM 时先停止正在运行的 ffmpeg/whisper 子进程、同步删除私有临时音频目录，再以 130/143 退出；正常结束后注销该处理器。

whisper 参数：`-l zh` 时附加 `--prompt "以下是普通话的句子。"`（引导简体与标点）。`--clean`：

- `off`：只做常规转写。
- `on`：只做预处理转写：`ffmpeg -af "highpass=f=120,lowpass=f=6000,afftdn=nf=-25,dynaudnorm"` 后加 `-mc 0 -et 2.8 -nth 0.3`。
- `auto`（默认）：先常规转写；用 `silencedetect=n=-35dB:d=0.5` 估算有声时长（总时长减去 ≥0.5 s 的静音段）。若有声 ≥ 2 s 且识别覆盖（句子区间并集）< 有声时长的 50%，再做预处理转写，取覆盖更大的一次（相等时保留常规结果），理由写入 `choice_reason`。

判据实测（whisper.cpp 1.9.2）：背景音乐很重的 27 s 直播口播片段全程有声（-35 dB 下无静音段，有声 26.842 s），常规转写只识别前 2.28 s（8.5%），触发重试；预处理转写 13 句覆盖 26.84 s，被选中。`say -v Tingting` 合成的 2.1 s 中文语音常规覆盖 1.86 s，不触发重试；纯静音有声 0 s，不触发重试。

输出（时间单位秒）：

```text
{schema: "creative-craft.local-transcript.v1",
 media: {path_basename, sha256, duration},
 engine: {name: "whisper.cpp", binary_version, model, model_sha256},
 language, audio_activity: {active_seconds, detector},
 attempts: [{params: {preprocess, whisper_args}, coverage_seconds}],
 chosen_attempt, choice_reason, note, segments: [{start, end, text}],
 phrases: [{start, end, text, text_reliable?: false}]}
```

`asr.mjs` 导出 `toPlanEvidence(spans, from, to, method, { segments })`：返回与 `[from, to]` 有重叠的句子（或短语），形如 `{modality: "asr", start_seconds, end_seconds, excerpt, raw_score: null, method}`，时间保留原始边界（不裁到区间）。传入短语时同时传 `segments`：标记 `text_reliable: false` 的短语以其所在句段（重叠最多的 segment）的文本作为 `excerpt`，时间仍是短语自己的，`method` 追加说明“短语文本乱码、摘录为整句”；没有可用句段时报错，不输出乱码摘录。

限制：ASR 文本可能有错字和同音字（如品牌名、人名），引用前需核对；时间戳是句级，不是逐字或逐帧对齐，剪辑点必须人工听审确认。覆盖率只说明“有文字的时间段”，不说明文字正确：whisper 会在纯音乐/持续音调上幻觉出整句（测试中 440 Hz 正弦音被“转写”为一句视频结尾套话并覆盖全程），此时覆盖足够、不会重试，幻觉内容也会进入结果。`auto` 判据只在上述片段上实测，阈值尚未在更多素材上标定。输出文件必须不存在。

`npm test` 中的 ASR 测试只用合成音频（ffmpeg 静音与正弦音、macOS `say -v Tingting`），不含客户素材；whisper-cli 或模型缺失时两项端到端测试跳过并给出原因，模型存在但摘要不符则失败。

**短语级时间（phrases）**：whisper 对背景音乐垫底的密集口播会把十几到二十几秒合成一个句段（segments）。转写改用 `-ojf` 读取词元时间戳，在逗号、句号等标点处切分为 `phrases`。中文标点与 `,!?;` 总是断句；`.` 与 `:` 只在下一个词元不以数字开头、且当前词元不是单个拉丁字母缩写（如 `A.`）时断句，所以 `3.`+`5倍`、`10:`+`30` 不会被切开。词元文本可能把一个多字节汉字拆在两个词元之间，拼出的短语会含替换字符 U+FFFD（句段文本不受影响）：这类短语保留时间，标记 `text_reliable: false`，取证时改用所在句段文本（见 `toPlanEvidence`）。在一条 137 秒的真实素材上，相对云端 ASR 的句末边界：中位偏差 0.09 s，p90 0.66 s；句首中位 0.14 s，个别离群达 3 s。短语只用于**提名**剪辑点，仍需结合能量谷、烧录字幕检查和人工听审确认。

## 素材分析与剪辑点建议

把“镜头检测 → 本地 ASR 短语 → 能量谷 → 烧录字幕换行 → 镜头碎片 → 帧中点 → 冲突列选项 → 按段音量”这套手工选点流程固化为两步。两步都只读素材、只在本机运行，输出文件必须是新文件；结果是**建议**，每个点仍需听审、看首尾帧。

```sh
node cli.mjs analyze MEDIA NEW_ANALYSIS.json [--transcript T.json | --asr [--lang zh] [--clean auto|on|off]] [--caption-band TOP:BOTTOM] [--scene-threshold N]
node cli.mjs suggest-cuts ANALYSIS.json BEATS.json NEW_CUTS.json
node cli.mjs apply-cuts CUTS.json NEW_APPLIED.json [--choose BEAT.EDGE=OPTION ...]
```

### analyze：`creative-craft.footage-analysis.v1`（执行层自有格式）

时间单位均为媒体秒（流时间 − 最早流起点，与 EditDocument `source_in_seconds` 一致），镜头、字幕、短语、句段、能量与响度同一时间轴（`time_base` 字段注明）。能量与响度从音频流首样本解码，其 `start_seconds` 即音频流相对最早起点的偏移 `audio_offset_seconds`；ASR/transcript 的时间从解码音频首样本计（`asr.mjs` 单独解码音频），写入前统一加上该偏移换算为媒体时间（音频晚于视频开始的素材，短语与能量谷、建议剪辑点才对得上）。帧 n 占 `[n/fps, (n+1)/fps)`，帧中点 `(n+0.5)/fps`。

```text
{schema, time_base, audio_offset_seconds, media: {path_basename, sha256, duration, video_duration, start_seconds, frame_rate, fps, frame_count, width, height, has_audio},
 shots: {method, scene_threshold, list: [{index, start_frame, end_frame(不含), frames, start_seconds, end_seconds, start_mid_seconds, duration_seconds}]},
 captions: {method, band, changes: [{frame, source_seconds, frame_mid_seconds, kind: caption|shot, line_share, glyph_share, rest_mad}]},
 dips: {method, thresholds, list: [{start_frame, min_frame, end_frame(不含), start_seconds, min_seconds, end_seconds, ref_luma, min_luma}]},
 speech: {source: transcript|asr|none, note?, transcript?, caveat, phrase_split, phrases: [{index, start, end, text, text_reliable?, split_from?, split_by?, text_split_estimated?, lufs, true_peak_dbtp}], segments},
 energy: {window_seconds: 0.02, sample_rate: 16000, start_seconds, unit: "dBFS", floor_db: -100, format, values_db: [...]},
 loudness: {target_lufs: -14, integrated_lufs, true_peak_dbtp, volume_for_target,
            series: {hop_seconds: 0.1, block_seconds: 0.4, start_seconds, format, momentary_lufs: [...], true_peak_dbtp: [...]}}}
```

- **镜头**：全片按 15 s 分块解码（灰度、短边 360，块两侧各留 0.3 s 余量，事件归属其时间所在的块），用 QA 剪辑点检查的同一判定（`cut-fragments.mjs` 的 `shotChanges`：MAD ≥ 30 且 MAD 跳变 ≥ 阈值×100，或均值阶跃 ≥ 30，可识别闪白）。帧号按 `frame_rate` 换算；源素材没有可信恒定帧率时（`source-frames.mjs` 的 `probedFrameRate` 为 null）不给帧号，`suggest-cuts` 拒绝此类分析。
- **烧录字幕**：全片扫描，复用 `burned-captions.mjs` 的 `stepEvents`（帧差阶跃启发式，不是 OCR）；`kind: shot` 表示字幕带与整帧一起变化。
- **压暗/黑场过渡（dips）**：渐变的“压黑再亮起”每帧亮度只变 ~20 灰度级，达不到镜头判据（均值阶跃 ≥ 30），会被漏掉；剪辑点落在里面，成片就以一段从黑场淡入（或淡出到黑）开头/结尾。复用镜头扫描同一次解码的逐帧平均灰度（`cut-fragments.mjs` 的 `frameStats` / `lumaDips`，全片拼成一条序列，跨块的 dip 也能找到）：从一段内最暗的帧向两侧走，只要亮度仍在回升（一或两帧内升 > `step_levels` = 2；离谷底 ≤ `flat_levels` = 20 的帧即使平也继续，所以保持几帧的黑场算一个 dip）就继续，直到两侧亮度稳定；最暗帧 ≤ `ratio` = 50% × 参考亮度、且比参考低 ≥ `depth_levels` = 40（参考亮度 `ref_luma` 取两侧稳定亮度的较低者），压暗帧总长 ≤ `max_seconds` = 1.5 s 才算 dip；走到解码窗口边缘仍未稳定的不判，除非那就是文件本身的首帧/末帧：片头从黑场淡入、片尾淡出到黑是一侧敞开的 dip，只用另一侧的稳定亮度作参考（全片序列总是从首帧到末帧；QA 的解码窗口只在窗口边缘就是文件边缘时这样判），一侧敞开时无法靠“亮度恢复”区分淡出与切到较暗的末镜头，所以最暗帧须 ≤ `open_ratio` = 25% × 参考亮度（红切蓝这类硬切约 50%，淡到黑只有几 %）；片尾敞开的 dip `end_frame` 为帧数、`end_seconds` 为末帧结束时间。`start_frame` 是第一帧压暗帧，`end_frame` 是第一帧恢复帧（不含），`min_frame` 最暗帧，`min_luma` 其平均灰度。标定（`byq-cushion-05` 整片 157.6 s，30 fps，只读）：全片只报 1 个 dip，即 124.833–125.133 s（帧 3745–3753，平均灰度 119.6 → 3.0 → 109.6），正是 wear 段入点 124.95 s 所在的压黑过渡；把阈值放宽到 ratio 1、depth 3 时全片 35 个候选里次深的只有 18.5 级 / 85%（136.0 s），离阈值很远，原阈值下无误报。时长超过 1.5 s 的黑场不是 dip（QA 的 blackdetect 管）；叠化（两镜头交叉）亮度不一定下降，不检出。旧分析文件没有 `dips` 字段，`suggest-cuts` 照常工作、不应用 dip 规则。
- **短语**：`--transcript` 读 `transcribe` 的输出（`media.sha256` 与素材不符则拒绝）；`--asr` 直接调用本地 whisper.cpp（`asr.mjs` 的 `transcribe`，含背景音乐降噪重试），临时转写文件放在 `fs.realpath(os.tmpdir())` 下的私有目录，结束即删；两者都没有时 `phrases` 为空并在 `note` 说明，建议只能以 beat 时间范围为语义边界。
- **短语细分**（`PHRASE_SPLIT`）：`asr.mjs` 只在标点处切词元；背景音乐重时降噪重试常用空格分句（如“对不起了 周年庆…”），而 transcript 文件不含词元时间，所以在这里按能量细分，结果带 `split_from`（原短语序号）与 `split_by`：
  - `whitespace`：两个 CJK 字符之间的空格（含全角空格）与标点同等视为短语边界。边界时间取空格文本位置（按字数比例）± 25% 短语时长内最低的能量谷（距短语两端 ≥ 0.1 s，低于短语中位能量 ≥ 6 dB，向两侧扩到谷底 +6 dB），前一段止于谷起点、后一段始于谷终点；找不到谷则不拆。挨着拉丁字母或数字的空格（“Bossin 素颜霜”）是词间空格，不拆。
  - `energy`：没有分隔符时，短语内部连续 ≥ 0.25 s、全程低于短语中位能量 ≥ 15 dB 的停顿也拆开，文字按时间比例分配并标 `text_split_estimated: true`。阈值来自 4 条真实口播素材：连续语句内部的能量凹陷最长达 0.22 s（−15 dB）和 0.32 s（−12 dB），阈值高于两者；这 4 条素材上该规则没有触发任何拆分，只有空格规则拆了重音乐素材的 5 个短语（成为 11 段）。
- **能量包络**：单声道 16 kHz，20 ms 窗 RMS，`values_db[i]` 覆盖 `[start_seconds + i×0.02, +0.02)`，保留 0.1 dB，静音记 −100。背景音乐垫底时 silencedetect 找不到静音，只能看能量谷。
- **并行与取消**：画面扫描、能量、响度与短语四路并行；任一路失败即中止其余各路（AbortController 传入每个 ffmpeg/whisper 子进程调用，子进程被终止），等各路收尾（临时目录已删）后抛出最先的错误，CLI 及时退出，不写输出文件。
- **响度**：一次 `ebur128=peak=true:framelog=verbose` 全片解析（Summary 由 `media-analysis.mjs` 的 `ebur128Summary` 解析，与 QA 共用），保存 100 ms 步进的瞬时响度（400 ms 块）与每 100 ms 的真峰值。任一区间的积分响度按 BS.1770 门限（绝对 −70 LUFS、相对 −10 LU）由该序列计算，与 ffmpeg 全片结果一致（测试要求 ≤ 0.5 LU）；短于 400 ms 的区间为 null。

### suggest-cuts：`creative-craft.cut-suggestions.v1`

`BEATS.json` 为数组或 `{beats, asset_id?, track_id?, canvas_fps?}`；beat 为 `{id, from, to}`（粗略源时间范围）或 `{id, text}`（按短语文本匹配）。beat 还可带 production-plan 字段 `role`、`purpose`、`requirement`（非空字符串）与 `hard_constraints`（非空字符串数组），原样写进 `cuts.json` 的 beat，供 `apply-cuts` 生成计划 beat；不给就不写，也不会被补。

- **语义边界**：范围 beat 取至少 50% 落在范围内的完整短语；文本 beat 把文本与每段连续短语去掉空白、标点、符号并小写后算字符 LCS 相似度 `2·LCS/(|a|+|b|)`，取最高者（并列取最早、最短），低于 0.6 为 `unmatched`；别处得分相差 ≤ 0.02 时记为 `edge: text` 冲突。
- **能量谷**：入点在首短语起点前 0.4 s 至后 0.15 s 内找、出点在末短语终点前 0.15 s 至后 0.4 s 内找（不越过相邻短语 0.15 s 以上）。谷 = 不高于该窗最低值 +6 dB 的 20 ms 窗，间隔 ≤ 80 ms（咔嗒声、换气）的合并；只取最低值在窗底 +3 dB 内的谷，选离短语边界最近者。切点放在谷的最低段（最低值 +1 dB 内）中央，但入点距语音开始最多 0.2 s（`lead_in`）、出点距语音结束最多 0.2 s（`lead_out`）。出点尾音留量即由此决定：谷短时切在谷中，谷长时留到语音结束后 0.2 s 为止（谷底更早则更少），之后若字幕/镜头规则把出点提前则以规则为准；需要更长或更短的尾音请人工调整。
- **入点规则**（反复应用直到不再移动）：入点后 0.5 s 内有字幕变化 → 移到该帧（入点帧本身就是变化帧视为对齐，与 QA 一致。此时其后 0.5 s 内若还有变化，例如第 n 与 n+6 帧，**不自动移动**入点，只在 `notes` 与 `evidence.in.opening_caption`（`in_frame`、`next_change_frame`、`next_change_seconds`、`shown_seconds`）提示“开场字幕仅显示 x s，可能是上一行残留，请检查”。理由：帧差检测分不出“换一行”与“字幕动画/局部变化”或“空白后出新行”，真实素材上自动后移会偏离人工入点（混剪口播 31.60 s 处 948→953 帧的弱变化会把入点推后 5.5 帧）；渲染后 QA 的 `burned-caption-cut-points` 还会在成片上再判一次）；入点后 1 s 内有镜头切换 → 移到切换帧（相隔 < 0.5 s 的连续切换视为闪切一并跳过；比 QA 的碎片判定更严：开头镜头不足 1 s 也移）。
- **dip 规则**（入点、出点都在规则循环里，与字幕/镜头规则一起反复应用）：入点帧是分析里某个 dip 的压暗帧 → 移到该 dip 的第一帧恢复帧 `end_frame`；出点前最后显示的帧是压暗帧 → 移到 dip 的第一帧压暗帧 `start_frame`（最后显示的是压暗前一帧）。只有这次移动切掉的语音 ≤ `speech_tolerance`（0.25 s，口径同其他规则）才移；否则**不移、也不算冲突**（短暂淡入是观感问题，不是丢字），在 `notes` 与 `evidence.in.dip` / `evidence.out.dip`（`start_frame`、`min_frame`、`end_frame`、`start_seconds`、`end_seconds`、`ref_luma`、`min_luma`、`kept_because`）里提示；`kept_because` 写明留在 dip 内的真实原因：`speech_tolerance`（移出会切掉超过 0.25 s 语音，note 给出切掉的秒数）、`conflict_option`（草稿采用的冲突选项落在这里）、`dip_starts_before_in`（出点所在 dip 在入点或之前就开始，结束在它之前就没有内容了）、`no_recovered_frame`（入点所在 dip 一直到文件末尾，没有恢复帧可移）、`max_moves`（规则移动次数用完）。`qa_precheck.dip` 给出最终点是否仍在 dip 内；`qa_precheck.burned_caption` 按 QA 的判法给出：边缘帧是源镜头切换（`kind: shot`）时，规则仍停在这一帧，但预检与 QA 一样报 `warn`。真实素材：wear 段入点原在 3748 帧（124.95 s，dip 谷底附近，成片以约 0.2 s 从黑场淡入开头）；能量谷止于 125.16 s，移到 3754 帧（125.15 s）不切语音（ASR 短语起点 125.10 s 只是近似），所以入点移到 125.15 s。移动后入点距能量谷终点（语音起点）只剩 0.01 s，小于 `min_lead_in`（0.05 s），`notes` 提示听首字：任何规则移动后，入点距语音起点不足 0.05 s 时都这样提示（移动没有切到语音，但首字起音可能被切）。
- **出点规则**：出点（不含帧）前 0.5 s 内有字幕变化 → 移到变化帧（出点帧本身就是变化帧视为对齐，与入点对称：其前 0.5 s 内若还有变化，**不再移动**出点，只在 `notes` 与 `evidence.out.closing_caption`（`out_frame`、`previous_change_frame`、`previous_change_seconds`、`shown_seconds`）提示“结尾字幕仅显示 x s”。理由：真实素材 hook 段语音止于约 60.04 s，出点先从谷底 1804 帧移到 1803 帧（60.1 s 的下一行）是对的；若再按 1789 帧（59.633 s，正在说的这一行的换行）移动，会切掉 0.39 s 语音并变成 needs_decision）；结尾那段镜头若属于下一镜头（切换发生在语音结束后、或出点后的部分多于出点前、或为闪切）→ 移到切换帧。
- 所有点写为帧中点 `(n+0.5)/fps`；`evidence` 给出短语、谷（范围、最低值、深度）、每次移动的规则与原因，以及按 QA 现有判定（`judgeCutPoint`、`judgeFragment`）在帧网格上的预检结果。有冲突的边，`evidence.in`/`out` 描述草稿最终采用的边：`uses` 为所选选项，`semantic_anchor_seconds`、`energy_valley`、`valley_frame`、`moves` 取自该选项（`drop_*` 为相邻短语的锚点、谷与移动；`cut_at_change` 为变化后的谷、由它得到的帧、到变化处的移动加上从谷出发的移动；`keep_speech` 为越限之前的移动），规则本身的原始候选另列在 `rules_candidate`。
- **冲突**：某次移动切掉的语音超过 0.25 s（`speech_tolerance`）时不静默取舍，beat 记为 `needs_decision`，列出 `keep_speech`（保住语音，接受旧镜头碎片/旧字幕）、`cut_at_change`（从变化处开始；其后 0.3 s 内有比周围低 ≥ 8 dB 的谷时落到谷里，即在词间切、丢掉前几个字）、`drop_first_phrase` / `drop_last_phrase`（改从下一短语开始或到上一短语结束）。草稿默认用干净的 drop 选项（整句删除不会留下半个字，短语仍是语义单位），否则干净的 `cut_at_change`，否则 `keep_speech`，并在 `draft_uses` 写明。beat 可写 `prefer: "keep_speech"` 或 `"cut_at_change"`（0.12.0）：人事先决定，该 beat 的冲突草稿直接用这个选项（出点在已定入点之后算，前后一致），冲突仍列出并带 `decided_by: "prefer"`，但不算待决，beat 为 `suggested`、`apply-cuts` 无需 `--choose`。用途：混剪/画外音素材里口播本来就跨镜头切换，默认的整句删除会把 beat 剪得只剩零点几秒（真实素材 `byq-velvet-03` 的收尾段由 4.4 s 缩到 0.67 s）。≤ 0.25 s 的移动写进 `notes`，提醒听首字/尾字。
- **音量**：区间积分响度调到 −14 LUFS 的线性增益，上限 1（`volume.suggested`），同时给出真峰值与增益后峰值。
- **证据**：`evidence.phrases` 是草稿所用的短语；`evidence.option_phrases` 是任一选项可达范围内的全部短语（供 `apply-cuts` 按最终选择取证据）。
- **草稿**：`draft.items` 是可直接放进 v2 spec 的 media item（`asset_id` 默认 `ASSET_ID`，需替换），从 0 帧首尾相接，`frames = round((出点 − 入点) × canvas_fps)`，`canvas_fps` 默认取素材帧率。仍有冲突的 beat，其 item 带显式标记 `needs_decision: true` 与 `decisions: [{edge, draft_uses, options}]`，`draft.needs_decision` 列出这些 beat；EditDocument v2 校验拒绝这两个键，所以必须人工决定后才能用（用 `apply-cuts --choose` 落实，不必手算帧），不会被静默套用。CLI 摘要的 `status` 此时为 `needs_decision`，`needs_decision` 字段列出每个 beat 的待决边与选项。

### apply-cuts：落实决定，生成 v2 items 与计划 beat

`needs_decision` 的 beat 不再需要手算帧：每个待决边用 `--choose BEAT.EDGE=OPTION`（如 `--choose hook.out=keep_speech`，可重复；EDGE 为 `in`/`out`，OPTION 为该边 `conflicts[].options` 里的 id）选定，该边取选项自带的 `frame`/`seconds`（帧中点），其余边用建议值。所有 item 按 `draft.items` 顺序从 0 帧重新首尾相接，`frames = round((出点 − 入点) × canvas_fps)`，去掉 `needs_decision`/`decisions` 键，可直接放进 v2 spec（`asset_id` 仍是 BEATS.json 给的；占位 `ASSET_ID` 会在 `notes` 提醒）。拒绝（报错、不写文件）：仍有待决边未选（错误里列出每个边的选项与草稿默认）、beat/选项 id 不存在、对没有待决的边下选择、对没有可用范围的 beat（`unmatched`）下选择、同一边选两次、选后出点不在入点之后；以及入点选了草稿以外的选项，而该 beat 出点也有待决、或出点距任一入点不超过 `shot_window` + dip 最长时长（1 s + 1.5 s = 2.5 s）：出点和它的选项是在草稿入点之后算的（出点的镜头规则与 dip 规则都只看入点之后的变化），换了入点可能不再成立，需按新入点调整 beat 范围重跑 `suggest-cuts`。没有可用范围的 `unmatched` beat 不进 items，列在 `skipped`。所选范围与草稿不同、且音量确有测量值（有音频、区间不短于 400 ms）的 beat，`notes` 提醒音量是在草稿范围上测的。

**直接写出计划与剪辑稿**（0.12.0）：`--plan-template PLAN.json --plan-out NEW_PLAN.json` 以手写的计划头（`plan_id`、`brief_ref`、`output`、`delivery_promises` 等；`beats` 会被替换）生成完整的 production plan，整份按 `production-plan.schema.json` 校验；beat 不完整（缺 role/purpose 等）或校验不过时拒绝，不发明字段。`--spec-template SPEC.json --spec-out NEW_SPEC.json` 以 v2 spec 头（`project_id`、`canvas`、`assets`、`tracks`，可含其他轨道的 item）生成 spec：applied item 所在轨道（默认 `v_main`）上的 media item 全部替换，其他轨道（如图形轨、字幕轨）原样保留，跑出新时长的保留 item 写进 `notes`。拒绝：该轨道上有非 media item（applied 片段从第 0 帧首尾相接填满该轨，留着必然重叠，请移到其他轨道）、保留的 item 关联（`link.item_id`）到该轨道被替换的片段（时间按旧剪辑算的，需按新剪辑重做字幕）、轨道不存在或 `locked`、模板 `canvas.fps` 与排布 item 用的帧率不同、`asset_id` 不存在（占位 `ASSET_ID` 提示在 BEATS.json 里设 `asset_id`）。之后用与 `create` 相同的检查（`prepareProject`：探测并对每个素材做完整 SHA-256，不复制、不写入）校验；代价是素材较大时这一步要读完整个文件，之后 `create` 还会再读一次（暂未缓存）。两对参数都必须成对给；所有输出（含 applied 结果）都必须是新文件且互不相同，**全部生成并校验通过后才写**：先写临时文件，再用 `link` 放到目标路径（目标已存在时报错、绝不覆盖；大小写不敏感文件系统上两个只差大小写的名字也在这里报错），任何一步失败都删掉已放置的文件与临时文件。计划的语义校验（证据落在选段内等）仍由 `video-record`/`validate` 在记录时完成。

输出 `creative-craft.applied-cuts.v1`：`{schema, analysis, cuts: {path_basename, sha256}, canvas_fps, choices: [{beat, edge, option, frame, seconds, draft_used}], items, plan_beats, plan_status, plan_errors?, plan_beats_incomplete?, skipped?, notes}`。items 与 suggest-cuts 草稿用同一个首尾相接函数（`backToBack`）排布。

`plan_beats` 是 `production-plan.schema.json` 的 beat：`source_kind: footage`、`duration_seconds`（item 帧数 / canvas_fps）、`generation_ref: null`、`locked: false`，`selection` 为 `{asset_ref: asset_id, source_start_seconds, source_end_seconds, evidence, reason, status: candidate}`；`evidence` 是最终范围内的 ASR 短语（≥ 50% 落在范围内，同范围 beat 的覆盖口径）：`{modality: asr, start_seconds, end_seconds, excerpt: 短语文本, raw_score: null, method}`。短语来自 `cuts.json` 每个 beat 的 `evidence.option_phrases`（suggest-cuts 记录任一选项可达范围内的全部短语，所以选了与草稿不同的选项也能找回被丢的短语；旧文件没有该字段时，用草稿短语加 drop 选项列出的短语）。`role`/`purpose`/`requirement`/`hard_constraints` 只取 BEATS.json 给的；缺少时**不编造**，beat 里不写这些键，`plan_beats_incomplete` 与 CLI 输出列出缺哪些。每个 beat 都按 schema 文件本身的 `$defs.beat`（`json-schema.mjs`，只实现 shared schema 用到的关键字，遇到不支持的关键字报错）与计划语义规则（区间终点晚于起点、证据在区间 ±2 s 内；从 `creative_craft_contracts.py` 的 `validate_production_plan` 照抄，以 Python 为准）校验。计划问题（如 beat id `01_hook`/`开场` 不合 id 规则、超过 600 s、ASR 文本为空）**不影响 items**：仍写出文件、CLI 正常退出，`plan_status` 为 `valid` / `incomplete`（只缺计划字段）/ `invalid`，`plan_errors` 与 CLI 摘要列出每个 beat 的问题；只有 items 本身建不出来时才报错退出。smoke 再用 Python jsonschema 校验一次。

真实素材（`byq-cushion-05`）：新 `cuts.json` 无待决，直接 `apply-cuts` 得到 hook 97 帧（56.883333–60.116667 s）、texture 92、test 121、wear 200 帧（入点 125.15 s）；旧 `cuts.json`（hook 出点待决）不带 `--choose` 被拒，`--choose hook.out=keep_speech` 得到 hook 97 帧、证据含“无滤镜。”。BEATS.json 补上计划字段后生成的 4 个计划 beat 通过 schema 与 `validate_production_plan`。

### 实测与限制

在 4 条真实口播素材（30 fps；含背景音乐垫底、多镜头混剪、重音乐直播片段）上，对 9 个人工多轮修订后的入点做了只读验证（素材、转写与结果只放临时目录，未入库）：7 个建议入点与人工值同帧或差 1 帧（无冲突）；一个粗范围起点早于源镜头切换，报告冲突，草稿所用选项与人工最终值同帧；一个开头是 0.63 s 短镜头，报告冲突；空格细分后“对不起了”成为独立短语，草稿默认的 `drop_first_phrase` 落在其后的能量谷内，与人工值差 1 帧。人工出点本身风格不一（有的紧贴语音，有的留 0.4 s 尾音），建议出点与之相差 0–6.5 帧。

限制：短语时间来自 ASR 词元时间戳（中位误差约 0.1 s，个别离群到秒级）；空格细分依赖空格两侧确有能量谷，无谷时不拆；能量停顿细分的文字划分是按时间估计的；字幕检测是帧差启发式，画中画、手部入画可能被当成字幕变化，构图相近的镜头切换可能漏检为镜头（但仍会作为字幕变化出现）；能量谷只看能量，不区分换气与语音；阈值只在上述素材上标定。

## 合成测试输出保留

默认 `npm run smoke` 在成功写入 summary 后自动整理 `dist/local-production`：
只识别时间戳命名且 summary 明确标识 synthetic/passed 的运行，保留最近两轮
完整输出，旧轮删除已知媒体/图片/字体文件，保留不超过 1 MiB 的 JSON、HTML、
文本、JS 和字幕报告。报告引用的旧大文件可能已退役，重现需重新运行测试。
失败、无 summary、未知文件、symlink、`.keep` 标记和被占用的目录不删除。
真实素材、图像工程及其他 dist 目录不在范围内。

```sh
npm run retention           # 只读计划，含文件清单和预计回收字节
npm run retention -- --apply # 重新规划并执行相同策略
```

默认 smoke 和执行清理共用 `.retention.lock`，冲突直接失败；异常退出遗留锁
须先核对 owner.json 的 PID，再人工处理，不会自动抢锁。占用检查依赖 lsof，
不可用或判断不明时保留。清理失败会让命令非零退出，不能撤销此前已删除文件。
这是受信任本机用户的测试保留机制，不防御其他非协作进程的恶意文件替换。
显式指定的自定义 smoke 输出不自动清理，且必须位于受管目录之外。
