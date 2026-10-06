# 古籍局部字样盲审包

包编号：`bazi-timing-blind-review-v1`。本包包含五张匿名局部影像，其中混有目标案例和校准案例；审读者不会得知二者的身份、原书、版本、页码、现有候选读法或其他审读者的回答。

请只使用本目录，不要查看仓库中其他文件、影像元数据、搜索引擎、OCR 或协调人答案键。每位审读者独立作答，提交前不要相互讨论。这个隔离是工作流约束，不是密码学保密；若审读者能访问完整仓库，协调人应另行复制本目录后再发送。

## 审读方法

五张图均为传统竖排：栏位从右向左，栏内从上向下。`packet.json` 为每个案例标出“自右数第几栏”作为焦点栏；图上的细红框标出本轮需要机器比对的局部字串，但不提供候选读法。红框是统一的定位标注，未覆盖或修改框内字形。

1. 先逐字转录焦点栏中可见的全部文字，再单独转录红框内全部可见文字；不补全裁切边缘之外的内容。
2. `focusColumnLiteral` 保留可辨的异体字、繁体字与印刷标点；空白不计入正文。
3. `focusSpanLiteral` 只填写红框内字样，仍保留可见标点；`focusSpanNormalized` 遵守与整栏相同的规范化规则。
4. 一个无法辨认但确定存在的字写作 `□`；红框内有任何疑字时，把 `focusSpanHasUncertainty` 设为 `true`，并在 `uncertainPositions` 说明。
5. `focusColumnNormalized` 和 `focusSpanNormalized` 只允许去除空白或统一明显的排版标点，不得简化汉字、改写语序或据上下文校正字词。不需要规范化时与对应字面转录相同。
6. 相邻栏只用于判断阅读顺序和裁切边界；必要说明写入 `neighboringColumnNotes`。
7. 不猜原书、版本、年代或“通顺的原文”。本任务只问图上实际印了什么。

## 回收格式

复制并填写 [response-template.json](response-template.json)。`glyphConfidence`、`punctuationConfidence` 使用 `high`、`medium`、`low`；`imageSufficiency` 使用 `yes`、`partial`、`no`。每个不确定位置至少记录：从焦点栏顶部可见首字起算的 `sequenceIndex`、观察到的字形、候选字、置信度和理由。协调人裁决器使用红框字段比较同一位置，整栏字段用于检查上下文与转录边界。

提交前确认：

- 五个案例均有回答；
- 每例都填写整栏与红框两组字面/规范化字段；
- `reviewedWithoutAnswerKey` 与 `reviewedWithoutOtherReviewerResponses` 为 `true`；
- 如使用过 OCR、网页、其他版本或他人意见，必须把 `usedOcrOrExternalLookup` 设为 `true` 并说明；
- 不在文件中加入来源猜测。

协调人应至少收集两份相互独立的回答；存在高置信冲突、图像不足或校准失败时，收集第三份。答案键和裁决门槛位于本目录之外，不随本包发送。
