# UP-01 validation receipt

Date: 2026-09-15 Asia/Shanghai. Local uncommitted implementation on top of `2d33799b939fab61fa842f0dfab420ed19239f19` and the preceding upstream-governance work.

- Full test discovery: 183 tests successful, three existing optional Markdown renderer skips. This batch adds 19 regression methods for unknown/adverse health, review windows, legacy history, calculation failures, citation bindings and research assessment boundaries.
- Source validation: valid, zero warnings/errors. Package validation: all seven checks passed, including temporary installation, packaged/installed self-tests and installed research smoke. No actual user Skill installation occurred.
- JSON Schema: four tracking v2 contracts validated against 16 real temporary workflow outputs; research status and receipt validated against four complete/partial-coverage outputs. Validation dependencies were installed only in a temporary environment.
- OpenSpec strict validation and Git whitespace checks passed.
- Independent scoped review found one P2: new review-date constraints incorrectly applied to sealed v1 history. Fixed by retaining historical validation and treating unusable legacy deadlines as UNKNOWN in current assessments.
- Compatibility was verified using the actual HEAD implementation to create a v1 archive with a deadline predating its thesis. The original and new readers both accepted the same sealed archive; the new current assessment had UNKNOWN freshness and null score, with all archived bytes unchanged.
- Provider-gap completion remains permitted under its existing contract, while assessment reports PARTIAL evidence coverage. Unbound IDs, failed-provider citations and incorrect local paths block completion. Claim support and source freshness remain UNVERIFIED, including old retrieval dates.

These are local, synthetic behavior and package checks. No live provider, real investment conclusion, host installation, application, Windows-host result, commit or push is claimed. Three optional renderer tests remain skipped. Existing HTTP 400/429 fixture cleanup ResourceWarnings did not cause test failures.

## 2026-09-16 收据元数据复核

有界复核 `receipt_status`、状态完成门禁及 finalize 拒绝路径，复现收据 `valid`、`run_id`、`automatic_trading`、`provider_gaps` 变更后仍返回 complete/VERIFIED。现已校验必需字段、完成标志、工作区身份、实际 Provider 缺口、带时区时间及可选 assessment；旧版缺少 assessment 的收据仍兼容。异常收据返回 INVALID，finalize 拒绝且保留现有文件。

同一临时工作区的四组新旧读取器对照见 `acceptance/core-receipt-20260916.json`。研究工作流 23 项、全量 263 项零跳过通过；源码 19 项、包检查 8 项通过。全局副本已备份更新并核对一致。本批不代表全仓审查、收据签名认证或自然语言验收重跑；未提交、推送或发布。

## 2026-09-16 官方证据路径复核

后续有界复核发现 imported 来源的绝对 local_path 可以指向工作区外文件并通过状态检查。现在读取前仅接受导入器为该来源 ID 生成的文件名，并要求扩展名与实际 PDF/HTML 格式一致。四类异常路径在文件读取前被拒绝，正常导入与格式错配另有回归覆盖。

同一夹具的新旧读取器对照及源码绑定见 `acceptance/official-evidence-path-20260916.json`。研究工作流 24 项、全量 264 项零跳过通过；全量运行后补充的格式错配分支已重跑研究工作流 24 项通过。源码 19 项、包检查 8 项通过，全局副本已备份同步。路径与格式校验不证明发行人身份、报告期或正文语义；不宣称并发完整性、全仓或深度安全审查完成。

## 2026-09-16 公开引用 URL 复核

来源 ID 正确但公开链接指向无关网页时，旧读取器仍允许封存并显示 citation_binding=VERIFIED。现已把导入时登记的 URL 纳入引用目标，裸 URL 或单一 Markdown 链接必须精确匹配对应来源；无关 URL、其他来源 URL 和无法明确解析的混合文本阻断。Provider 未登记公开证据 URL 时使用本地证据路径，不能以接口文档替代。

同一已封存工作区的新旧对照见 `acceptance/public-citation-20260916.json`：新版 complete=false、citation_binding=INVALID，再封存被拒绝且所有原文件不变。正确公开链接及本地引用保持可用。研究工作流 25 项、全量 265 项零跳过，源码 19 项、包检查 8 项通过；全局副本已备份同步。URL 一致性不证明网页内容、发行人身份或论点支持；旧报告存在链接错配时须保留历史并在新工作区修正。

## 2026-09-16 研究生命周期 CLI 验收

`tests/test_research_run.py` 增加真实子进程生命周期回归，源码 CLI 与全局安装 CLI 各完成 21 个步骤，见 `acceptance/research-lifecycle-20260916.json`。覆盖初始化、缺证据阻断、三份本地正式材料夹具导入、重复导入保护、URL 错配阻断、纠正草稿后封存、状态复核、幂等封存，以及旧收据兼容和收据/路径/链接/原始字节异常。异常发生在隔离副本中；状态与再次封存均校验预期错误类型，原封存目录及失败副本文件哈希不变。

全量 266 项零跳过、源码 19 项、包检查 8 项通过；全量运行后补充的精确错误类型断言已在两套 CLI 的完整生命周期中复验。源码与全局安装一致，本批只增加测试和验收记录，没有改运行时代码或重新安装。Provider 关闭且覆盖保持 PARTIAL，论点支持和来源时效保持 UNVERIFIED；这是本地合成 `.research` 核心流程验收，不是联网真实研究、内核断网验证或独立正式 money 档案准出。

The implementation adapts the reviewed MyInvestPilot principle that artifact readiness is distinct from investment judgment. It does not copy or validate the upstream engine. Future issuer/reporting-period semantic validation and the professional research loop remain separate work.
