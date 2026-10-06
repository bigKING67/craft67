# 自有报告独立验收复测（2026-09-20）

结论：`PASS_BOUNDED_AUTONOMOUS_NATIVE_E2E`。修复后的同类独立自然语言任务，在 972.505 秒内正常完成并输出最终答复，没有超时或父会话研究补救。该结论仅覆盖本次 Apple 历史研究案例与交付链，不等于所有公司的研究能力或投资结论均通过。

## 验收条件

从空工作目录启动独立 Codex 会话，冻结 75 个 Skill 文件，初始与全局安装逐文件一致。沿用上轮研究目标、截至 2025-11-01 的历史事实边界和 1200 秒窗口；不提供财务答案、来源文件、旧工作区材料或父会话修复脚本。匿名公开取证允许；账户、交易、发布、修改共享工具与子代理均禁止。运行期间候选、全局安装及共享投资工具哈希不变。

## 父会话复核

| 项目 | 结果 |
|---|---|
| 独立会话正常结束及最终答复 | PASS，exit=0，timeout=false |
| 研究核心 status | valid=true、complete=true |
| 10 个引用来源原件 SHA-256 | 全部一致 |
| 15 个交付产物的 bytes/SHA-256 | 全部一致 |
| 带 macOS Seatbelt 的 sealed snapshot 回读 | PASS |
| verify-all | PASS，无 pending/orphan/transaction 警告 |
| 完成账本 verify --artifacts | PASS |
| 归档 HTML/PDF 与 render-validation 绑定 | 逐字节一致 |
| 证券身份与截止时间 | AAPL、NASDAQ、US-NASDAQ:AAPL、2025-11-01T23:59:59-04:00 完整保留 |
| revision 文件只读 | PASS |

这次不再出现预览与归档重渲染导致的 seal 哈希冲突，也没有 YAML 元数据缺失。研究核心记录 93 条计算回执和 3 条三表勾稽；研究证据仍为 PARTIAL，主要包括财务独立双源、早年债务与实际股数、完整治理/问答范围、历史可比估值与股数/净现金时间桥等缺口，均明确限制为条件研究。

## 自主纠错与限制

不是无错误的一次执行。会话自行处理了 SEC 抓取失败、研究输入缺项、视觉路由参数和 archive 审计输入类型错误。归档第一次传入 verdict object，而接口需要 audit result array；原失败产物保留于任务 failures 目录，纠正输入并显式 retry 后完成。没有修改共享代码、降低门禁或父会话介入。

报告为 7 页。独立会话实际检查全部 PDF 页与 1440×1000、390×844、深色浏览器截图；父会话抽查封面、估值、末页，并复核产物绑定。末页留白、跨页表格和未覆盖完整键盘/屏幕阅读器验收仍记录为限制。报告保留生成时的预览状态文本，正式 seal 状态以外部回执和 revision 为准，不能将页面文本当作封存证明。浏览器清理回执为任务页关闭并验证 1 个，残留 0、错误 0。

本轮没有继续改实现或安装。工程验收通过与研究证据完整性是不同状态，不改写上轮超时结果，不给研究强行补 PASS。

## 证据与产物

- 全部原始执行及父复核：`local/skill-evals/20260920-native-full-host-v2/`
- HTML/PDF：上述目录的 `host/workspace/report/report.html` 与 `report.pdf`
- 正式隔离档案：`host/workspace/archive/AAPL-Apple/2025-11-01/revisions/r0001/`
- 结构化结论：`acceptance/native-full-host-v2-review-20260920.json`

后续优先回到研究核心的数据缺口与不同市场压力案例；本次通过不足以解除应用延期原则。审计数组与 verdict 对象易混淆，记录为入口易用性改进候选，不追改本次冻结验收。
