# 五类论证整段复用门禁

日期：2026-09-25。结论：报告校验此前只确认八字与紫微各五个主题存在、引用合法，却允许同一候选的五项用同一组通用文字填充。现在同一候选、同一体系内，任意两个主题若把 conclusion、counterReview、conditions、alternatives 四项整段复用，会以 `DUPLICATE_REASONING_NARRATIVE` 拒绝。

## 范围与误伤控制

比较前只去掉首尾空白并折叠连续空白，四个字段必须全部相同才会命中。单个共同结论、共同成立条件、同一事实或同一规则仍可复用；八字与紫微不交叉比较，不同候选也不交叉比较。这是一条防止模板占位的结构门禁，不尝试用关键词或文本相似度判断论证好坏，也不能识别只改少量措辞的近似重复。

现有 22 份 `examples/acceptance/**/report.json` 扫描结果为 0 组重复，所以没有改写冻结报告或历史 Skill 快照。测试夹具原本故意用同一模板填满各主题；已改成按 topic 区分，并加入八字、紫微两条直接回归，分别验证空白变体仍会拒绝、只共享一个字段继续允许。既有双候选回归同时证明相同主题文字可以出现在不同候选，不会串候选误报。

## 验证边界

- `npm run check`：175/175 PASS；TypeScript strict 与 build PASS。
- 构建版 CLI 对注入整段重复的报告退出 1，并返回 `DUPLICATE_REASONING_NARRATIVE`；临时文件已删除。
- 23 份 semantic-forward manifest 由当前构建版逐份重放成功，23 份均因缺可信 runtime receipt 保持 partial；本轮没有新增第 24 份，因为新行为是 report JSON 的确定性结构拒绝，直接报告回归比复制一份自然语言回答更能证明该门禁。
- Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 81 个现行 Markdown、402 个本地链接无缺失；不读取 private，private 与 node_modules 之外 175 个 JSON 均可解析。
- `openspec/` 与 `.git/` 均不存在；没有全局安装、发布、推送或外部动作。

测试通过只证明整段占位复制会被当前结构校验拒绝。它不证明五项文字真正回答了各自主题，不证明传统规则成立，也不证明命理解释或现实预测有效。
