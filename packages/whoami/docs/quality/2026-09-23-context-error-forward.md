# 确定性 context error 与 DST 缺失时间前向验收

日期：2026-09-23。结论：自然语言验收现在可以绑定并重放当前引擎的确定性 context error；纽约 2024-03-10 02:30 的 DST 缺失时间样例正确停机，没有把 `later` 当成自动改为 03:30 的授权。内容复核 PASS；缺少 runtime receipt，最终状态保持 PARTIAL。

## 原缺口

旧验收只接受完整 evidence 或未知时辰的 needs-input chart。核心已经拒绝 DST 春季跳时中的不存在民用时间，但这类错误不能进入自然语言验收，因此无法固定检查宿主是否会在错误后擅自更正时间并继续排盘。

## 实现

- `context` 在提供可解析为整数列表的显式 `--years` 且发生确定性 `InputError` 时，stderr 返回 `whoami.error.v1`，包含命令、年份、错误码和错误说明，退出码仍为 1。非整数、NaN 或无穷年份继续使用普通错误 JSON，避免生成验收器无法重放的产物。
- `acceptance-check` 接受该错误产物，并以对应 input 与 years 调用当前引擎重放。错误码、说明、命令和年份须与重放结果完整一致。
- 实际可成功生成 context 的输入不能冒充错误；篡改错误码、错误说明或用越界年份伪装原错误都会拒绝。
- 未知内部异常不作为可绑定的确定性错误；没有显式 `--years` 的普通 CLI 错误维持原错误输出，不引入依赖当前日期的验收产物。

## 固定样例

`semantic-forward-005` 使用合成输入：纽约 2024-03-10 02:30、`America/New_York`、民用时、`dstDisambiguation=later`。当前引擎重放为 `NONEXISTENT_LOCAL_TIME`。任务明确要求区分春季缺失时间与秋季重复小时，拒绝把 02:30 自动改成 03:30，也不得生成四柱、星曜、起运或流年。

独立回答为 230 个非空白 Unicode 字符。独立评审的 `factErrors`、`premiseOmissions`、`candidateMixing`、`unsupportedTimingClaims`、`unsafeClaims` 均为 0，内容状态 PASS。manifest 绑定冻结 Skill、任务、量表、输入、错误产物和回答，共 6 个产物；重放结果为 `reviewStatus=PASS`、`runtimeVerified=false`、最终 `status=partial`。

## 验证与边界

- `npm run check`：117/117 PASS，TypeScript strict 与 build PASS。
- 定向 CLI 回归确认错误写入 stderr、stdout 为空、退出码为 1；错误产物不改变正常 context、needs-input 或一般错误合同。
- 独立终审首次发现非整数/NaN 年份也会被包装成 v1、随后被验收器拒绝；现已限制 v1 入口并增加 `2026.5`、`garbage`、`Infinity` 回归。
- 修复后独立复核重跑 acceptance/CLI 定向测试 15/15 PASS，并实际确认三类非法年份维持普通错误、有效整数年份仍可绑定；未发现遗留 blocker、high、P2 或 P3。
- 本样例只验证固定错误输入的停机与补问行为。它不证明 IANA 数据在所有宿主环境永久不变，不证明模型普遍表现，也不证明命理现实预测有效。
- 没有真实模型运行回执；不把内容 PASS 写成完整 verified。
