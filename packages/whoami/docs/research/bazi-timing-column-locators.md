# 八字岁运逐栏坐标与局部影像定位

核验日期：2026-09-26。机器可读坐标见 [bazi-timing-column-locators.json](bazi-timing-column-locators.json)，页级正文见[外交转录](bazi-timing-diplomatic-transcription.md)，锚点进入[版本关系证据矩阵](bazi-timing-stemma-matrix.md)。本层覆盖原有 5 个扫描见证、28 个 PDF 页或跨页、31 个叶面，提供 301 个竖排文本行区域、10 个手工复核锚点和 9 张局部证据图。

最重要的结果不是坐标数量，而是逐栏回看纠正了页级初稿的一处错误：明末本 PDF 第 68 页右叶的“喜陰則”，应按传统阅读次序续接左叶最右栏“辛與酉為好。此皆宜例推以見。”；左叶再下一栏才开始“貞元”。因此该处是完整的跨叶正文，不是无标记中断。转录、校本、来源清单和既有验收记录均已同步更正。

## 坐标合同

- 原点是 300 DPI 页面栅格左上角，单位为像素；每个框使用 `x, y, width, height`，并同时给出相对页面宽高的 0—1 归一化坐标。
- PDF 由 `pdftoppm 26.09.0` 以 300 DPI 渲染。`Tesseract 5.5.3 + chi_tra_vert + psm 5` 只提供 level-4 几何框，OCR 字符没有写入正式转录，也不参与异文裁定。
- `verticalLineRegions` 是导航用竖排文本行候选，不声称逐字框、排字栏绝对复原或影印替代。十个 `anchors` 的字面判断均由人工回看扫描和局部证据图确认；引用时以扫描字形和手工锚点为准。
- 明末双叶扫描分别使用 `right:Rnn`、`left:Lnn`；其余单页使用 `page:Cnn`。编号按从右到左排列，栏内按从上到下阅读。
- 坐标只对 JSON 中登记 SHA-256 的源 PDF 和上述渲染参数成立；源文件或渲染参数变化后必须重建，不能沿用旧框。

## 覆盖

| 见证 | PDF 页 | 叶面 | 竖排区域 | 说明 |
|---|---:|---:|---:|---|
| 世界图书馆本《子平真诠》 | 7 | 7 | 71 | PDF 56—62 |
| 1926 文明书局本《子平真诠》第 2 卷 | 4 | 4 | 48 | PDF 43—46 |
| 明末长庚馆刊《滴天髓》 | 3 | 6 | 47 | PDF 66—68，左右叶分开 |
| 1936《滴天髓辑要》 | 3 | 3 | 33 | PDF 25—27 |
| 1947《滴天髓阐微》 | 11 | 11 | 102 | PDF 501—511 |
| 合计 | 28 | 31 | 301 | 10 个人工锚点，9 张证据图 |

## 人工复核锚点

| ID | 见证定位 | 栏位 | 可见读法与处理 | 局部证据 |
|---|---|---|---|---|
| A01 | 世界本 PDF 61 / 书页 52 | C02→C03 | “亦作清論”跨两栏连续 | [图](evidence/bazi-timing-column-locators/zp-world-61-qinglun.jpg) |
| A02 | 1926 本 PDF 45 / 书页 32 | C12 | “亦作清出”；句法可疑但照见证保留 | [图](evidence/bazi-timing-column-locators/zp-1926-45-qingchu.jpg) |
| A03 | 1926 本 PDF 45 / 书页 32 | C08 | “壬生戌下闕”；明确缺文，不跨本补齐 | [图](evidence/bazi-timing-column-locators/zp-1926-45-lacuna.jpg) |
| A04 | 明末本 PDF 66 右叶 | R06 | “主譬如吾身”；`主` 前未见“日” | [图](evidence/bazi-timing-column-locators/dts-ming-66-zhu.jpg) |
| A05 | 明末本 PDF 67 左叶 | L01 | “大。則運自降。吉。”；可见但句法可疑 | [图](evidence/bazi-timing-column-locators/dts-ming-67-zijiangji.jpg) |
| A06 | 明末本 PDF 68 右叶 | R04 | “喜水則甚利”；与后本“不吉”方向相反 | [图](evidence/bazi-timing-column-locators/dts-ming-68-continuity.jpg) |
| A07 | 明末本 PDF 68 跨叶 | R07→L01→L02 | “喜陰則”续“辛與酉為好。此皆宜例推以見。”；下一栏“貞元” | [图](evidence/bazi-timing-column-locators/dts-ming-68-continuity.jpg) |
| A08 | 1936 本 PDF 27 / 书页 22 | C03 | “喜水則不吉” | [图](evidence/bazi-timing-column-locators/dts-1936-27-buji.jpg) |
| A09 | 1947 本 PDF 510 / 书页 122 | C06 | 原注层“喜水則不吉” | [图](evidence/bazi-timing-column-locators/dts-1947-510-buji.jpg) |
| A10 | 1947 本 PDF 505 / 书页 117 | C08 | “是年進而中”；可见但句法可疑 | [图](evidence/bazi-timing-column-locators/dts-1947-505-jinerzhong.jpg) |

JSON 对每张局部图登记相对于 300 DPI 源页的 `sourceBoxPx`、交付图尺寸、文件字节数和 SHA-256。1936 本证据图为便于仓库存储按比例缩小，源页裁切框仍保留在 `sourceBoxPx` 中；其余证据图保持裁切像素尺寸。

A04、A05、A10 三个疑难读法与 A03、A08 两个校准点已进入[来源隐藏盲审包](bazi-timing-blind-review/README.md)。盲审图只从上述证据图裁切，不旋转、不缩放、不描字；统一增加的细红框只标定位范围，不覆盖框内字形。审读者材料不含见证、页码、锚点、候选读法或案例角色。当前尚未回收外部审读结果，因此原锚点仍保持“扫描内人工可见、外部独立复核待完成”的状态。

## 使用边界

本坐标层用于从版本、页、叶面快速回到局部字形，解决“这句话在何处、跨哪一栏、是否跨叶”的复核问题。它不把 OCR 变成文本权威，也不把古籍说法变成自动吉凶规则。明末本“甚利”与后本“不吉”的相反分支仍禁止合并成确定性算法；文字定位也不能证明命理理论、命例叙述或现实预测有效。
