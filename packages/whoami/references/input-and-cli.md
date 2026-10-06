# 输入与 CLI

运行：Node.js >=22，`npm ci --ignore-scripts`、`npm run build`。固定版本见 package-lock.json。
使用 `node dist/cli.js` 可避免 npm 在 stdout 输出脚本前缀；`npm run cli -- ...` 供交互调试。

```json
{"calendar":"solar","date":"2000-08-16","time":"04:00:00","place":"合成样例地点（东经120度）","longitude":120,"timeZone":"Asia/Shanghai","gender":"female","timeBasis":"true-solar","dayBoundary":"zi","uncertaintyMinutes":0,"provenance":{"placeSource":"用户提供","longitudeSource":"公开地名库记录","timeZoneSource":"IANA Asia/Shanghai","verifiedAt":"2026-09-23"}}
```

| 字段 | 约定 |
|---|---|
| calendar / date | solar 或 lunar；YYYY-MM-DD。首版 1901–2098 |
| leapMonth | 农历必填 boolean；公历不能 true |
| time | HH:mm[:ss]；未知明确 null |
| uncertaintyMinutes | 出生时间的 ±分钟，0–120，默认 0；更宽范围先补问 |
| place / longitude | 原始地点文字与经度，东正西负；不自动地理编码，不收姓名 |
| timeZone | IANA 地区时区，不能将固定 +08 当作历史地区时区 |
| gender | male / female；传统排盘所需参数，不自动从名字推断 |
| timeBasis | 默认 true-solar，可选 civil |
| dayBoundary | 默认 zi（23:00 换日），midnight（00:00 换日）可比较 |
| dstDisambiguation | 默认 reject；重复小时在用户确认后选择 earlier/later；不存在时间始终拒绝 |
| provenance | 可选来源元数据：placeSource、longitudeSource、timeZoneSource、verifiedAt，均为非空文字。只记录来源说明，不自动证明来源真实 |

未识别字段拒绝，provenance 内也不接收未知键，防止拼写错误悄悄改变口径。中国历史夏令时由 IANA tzdata 解析，运行环境版本写入命盘。省略 provenance 时仍可排盘，但 context 和渲染报告明确显示地点、经度、时区来源未核验。

## 命令

```sh
node dist/cli.js validate --input examples/birth.json
node dist/cli.js chart --input examples/birth.json --years 2024,2025,2026,2027,2028
node dist/cli.js context --input examples/birth.json --years 2024,2025,2026,2027,2028
node dist/cli.js rule-review --input examples/birth.json --years 2024,2025,2026,2027,2028
node dist/cli.js report-template --input examples/birth.json --years 2024,2025,2026,2027,2028 --mode combined
node dist/cli.js report-check --input examples/birth.json --report /path/to/report.json --years 2024,2025,2026,2027,2028
node dist/cli.js render --input examples/birth.json --report /path/to/report.json --years 2024,2025,2026,2027,2028
node dist/cli.js answer-check --input examples/birth.json --years 2026 --as-of 2026-09-28 --text -
```

`answer-check` 用于快速档纯文本答复：`--text` 为文本文件或 `-`（stdin，避免落盘真人答复）；`--as-of` 是按用户报告时区冻结的 YYYY-MM-DD，答复含相对年份时必须提供。它复用报告的高风险措辞、未决前提升级与时间规则，并在单候选时核对流年主题宫位集合；成功输出 `status: valid` 与 chartId/evidenceId，失败按下述错误契约退出 1。它不读取报告、不证明解释语义，也不替代完整报告的 `report-check`。

### 断言清单 answer-audit

快速档交付时以 `--audit -` 从 stdin 传入 `whoami.answer-audit.v1`，答复原文放在 `answer` 中（也可另用 `--text` 传文件，此时 `answer` 可省略；input、text、audit 最多一项走 stdin）：

```json
{"schema":"whoami.answer-audit.v1","evidenceId":"与 context 相同","answer":"完整答复原文","claims":[
  {"text":"答复中逐字存在的句子或整段","kinds":["timing","event"],"stance":"conditional","factRefs":["C1-….bazi.cycleRelations"]}
]}
```

- `kinds`：event（事件、财运、关系、健康与吉凶）、pattern（格局、用神、强弱）、timing（年份、流年流月、大运大限、起运）、palace（运限宫职）、fact（命盘事实）。`stance`：conditional、unresolved、fact-restatement。kinds 含 fact 时 stance 必须是 fact-restatement（可兼 timing/palace，如“2027 年是丁未流年，全年处在辛巳大运”）；含 event 或 pattern 时不能用 fact-restatement。
- 依据：pattern 须引用 patternReview、wealthReview、monthExposure 或 rootDetails 之一；timing 须引用 bazi.cycles/cycleRelations/monthlyCycles 或 ziwei.cycles/transformations/monthly 之一；palace 须引用紫微宫位或运限事实；所有 factRefs 须在当前 context 中存在。
- 覆盖：答复按句末标点与换行切句、再按逗号切成分句；“一、……”“## ……”等 24 字内的小标题跳过。含触发词的分句须被某条断言的 text 整句包含（按整段登记即可一次覆盖多句），覆盖断言须声明该分句触发的每一类；整段登记时要声明段内出现的全部判断类型；段内只要含事件或格局判断就不标 fact（段内命盘事实随之不单独按 fact 核对），纯事实段落才用 fact。多登记不含触发词的句子允许，但不增加检查。
- 限定语：含事件或格局判断的句子须带下列任一条件或限定语，否则报 `AUDIT_STANCE_MISMATCH`：如果、若、假如、除非、一旦、取决、视乎、视情况、而定、条件、可能、或许、也许、倾向、未必、不一定、不确定、尚未、未定、未决、待、须、需要、要看、还要看、是否、能否、会改变、范围、入口、候选、分支、不宜、不能、不等于、并非、不是、不代表、只能、仅、参考、线索、保留、较难、偏向。这只能粗筛“登记为条件性却写得绝对”的句子，不能理解语义。
- 错误码：`INVALID_AUDIT`（格式、原文不逐字、事实不存在、answer 不一致）、`AUDIT_STALE`（evidenceId 不一致）、`AUDIT_KIND_MISMATCH`、`AUDIT_COVERAGE_GAP`、`AUDIT_STANCE_MISMATCH`；所有问题一次列出，错误码取第一处。结果的 `audit` 给出登记数与覆盖分句数，未传时为 `not-provided`。

`--granularity month`（chart/context/report-template/report-check/render/answer-check；rule-review 只看本命，不接受此参数）额外输出 `.bazi.monthlyCycles` 与 `.ziwei.monthly`，并在 context 中记录 `granularity: "month"`；不加时输出与同版本的年度 context 逐字节相同。同一报告的各命令必须使用相同的 years 与 granularity，否则 evidenceId 不匹配。

`context` 默认输出 `whoami.evidence.v3`：相对 v2 在 `patternReview` 中增加 `extendedPatterns`（建禄月劫、阳刃），并新增 `.bazi.externalPatterns`（外格候选），`R-bazi-pattern-review` 的引用与说明随之扩展。v1、v2 已发布冻结。v2 相对 v1：新增 `.bazi.cycleRelations`（岁运干支关系）、`.bazi.patternReview`（五格显干条件）、`.ziwei.flyingTransforms`（宫干飞化与自化）及 `R-bazi-pattern-review`；本命 `.bazi.relations` 只增不删地扩展半合、拱合、破、两两相刑与三会；相关规则的引用与说明随之扩展，其余事实与规则逐字节不变。`report-check`/`render` 按报告绑定的 evidenceId 自动选用 v1、v2 或 v3 重算（月度报告不回退到 v1），并在结果中返回 `evidenceSchema`；v1、v2 只为既有报告与验收样例保留，新报告一律基于 v3。

`report-template` 当前输出 v6，`timeReference.asOfDate` 与 `timeReference.timeZone` 留空等待宿主填写。填写报告实际采用的本地公历日期与 IANA 时区后再运行 `report-check`；不能把模板空值直接当成有效报告，也不能用系统读取时刻替换已经冻结的报告基准。

--input - 从 stdin 读。正常输出 stdout；错误 JSON 到 stderr 并退出 1；未知时辰 chart/context/rule-review 退出 2 并返回 needs-input。context 使用可解析为整数列表的显式 `--years` 时，确定性输入/计算错误会带 `whoami.error.v1`、命令和年份，可作为自然语言验收产物重放；非整数、NaN 或无穷年份维持普通错误 JSON。错误产物仍是失败结果，不能当作空白命盘或自动更正输入。ambiguous 不视作程序错误，但必须按多候选/未定时辰处理。指定流年 1901–2099，最多 20 年；不指定时以 Asia/Shanghai 当前年 ±2 年。

`rule-review` 成功时输出 Markdown，包含财格入口、八组显干前提、财印位置、财官分支反例，正官、七杀、印、食神、伤官五格与建禄月劫、阳刃的候选入口和已见显干条件（附原文引文），外格候选的通则、入口与排除条件，以及未决条件和证据ID；它不读取报告文件、不调用模型、不写入文件。缺时辰时仍输出 JSON needs-input 并退出2。它只是本命格局规则摘要，不是完整八字、紫微或流年解释。多候选全部保留，不选择“较好”的命盘。需要机器读取的完整事实仍用 context。

## 更正出生资料的差异对照

```sh
node dist/cli.js compare --before examples/acceptance/full-1996/birth.json --after examples/acceptance/full-1996/birth-1010.json --years 2026,2027,2028
```

成功输出 `whoami.compare.v1` JSON、退出0。changedInputFields 比较规范化输入，changedFacts 按同名事实项列出两端值及引用，unchangedFactKeys 保留未变项。evidenceBinding.bindingMatch 只比较两端版本，不代表已验证任何报告的正文或结构。即使事实没有变化，地点显示文字等输入变化也可导致报告绑定失效；同一时辰内更正时间也可能改变起运。

任一侧缺时辰，返回 needs-input、退出2。多候选未指定时返回 needs-selection、退出2，并列两侧候选。使用返回的完整ID加入 `--before-candidate <ID>` / `--after-candidate <ID>` 后再比较；只对多候选侧必填。此选择只是指定对照组合，不确认某个出生时间，也不按ID相似度或数组顺序跨输入配对。单候选若仍有时间不确定性，结果继续保留 ambiguous 和警告。

before/after 至多一侧可以是 `-` 从stdin读，不能两侧共用一次stdin。years在两端一致；没有报告文件参数，不自动改写正文、选择时辰或替换旧报告ID。

## 时间与流派

- 节气计算库的时间基准是固定 +08:00；将出生绝对时刻转换到此基准后取年/月柱。不能用经度修正值移动节气。
- 真太阳时按 NOAA fractional-year 均时差公式：UTC + 4×经度分钟 + 均时差。保留当地法定时差和校正明细。结果的小数秒是计算格式，非精度承诺。
- ±2 分钟太阳时边界筛查是工程保护，不是经过全日期认证的误差界。输入不确定区间每分钟加端点采样，候选非连续区间完备证明。
- 八字午夜方案令日干与晚子时干同属当天；这与某些库“当天日柱＋次日时干”的 sect=2 输出不同，已明确测试。
- 起运使用 lunar-typescript Yun sect=2，以绝对出生时刻至节的间隔计算；不以校正后的太阳时重复移动出生瞬间。起运日期是传统换算法结果，不能解释为可验证事件发生日。
- 同一候选四柱可以覆盖多个分钟样本，起运仍会随实际出生时刻移动。`cycles` 顶层值只是一条代表样本；`cycles.uncertainty` 给出样本数、出生偏移、太阳时偏移及起运最早/最晚范围。status=range 时报告必须写范围，不能只引用代表值。
- 紫微：全书派，农历年分界，闰月前半/后半分配，虚岁按年份；子初 forward、午夜 current。太阳时跨日会按校正日期派生紫微农历，是 whoami 的明确约定，不代表唯一流派。
- 紫微流年以农历新年，八字以立春；同一“2026年”边界可能不同。默认只输出年度层；`--granularity month` 另输出八字节气流月与紫微农历流月，仍不输出流日或钟点。

## 维护入口

本地 benchmark、自然语言回归、运行回执、外部签发和 Codex runtime audit 不属于日常排盘命令。维护这些能力时再完整读取[维护与验收契约](acceptance.md)；普通命理解读无需加载其 manifest、签名或运行证明细节。
