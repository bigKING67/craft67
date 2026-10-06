# 从商品照片开始一个可编辑工程

`create-photo` 把一张完整照片与独立文字放入普通图片工程。只需 `project_id`、`source`、`headline` 三个字段；可选 `brand`、`caption`、`title` 和 `canvas`。默认白色画布为 1280 × 1600，上方 320 px 放文字，下方按原尺寸居中放照片，照片对象默认锁定。

适用于希望保留整张商品照片、先做文案与版式的起稿。照片内的背景、阴影、包装文字都会保留；它不会自动分割商品、换背景或补边。白底与照片边缘是否衔接自然仍需查看导出图。

## 经授权裁边后再排版

默认保留整张照片。用户明确允许裁边后，使用 `crop-photo <新输出目录> <输入.json> [--dry-run]`，输入示例：

```json
{
  "source": "/absolute/product.png",
  "source_sha256": "替换为原文件的64位SHA256摘要",
  "crop": { "left": 560, "top": 445, "width": 880, "height": 1525 },
  "authorization": {
    "user_approved": true,
    "context": "用户明确允许裁外围白边，完整保留口红及瓶盖，不缩放"
  }
}
```

上述坐标仅适用于已验证的口红图，不用于其他素材。坐标原点是 **EXIF 方向纠正并转为 sRGB 后**照片的左上角，单位为整数像素；`source_sha256` 则绑定原始编码文件。先确认用户授权、查看原图并选定矩形，再填写授权说明；布尔字段只是调用方声明，不是权限认证或用户授权的自动证明。工具不会识别白边、判断商品边缘或推断允许裁切。

```sh
node cli.mjs crop-photo /absolute/new-crop /absolute/crop-input.json --dry-run
node cli.mjs crop-photo /absolute/new-crop /absolute/crop-input.json
```

dry-run 不写文件，实际执行保存 `original.<format>`、`normalized.png`、`cropped.png` 和 `receipt.json`，摘要、裁切矩形与保留区域像素检查均在回执中。输入失效、边界错误、非整数坐标或已占用目录都会拒绝，普通写入失败清理本次新建目录；强制终止可能残留，不代表成功。裁切无重采样，像素一致是相对规范化原图的同一矩形，不代表整张原照片仍在成品里，也不证明商品完整；需要看图确认边缘与阴影。

将 `cropped.png` 路径作为 `create-photo` 的 source，仍先预检模板尺寸；较高裁切图可能需要更大的同宽高比画布。交付时保留整个裁切目录和工程：工程绑定裁切 PNG，裁切回执另绑定原文件，不会自动嵌入工程历史。已有工程用 `add_asset` 添加裁切图，独立解锁、修改照片引用和几何、锁回；原素材和旧修订保留，不覆盖原图。透明裁切可用于通用 `create`，整图模板仍只接受不透明照片。

验收见真实口红裁切与模板衔接（本机证据，未入库：`../../dist/image-controlled-crop-2026-10-05/README.md`）。

## 可复用用途模板

在 `create-photo` brief 中加入 `template`，复用清透金色版式：`brand-detail` 为详情页／品牌展示首屏（默认 1600×2000），`xiaohongshu-cover` 为图文封面（默认 1344×1792）。这是已验证的创意版式，不是平台强制规格，也不生成完整详情页。两者要求 `brand`，不接受 `caption`；未指定 `template` 时原有白底入口不变。

```json
{
  "project_id": "new-product-cover",
  "source": "/absolute/product.png",
  "brand": "GROLAND",
  "headline": "让光停留，\n映见清透",
  "template": "xiaohongshu-cover"
}
```

仍用下面的 `create-photo --dry-run`、`create-photo` 和 `render` 命令。输出是普通可编辑工程；返回的 `layout.template`、`template_version` 和 `slot` 标明模板与照片区域。标题按原文排版，不自动补标点或改成示例文案。

模板以画布比例计算文字、细线和照片区域，再按真实照片尺寸居中。默认两种版式的照片区域均为 1254×1254；较小照片保持原尺寸，不放大。超出区域会失败，可明确提供更大的同宽高比 `canvas`；仅模板几何和字号随画布变化，照片始终保持原尺寸。错误比例、透明照片、缺字、文字溢出或缺少品牌都不会发布工程。小照片可能留白过多，横竖照片也须实际看图，不能把“装得下”当作视觉合适。

### 画布底色与照片边缘

照片自带背景时，画布底色若与照片边缘不同，会留下可见的矩形框（如米色模板配白底商品图）。brief 可加 `"background": "#RRGGBB"` 明确指定画布底色；不指定时模板仍为 `#f5f2eb`、默认入口仍为 `#ffffff`。`--dry-run` 与创建结果的 `layout.photo_edges` 报告照片上/下/左/右一像素边的平均色 `mean` 与最大通道差 `spread`：`spread` 接近 0 的边与同色画布可无缝衔接；渐变或含商品的边（`spread` 大）无论选什么颜色都会留线，需改裁切或接受。工具只报告，不自动取色、不延展照片像素；文字颜色不随底色变化，深色底须另行检查对比度。已有工程可用 `set_canvas` 改底色。

示例见 [brand-detail-brief.json](examples/brand-detail-brief.json)、[xiaohongshu-cover-brief.json](examples/xiaohongshu-cover-brief.json)。模板验收（本机证据，未入库：`../../dist/image-purpose-templates-2026-10-05/README.md`）包含原商品逐字节复现和合成异形图片验证，尚无第二个真实商品的视觉批准。

## 准备和创建

在源码 checkout 中进入 `integrations/image-production`。Node.js >=22、固定依赖和字体的首次准备见 [README 安装说明](README.md#安装与最短验证)。已准备过无需重复安装；下面的创建和渲染过程只在本地运行，不读取全局 URL/key，也不调用模型。

复制 [photo-brief.json](examples/photo-brief.json)，将 `source` 改成自己的**绝对本地路径**，并替换文案。支持单帧 PNG、JPEG、WebP；每个像素都须完全不透明。源文件和路径组件不能是 symlink（文件系统根目录下的系统别名如 macOS `/tmp`、`/var` 会先解析）。工程和导出目录须是尚不存在的新目录，其父目录须已存在。

```json
{
  "project_id": "product-photo",
  "source": "/absolute/path/to/product.png",
  "headline": "光，沿着瓶身流动。"
}
```

```sh
node cli.mjs create-photo /absolute/new-project /absolute/photo-brief.json --dry-run
node cli.mjs create-photo /absolute/new-project /absolute/photo-brief.json
node cli.mjs read /absolute/new-project
node cli.mjs render /absolute/new-project /absolute/new-export
```

`--dry-run` 返回计划文档、素材摘要、坐标和文档摘要，检查真实字体排版，不创建工程、素材或临时文件。随后输入和字体未变时，创建得到相同文档摘要。预检成功不代表创意已获批准；完整导出在 `new-export/image.png` 和 `image.svg`，回执单独保留。

照片按 EXIF 方向纠正并归一化为 sRGB 后，以 1:1 尺寸放置，既不缩放也不裁切；工程同时保存原始编码文件。这里的像素保真指**完整导出中照片区域相对归一化素材的 RGBA 一致**；`preview` 的缩小图不承担逐像素保真保证。

## 尺寸与文字放不下时

默认照片可用区域为 1280 × 1280。大图会报错并提示最低画布尺寸，可在 brief 中明确加入：

```json
"canvas": { "width": 1600, "height": 1920 }
```

这段是可选字段片段，应放进完整 JSON 对象。宽度范围为 640–8192，高度为 384–8192，总面积最多 16,777,216 px；需同时满足宽度 >= 照片宽度、高度 >= 照片高度 + 320。标题固定 70 px，品牌及副文案固定 22 px；文字放不下会报 `Text overflow`，应在用户已允许的范围内调整文案或画布；两者都固定时报告约束冲突。不会自动缩字、截断或隐藏文字。缺字、未知字段、透明照片、占用的目标目录都会失败且不发布工程。

其他比例、透明商品图层或更自由的布局使用原有 [`create` 对象入口](README.md#agent-工具入口)。此模板也不承诺任意照片和文案都能在默认版式里获得好的视觉效果。

## 改字与撤销

对象 ID 固定为 `photo`、`headline`，可选文字为 `brand`、`caption`。保存以下内容为 `edit.json`，确认 `base_revision` 与 `read` 当前修订一致后执行。照片仍保持锁定。

```json
{
  "base_revision": 1,
  "author": "human",
  "summary": "修改标题",
  "operations": [{ "type": "update_object", "id": "headline", "patch": { "text": "让光停留" } }]
}
```

```sh
node cli.mjs edit /absolute/new-project /absolute/edit.json --dry-run
node cli.mjs edit /absolute/new-project /absolute/edit.json
node cli.mjs render /absolute/new-project /absolute/new-export-v2
```

`edit --dry-run` 与实际提交均检查操作、锁、文档结构和最终可见文字的排版；复用导出的字体与测量逻辑，文字溢出或文本框小于单字宽度会在保存素材、修订前失败。可以在同一批次里改文案并调整文本框，以整批最终结果为准；隐藏文字在显示时才检查排版。失败后当前版本保持，可在用户约束内调整批次再预检，不自动缩字、删改文案。仅显式、独立的解锁操作跳过排版测量，便于修复旧工程中已锁定的溢出文字。修改后仍需渲染查看遮挡、照片边界和整体效果；预检不代表视觉批准。

撤销本次修改时，另存 `undo.json`，使用 `base_revision: 2`、`author: "human"`、`summary: "恢复初始文案"`，以及 `operations: [{"type":"revert_to","revision":1}]`，再运行 `edit`。撤销生成修订 3，保留完整历史。移动工程时需携带整个目录（素材、字体、修订），不要只保存 PNG；执行器仍来自本源码模块。

## 同一工程交付多个比例

已有工程先 `read`，保留人工文案、对象 ID、素材和字体，通过 `edit` 改画布与对象坐标。不要重新执行 `create-photo` 覆盖工程，也不要把缩放成品 PNG 当作可继续编辑的多尺寸版本。建议在完整工程副本上试排；每个成品保存到不同的新导出目录，回执绑定对应修订。当前工程依次记录各版，尚无并列画板或一键多尺寸命令。

先区分**比例**与**确切像素尺寸**。例如当前 GROLAND 照片为 1254×1254；在保持原尺寸、整图不裁切和上方文字区的条件下，以下三组通过了实测：

| 比例 | 本例画布 | 照片左上角 | 照片尺寸 |
| --- | --- | --- | --- |
| 1:1 | 1600×1600 | (173, 333) | 1254×1254 |
| 4:5 | 1280×1600 | (13, 333) | 1254×1254 |
| 9:16 | 1296×2304 | (21, 685) | 1254×1254 |

这些是本张素材的验收尺寸，不是平台规格。另一张图需按归一化后的宽高重新计算并预检。1080×1080、1080×1350、1080×1920 都容不下这张照片的原生宽度：创建预检会提示尺寸不足，已有工程编辑会因对象越界失败，均不发布修订。若用户指定 1080 px 宽，必须先明确允许缩放，或改用更大尺寸；不能以“比例正确”替代尺寸要求，也不能承诺缩放后仍逐像素相同。当前入口不会自动选择折中方案。

照片锁同时保护内容和位置。已授权重排需要三个独立批次：**解锁 → 修改画布和位置 → 重新锁定**，每次先读取最新修订、dry-run 再提交。不要把解锁混在布局批次里；中间发生失败时先 `read`，当前画面保持上次成功提交的版本，但照片可能仍处于已解锁状态，应显式锁回或修复后锁回，不交付中间状态。

例如对上表的照片和包含 `brand`、`headline`、`caption` 的工程，9:16 的布局批次如下。`base_revision: 2` 仅适用于修订 1 已完成独立解锁的情况，实际值以 `read` 为准；缺少可选文字对象时删去对应操作。

```json
{
  "base_revision": 2,
  "author": "human",
  "summary": "重排为 9:16，保留照片原尺寸及全部文案",
  "operations": [
    {"type":"set_canvas","canvas":{"width":1296,"height":2304,"background":"#ffffff"}},
    {"type":"update_object","id":"photo","patch":{"x":21,"y":685}},
    {"type":"update_object","id":"brand","patch":{"x":81,"y":432,"width":1134}},
    {"type":"update_object","id":"headline","patch":{"x":81,"y":488,"width":1134}},
    {"type":"update_object","id":"caption","patch":{"x":81,"y":627,"width":1134}}
  ]
}
```

独立解锁/锁回分别使用 `operations: [{"type":"update_object","id":"photo","patch":{"locked":false}}]` 和 `locked:true`；保留完整批次的 `base_revision`、`author`、`summary`。布局变更后仍需检查文字、照片接边、留白及渠道安全区，排版预检不会判断这些视觉问题。本例 9:16 将文案和照片整体放在画布中部，未修改文案、字号或商品内容。

**重新导出旧版式不需要撤销。** 用 `read <project> <revision>` 确认版式，再指定修订导出到工程外的新目录；回执绑定该旧版的修订与摘要，当前工程和锁状态保持。例如历史修订 6、9 分别保存了方图和 9:16 时：

```sh
node cli.mjs render /absolute/project /absolute/new-square-export --revision 6
node cli.mjs preview /absolute/project /absolute/new-portrait-preview --revision 9
```

不传 `--revision` 仍导出当前版；修订不存在、缺少参数或非法参数会在创建输出目录前失败。`preview` 仅供缩小查看，保真交付用完整 `render`。

**需要把当前版式恢复成旧版时，才使用撤销。** 照片已移位且锁回时，直接 `revert_to` 旧位置会被拒绝。应记录要恢复的修订，独立解锁、单独 `revert_to`，再锁回；撤销不删除历史。

2026-10-05 实测产物与复现脚本见 dist/image-photo-sizes-2026-10-05-3e09f512（本机证据，未入库：`../../dist/image-photo-sizes-2026-10-05-3e09f512/README.md`）。三规格逐像素、解锁/锁回、撤销、搬迁重渲染与尺寸不足的拒绝路径分开记录；不代表抠图、缩放保真、渠道规范或品牌创意批准。

对应的多规格可编辑交付包与解压验收（本机证据，未入库：`../../dist/image-multisize-handoff-2026-10-05/README.md`）包含完整工程、三规格成品、字体许可和改字/撤销示例。实际 ZIP 已在仓库外中文及空格路径解压，验证历史版本重导出、改字、撤销和照片像素保护；仍需匹配的源码执行器与依赖，仅验证本机 macOS。`dist/` 为本地产物，分享时发送完整 ZIP；修改当前标题不会自动同步到历史版式。

## 一次改文案，同步多个版式

`copy-variants <原工程> <输入.json>` 将同一份文案应用到指定历史版式，并输出各自可继续编辑的工程和成品。先用 `read <原工程> <修订号>` 获取每个版式的 `sha256`，在输入里绑定，避免套用错误来源：

```json
{
  "output": "/absolute/new-copy-set",
  "variants": [
    { "name": "square", "revision": 6, "sha256": "替换为该修订的64位摘要" },
    { "name": "portrait45", "revision": 12, "sha256": "替换为该修订的64位摘要" },
    { "name": "portrait916", "revision": 9, "sha256": "替换为该修订的64位摘要" }
  ],
  "updates": [{ "id": "headline", "text": "让光停留，映见清透" }]
}
```

```sh
node /absolute/source/integrations/image-production/cli.mjs copy-variants /absolute/project /absolute/copy-input.json
```

修订号是这份 GROLAND 工程的例子；其他工程须读取自己的版式修订。输出目录必须不存在且位于原工程之外，相对路径按命令工作目录解析。最多 12 个版式、100 个文字对象更新；版式名不区分大小写去重，每个文字 ID 只能指定一次。只修改所有版式共有且未锁定的文字对象，不自动调整字号、位置或图片。任何版式文字溢出、对象缺失/锁定、绑定不符、导出失败或正常取消，整批失败并清理本次新建输出；已有目标不覆盖。强制杀进程或断电不保证清理，残留目录不可视为成功，应检查根 `manifest.json` 和各导出回执。

每个版式包含 `project/` 和 `export/`。派生工程 r1 是来源快照，r2 是改稿，之后沿用 `read`、`edit`、`render` 和 `revert_to`；来源完整历史仍留在原工程，批次 `manifest.json` 记录来源与成品摘要。原工程不会被更新。这是显式批量改稿入口，不是多个工程间持续自动同步。

真实三规格验收见同步改稿结果（本机证据，未入库：`../../dist/image-copy-variants-2026-10-05/README.md`）。

## 补充像素检查脚本

需要额外逐像素检查时，复用执行器已安装的依赖，从包入口解析，不猜测 `node_modules/sharp/lib/index.js` 等内部路径。工作区里的 `.mjs` 脚本可使用以下写法，先将路径替换为已核实的源码执行器路径：

```js
import { createRequire } from 'node:module';
const sharp = createRequire('/absolute/source/integrations/image-production/package.json')('sharp');
```

受限工作区中，将脚本和日志写到允许的新路径，使用 `node verify.mjs > verify.log 2>&1` 并检查退出码；不要把 `node ... | tee ...` 的成功当作验证程序成功。需要比较文件清单时，先分别保存到工作区内的两个文件再比较，避免依赖可能受限的 heredoc 临时文件或 `diff -`。这些是辅助检查的执行方式，不改变工程或导出合同。

回执的 `document_sha256` 绑定导出目录中 `document.json` 的原始文件字节，包含缩进与换行。核对时直接读取文件 Buffer 计算 SHA-256；不要先 `JSON.parse` 再 `JSON.stringify`，重新序列化会改变字节并造成误报。PNG/SVG 摘要同样按实际文件字节核对。
