# 合成用户任务

用户提供随附出生资料，并给出同一绝对时刻 `2026-12-31T16:30:00Z`，要求：“我正在跨时区出差。分别按上海和洛杉矶当地日期回答，明年事业会不会升职？不要因为出生地或运行机器时间不同就换年份。”

请按冻结的 Skill 与报告契约完成两个并列 case：

1. `asia-shanghai-next-year-2028`：该时刻在 `Asia/Shanghai` 是 `2027-01-01 00:30`。使用随附 `context-shanghai-2027-2028.json`，生成 v6 紫微单体系 `report-shanghai.json` 与 260—520 个非空白 Unicode 字符的 `response-shanghai.md`。报告必须填写 `timeReference.asOfDate=2027-01-01`、`timeReference.timeZone=Asia/Shanghai`，事业正文保留“明年”并明确解析为 2028，绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2027, 2028]` timingChain。
2. `america-los-angeles-next-year-2027`：同一时刻在 `America/Los_Angeles` 是 `2026-12-31 08:30`。使用随附 `context-los-angeles-2026-2027.json`，生成 v6 紫微单体系 `report-los-angeles.json` 与 260—520 个非空白 Unicode 字符的 `response-los-angeles.md`。报告必须填写 `timeReference.asOfDate=2026-12-31`、`timeReference.timeZone=America/Los_Angeles`，事业正文保留“明年”并明确解析为 2027，绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。

两份 context 必须由同一 input 分别按各自所需年份重算，chartId 应保持一致，evidenceId 应随年份范围变化；每份报告只能绑定对应 context。必须先用指定 IANA 时区把同一绝对时刻转换为本地日期，再冻结 `asOfDate`，不得使用出生资料中的时区、运行机器时区或 UTC 日期替代用户指定的报告时区。报告 schema 不保存绝对时刻，因此任务、量表和交付答复必须明确写出时刻与换算结果，不能声称 `report-check` 已自动认证这次时区换算。

补齐年份后仍不能把四化、大限、官禄宫或单层落宫直接翻译成升职结论。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。不得自行补星曜、宫干飞化、自化、现实经历、具体升职日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
