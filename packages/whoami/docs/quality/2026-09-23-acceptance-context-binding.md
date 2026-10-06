# 验收 input/context 绑定与边界前向样例

日期：2026-09-23。结论：自然语言验收从“分别校验文件哈希”提升为“文件哈希 + 当前引擎重算”。A 输入配 B context、context 事实篡改、与当前引擎不一致的旧结果、将未知时辰伪装成完整 evidence 均会拒绝。新增春节前农历年界与完全未知时辰两项固定前向样例；原始回答中的长度失败被保留并通过独立修订闭环。所有运行身份仍为 UNVERIFIED。

## 发现与修复

旧 `acceptance-check` 会验证 input 和 context 的 SHA-256、大小、目录边界及回执绑定，但不会读取二者内容。因此，只要 manifest 写入各自真实哈希，来自不同输入的 context 仍可能通过。

当前验收器读取每个 case 的 JSON：

- `whoami.evidence.v1`：使用 artifact input 与 context.years 重新执行 chart + evidence，并对整份结构深度比较；
- `whoami.chart.v1`：只接受 `status=needs-input`，使用相同输入与年份重算完整 chart；
- 其他 schema、手写摘要、输入/context 不匹配、事实改写、与当前引擎不一致的旧结果或 needs-input 冒充 evidence：fail closed。

运行回执合同没有放宽。重算只能证明当前本地引擎可复现 input/context，不能认证 provider/model 身份；没有可信 runtime receipt 时结果仍是 PARTIAL。

## semantic-forward-003

固定 Skill 快照、任务和两个合成案例后，独立代理只读取允许的 input/context，没有读取 rubric、源码、测试、其他示例或网络。

`lunar-year-boundary` 使用公历 2000-01-15。context 保留 `birthLunarYear=1999`、己卯年柱和请求年份 1999/2000/2026。原始回答正确区分公历日期、紫微农历新年界与八字立春年界，也说明地点、经度、时区来源未核验；五项语义计数为零，但只有 322 个非空白字符，低于任务的 350 下限，因此原始 reviewStatus 为 PARTIAL。独立修订回答为 355 字符，内容复核五项为零并标 PASS；原稿和原 manifest 没有覆写。

`unknown-time-needs-input` 使用 `time:null`，绑定当前引擎生成的 needs-input chart。回答拒绝补 12:00、生成四柱/星曜或给出 2026 唯一结论，并提出核对出生记录和可接受时间范围；157 个非空白字符，内容复核 PASS。

## 验证

- `npm run check`：115/115 tests PASS，TypeScript strict 与 build PASS；
- Skill `quick_validate.py`：PASS；
- 新增回归：A 输入配 B context 拒绝、单项事实篡改拒绝、真实 needs-input chart 接受、needs-input 冒充 evidence 拒绝；
- semantic-forward-001、002 原稿、002 修订稿、003 原稿、003 修订稿五个 manifest 均由新验收器重放成功，说明各自 input/context 仍与当前引擎一致；
- 003 原稿返回 `reviewStatus=PARTIAL`，修订稿内容评审 PASS；两者均因 runtime receipt 缺失保持最终 PARTIAL。

DST 重复/缺失时间继续由自动测试覆盖：reject 必须要求确认，earlier/later 保留不同实际瞬间，不允许不存在时间用 disambiguation 偷换。本轮没有把 CLI 错误文本扩充为 acceptance context 类型，因此没有把 DST 错误输出伪装成模型 context。

本轮没有修改排盘算法、报告 schema 或命盘证据规则；没有远端模型 API、真人资料、全局安装、发布或 push。当前目录不是 Git 仓库。
