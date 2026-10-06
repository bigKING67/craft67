# 报告契约

report-template 给出结构，宿主填充正文；CLI 本身不假装具有模型推理能力。将完整 JSON 交给 report-check 与 render；这不要求在聊天中重复展示 JSON。

## 交付方式与过程陈述

- 能在获准位置写文件时，将完整报告保存为一个 report JSON，后续 report-check 与 render 读取同一文件。局部修正后校验当前版本；完整 Markdown、命盘与证据文件存入用户指定的 repo 外目录或 gitignored private/，核对实际存在及渲染内容后交付链接。无需在多条命令和最终回答中反复复制整份 JSON，不为节省传输省略正文、论证、引用或解释边界。
- 只读或只能使用 stdout 时，仍须将完整报告传给校验和渲染，可在同一进程中复用内存对象；最终直接交付完整 Markdown 或宿主已实际捕获的完整附件。不能声称已保存文件，也不能用摘要或不存在的链接代替完整报告。宿主明确要求结构化输出时遵守其格式；维护评测另按验收合同绑定产物。
- 已有可访问的完整报告文件时，聊天答复直接回答用户问题、概括关键判断与限制，并提供报告链接。日常答复不罗列 context、claim、sidecar、命令、退出码或修复清单；必要的命理术语在具体依据中解释。用户明确请求技术排查时，才说明相关实现细节。聊天中的概括仍须与报告前提一致。
- 发送前单独复读聊天答复：保留用户问题、主要判断、关键限制和报告入口；删去仅供维护验收使用的 schema 版本、正文条数、逐字比对过程等说明。原始 JSON 可作为用户索要的技术附件，不在日常答复中展开检查清单；实际影响交付的失败或缺口仍须如实说明。
- 提到“已执行、失败、重试、修复、通过、已保存”时，逐项对应本次可见的调用结果或文件核验；操作已发起不等于完成，退出码为零不等于未超时或最终已交付。没有证据的过程不补写；确有影响交付的未知则说明尚未确认。旧日志可作为明确标注的历史来源，不能当作本轮发生的事件。中断恢复先核对现存输入、报告版本及实际完成阶段，复用仍匹配的产物；不得把中间产物说成已经交给用户。

## 高风险现实断言门禁

`report-check` 与 `render` 会检查所有最终会渲染给用户的自由文本：title、uncertainty、claim.text、claim.conditions、v6 六类 baziReasoning 与五类 ziweiReasoning 的 conclusion/counterReview/conditions/alternatives、两套 `timingChain` 的逐年复核/跨层复核/现实依据/缺口/撤回条件，以及 crossSystem.text。高置信命中以下类别时返回 `UNSAFE_REPORT_CLAIM`：

- 死亡或寿命的确定性预测，例如“必死”“活不过某岁”“死亡时间是……”；
- 疾病诊断，例如声称命主已确诊、患有特定疾病或一定会患病；
- 保证收益或确定性盈亏，例如“稳赚不赔”“必赚”“保证收益”“无风险收益”；
- 必然婚变或关系事件，例如“注定离婚”“一定出轨”“婚姻必破”。

明确的否定和限制语境允许通过，例如“不能据此断言稳赚”“不预测死亡时间”“不代表关系必然离婚”。句号、分号、逗号或“但是/然而”等转折会结束前一段否定作用，后续出现的新断言仍会拒绝。为避免误杀，门禁只覆盖窄而高置信的措辞；同义改写、隐喻、复杂双重否定和事实与建议之间的深层矛盾仍须人工核对。通过该门禁不等于完整语义安全认证。

当前 schema 固定为 `whoami.report.v6`，chartId/evidenceId 从同一次 context 原样使用。mode 为 bazi / ziwei / combined。title 非空；uncertainty 说明时间口径、候选与解释边界。v6 顶层必须填写 `timeReference: {"asOfDate":"YYYY-MM-DD","timeZone":"IANA 时区"}`，冻结报告中相对时间的解释基准。`whoami.report.v5` 只兼容不含相对时间词的既有报告；`whoami.report.v3/v4` 只兼容八字单体系历史报告。其他旧 schema 的紫微或综合报告会拒绝，必须基于同一 evidence 重新生成 v6 模板并补齐限运作用链。

报告中的冻结基准、相对年份、日期与时区合法性、DST、绝对时刻、区间、时长、重复日程及 evidence 粒度统一遵守[时间表达与 evidence 粒度契约](time.md)。`report-check` 只验证该契约已建模的文本和报告绑定，不认证宿主在报告外完成的时区换算，也不证明现实事件预测有效。

七个 sections.id 固定：summary、character、career、wealth、relationships、timing、advice。
每节有非空 claims 数组，每项为：

```json
{"text":"完整自然语言正文，可以包含多段。","kind":"interpretation","factRefs":["从context选择实际ID"],"ruleRefs":["从context选择实际ID"],"reasoningRefs":[{"candidate":"候选ID","topic":"strength"}],"premiseStatus":"unresolved","conditions":"结论成立的条件及替代解释","confidence":"medium"}
```

kind 为 interpretation/advice；confidence 为 low/medium/high，仅表示传统解释依据的把握。每个 claim 同时引事实和相关规则，每条规则引用都必须关联该项事实，不能靠一条相关规则掩盖其他无关规则。

claim 只要引用八字或紫微事实，reasoningRefs 就必须为每个涉及候选、每个涉及体系绑定至少一个实际依赖的论证 topic；引用另一候选、重复引用、悬空主题或只给命盘事实却不绑定论证都会拒绝。正文明确提到旺衰/身强弱、格局成败、调候、扶抑、用神/喜忌时，还必须绑定对应 strength、pattern、climate、balance、selection。引用紫微事实时，summary/character 必须绑定 ziwei-structure，career 绑定 ziwei-career，wealth 绑定 ziwei-wealth，relationships 绑定 ziwei-relationships，timing 绑定 ziwei-timing；advice 至少绑定其实际依赖的紫微主题。只有不含八字或紫微事实、也不依赖两类论证的 claim 才能使用 `reasoningRefs: []` 与 `premiseStatus: "not-applicable"`。

v6 claim 或 crossSystem 只要引用同候选 `.bazi.cycles`，就必须绑定该候选 `bazi-timing`；含八字事实且提到当前 evidence 年份或年份区间时，文字涉及的全部年份还必须出现在 `bazi-timing.years` 中。含紫微事实并提到这些年份时，同理必须绑定 `ziwei-timing`，且全部年份出现在 `timingChain.years` 中。区间会覆盖其中每个已请求年份，例如 `2026—2028` 不能只登记 2026 和 2028。加入未决运年前提后，premiseStatus 按最保守状态同步降为 unresolved。出生年份、来源出版年份或当前 evidence 之外的数字不会因此冒充运年年份。

报告所有最终可见自由文本的时间表达都必须先通过[时间表达与 evidence 粒度契约](time.md)。该契约定义稳定错误码、失败优先级、资料性窄例外及年度 evidence 的能力边界；不得在本报告契约中维护另一套摘要后绕过其前置检查。含八字或紫微事实的文字通过时间校验后，仍须按上一段绑定同候选时间论证与完整年份范围。

premiseStatus 不是宿主任意选择：所引八字与紫微论证中任一 status=unresolved，本项必须为 unresolved；全部为 conditional 才能写 conditional；没有两类论证才是 not-applicable。未决项若写“已经成立、结论已定、唯一用神、无需核对条件”等显式越级表述，返回 `UNRESOLVED_PREMISE_CLAIM`。明确的“不能说已经成立”“未自动判定唯一喜用”等否定语境允许。渲染结果在对应正文下区分八字与紫微主题，并展示候选及“未决/条件性”。

综合模式先按 [综合与追问](analysis.md#综合与追问) 对齐问题、时间、候选和前提，再填写 v6 crossSystem：`{"target":"career","years":[],"relationship":"insufficient","text":"具体不可比原因或关系判断","factRefs":["八字事实ID","紫微事实ID"],"reasoningRefs":[{"candidate":"候选ID","topic":"selection"},{"candidate":"候选ID","topic":"ziwei-career"}],"premiseStatus":"unresolved"}`。target 只允许 general/career/wealth/relationships/timing；years 必须去重升序，并与 text 中显式或相对表达涉及的 evidence 年份完全一致，未涉及具体流年时填空数组，target=timing 时不得为空。旧 v5 报告继续兼容原有 crossSystem 结构，不靠补字段冒充 v6 迁移。

supports/complements/conflicts 属于强关系，每项只能比较一个候选，所引前提必须全部为 conditional，且八字、紫微两边都至少有一条 factRefs 直接落在所绑定论证的 supportRefs/counterRefs 中；同时直接引用 target 对应的紫微论证与主题事实：general 为 base+命宫，career/wealth/relationships 分别为官禄/财帛/夫妻宫，timing 为运限+四化。强关系只要带年份，还必须同时引用八字 cycles、紫微 cycles、紫微 transformations，并绑定 `bazi-timing` 与 `ziwei-timing`。任一前提 unresolved 时关系只能写 insufficient。insufficient 仍须声明打算比较的 target 与 years，但可以据实记录主题证据、时间链或现实前提尚未闭合。crossSystem 同样为每个候选分别绑定八字与紫微前提；单体系 crossSystem 为空，不混入另一体系，不可把候选 A 的八字与候选 B 的紫微拼成印证。该门禁只证明结构范围对齐，不会自动理解两边文字是否真的支持、互补或冲突。

候选覆盖按“候选 × 当前模式所需体系”检查。bazi 要求每个候选至少出现八字命盘事实；ziwei 要求紫微命盘事实；combined 两者都要，可以分布在正文与 crossSystem 中。`input.*` 仅是资料与来源元数据，不能单独满足覆盖；给 C2 增加出生时间引用也不等于分析了 C2 的紫微或八字。

assertions 是对核心事实的显式复述，格式 `{ "factRef": "实际ID", "value": "原事实的完整原始值" }`，可为空；填写时必须全值匹配，且遵守单体系模式约束。它不是自由文本语义验证器。

报告渲染先附输入、资料来源、口径与风险提示，随后立即展示七节用户正文；综合模式的“八字与紫微对照”也留在用户正文之后。正文结束后进入支持材料区：先按 mode 插入“术语速查”，八字只列八字词，紫微只列紫微词，综合模式合并两组；再列自动核对、八字详细论证和被引用的事实附录。词表只解释这些术语在本报告中的阅读含义，不增加事实、判断或置信度；正文仍须在具体语境中说明实际依据与条件。资料来源缺失时显示未核验，不据地点文字猜测。八字/综合模式遇到 `cycles.uncertainty.status=range` 时，支持材料区逐候选显示采样数、偏移及起运最早—最晚范围，并把对应 cycles 事实加入附录；顶层代表值不能写成唯一时点。随后插入逐候选的“核心规则复核”，直接读取财格入口、财印位置和财官分支反例；对应事实与规则自动进入附录，不依赖宿主是否引用。纯紫微模式不插入起运或八字复核。紫微/综合模式在支持材料区另列“四化分层核对”，按请求年份连接生年、当期大限与流年，显示同星不同四化及定位缺口；对应事实与规则自动进入附录。纯八字不插入紫微内容。相同四化多层出现不累计概率，未列差异不代表已判吉凶。宿主须在正文回应相关反例与缺口；若提出救应或成格，单独论证条件。自动复核与高风险措辞门禁是可见、可复算的最低保护，不会自动判读或改写其余自由文本；report-check 通过仍不表示语义无矛盾。附录供核对，不能代替正文。多候选报告须明确哪段适用于哪张盘，共同点与差异都给依据，不能用一张代表盘声称覆盖全部出生区间。

自动生成的用户可见标签在单候选报告中写“当前命盘”，多候选报告中按 `candidateIds` 顺序写“候选 1”“候选 2”等；论证前提按候选归并主题，不展示 `C1-…/topic` 形式的内部键。原始 candidate ID、事实 ID 与规则 ID 继续保留在可展开的证据附录及 report JSON 中，供精确追踪。宿主自己填写的正文也应使用同一自然标签，不把内部 ID 当成面向用户的称呼。

每条 claim 的条件与限制必须留在正文可见的“解释边界”中，同时显示传统解释把握以及所引八字/紫微前提为未决或条件性；不能把限制全部折叠。具体事实链接和论证主题放入紧随该 claim 的“查看本段命盘依据与论证主题”折叠区。crossSystem 同理：关系判断、target/years 对照范围和两体系前提状态可见，具体对照依据可展开。折叠只改善阅读层级，不删除 report JSON 绑定、事实引用或前提状态。

不编辑 chartId 以让旧报告“通过”；资料或引擎变化后重新 context 与分析。多轮追问引用既有证据；更正资料时另建新报告，并记录被替代的旧结论。

## 八字论证（八字/综合模式必填）

bazi/combined 的 v6 报告对每个 candidateId 填写 baziReasoning 六项：strength（旺衰）、pattern（格局）、climate（调候）、balance（扶抑）、selection（最终用神取舍）、bazi-timing（运年与边界）。紫微单体系填空数组。兼容读取的 v3/v4/v5 旧报告仍只允许前五项；`bazi-timing` 不可追加到旧 schema 冒充迁移。

```json
{"candidate":"实际候选ID","topic":"strength","status":"unresolved","conclusion":"当前判断或无法判断的理由","supportRefs":["本候选八字事实ID"],"counterRefs":[],"counterReview":"检查了什么反证，为什么未定位或尚无法判断","conditions":"成立条件或缺失资料","alternatives":"替代解释与取舍理由","ruleRefs":["关联这些事实的规则ID"]}
```

`bazi-timing` 另加 `years` 与 `timingChain`，例如：

```json
{"candidate":"实际候选ID","topic":"bazi-timing","status":"unresolved","years":[2026],"conclusion":"运年范围、边界与当前可判断程度","supportRefs":["同候选.bazi.cycles","同候选.bazi.relations"],"counterRefs":[],"counterReview":"已核对与尚未闭合的年度作用","conditions":"适用年份、主题与撤回条件","alternatives":"未闭合时如何保留分支","ruleRefs":["同候选.R-bazi-timing"],"timingChain":{"target":"general","cycleRefs":["同候选.bazi.cycles"],"annualReviews":[{"year":2026,"pillar":"丙午","boundary":"lichun","natalRefs":["同候选.bazi.relations"],"review":"2026 丙午如何连接本命与运年，以及当前为何未决"}],"crossLayerReview":"本命、大运与流年如何分层核对","missingLinks":["尚未闭合的现实或传统解释环节"],"realityBasis":{"status":"not-provided","summary":"当前没有可核对的现实触发资料","source":null},"withdrawalConditions":"哪些新资料或反例出现时撤回本判断"}}
```

status 为 conditional 或 unresolved；conditional 仍不代表确定性事实。supportRefs 是支持当前判断或未决状态的盘面依据，必须非空；counterRefs 允许为空，但 counterReview 必须解释检查范围和缺口，不能把空数组解释成无反证。两侧可引用同一复合事实，由文字说明其中不同的作用，不自动打分。

同一候选的六个 v6 主题必须各自回答该主题的问题，不能用一组通用占位文字填满多项。`report-check` 会折叠首尾与连续空白；若两个主题的 conclusion、counterReview、conditions、alternatives 四项归一化后全部相同，返回 `DUPLICATE_REASONING_NARRATIVE`。单个字段、同一事实或同一规则可以在确有共同前提时复用；程序不判断措辞略改后的近似重复，也不把通过此门禁当作语义质量认证。

每项还须绑定可由当前 evidence 直接判定的主题锚点，否则分别返回 `MISSING_TOPIC_RULE` 或 `MISSING_TOPIC_EVIDENCE`：strength 至少引用月柱、rootDetails 以及 structure/root-review 规则；pattern 至少引用 monthExposure 以及 structure/wealth-review/month-exposure 规则；climate 至少引用月柱与 structure 规则；balance 至少引用 rootDetails 或 relations，以及 structure/root-review/wealth-review 规则；selection 至少引用 monthExposure、wealthReview、rootDetails 之一，以及上述结构、通根、财格或月令透干规则；bazi-timing 必须引用 `.bazi.cycles` 与 `R-bazi-timing`，years 只能来自当前 evidence 且去重升序，可以在未请求具体流年时为空，其自身四个叙事字段涉及的 evidence 年份也必须全部纳入 years。锚点证明该主题没有只挂无关事实或规则，不证明文字已经完成传统论证。

v6 `bazi-timing.timingChain` 的 target 为 career/wealth/relationships/general；`cycleRefs` 必须非空、只引用同候选 cycles，并已纳入该项 supportRefs/counterRefs。`annualReviews` 与顶层 years 数量和顺序完全一致；每项 year、pillar、boundary 必须逐值匹配 cycles 的 yearly 事实，boundary 当前固定为 `lichun`。每项还须以 `natalRefs` 引用已纳入本项依据的同候选四柱或 relations，review 明确写出该年与干支。`crossLayerReview` 区分本命、大运与流年，`missingLinks` 记录未闭合的传统或现实环节，`realityBasis` 与 `withdrawalConditions` 采用和紫微作用链相同的失败封闭语义。现实资料未提供时 source 必须为 null、missingLinks 至少一项且 status 强制 unresolved；声明资料已提供只建立来源可追踪性，conditional 还要求 missingLinks 为空。未决项即使已声明现实来源，也必须保留至少一个缺口。程序只核验结构、确定性干支与引用闭合，不认证现实资料真实性或传统推论。

引用只允许本候选八字事实；每一条规则均需关联所引事实。每侧不可重复同一 ID，跨字段同源事实也不应重复计权。selection 必须在文字中说明前三种取用口径的分歧和适用条件，并遵守[最终取舍状态门槛](selection.md)。conditional 不按其他 topic 的状态计数：须在限定语境内给出具体方向、完整前提、反证与撤回条件；只有候选身份或待比较分支时继续 unresolved。程序只验证结构与引用，宿主仍要核对语义，不能以填写无关文字通过格式校验代替论证。

## 紫微论证（紫微/综合模式必填）

ziwei/combined 对每个 candidateId 填写 ziweiReasoning 的五项：ziwei-structure（本命结构）、ziwei-career（事业联宫）、ziwei-wealth（财运联宫）、ziwei-relationships（关系联宫）、ziwei-timing（限运与四化）。八字单体系填空数组。

```json
{"candidate":"实际候选ID","topic":"ziwei-career","status":"conditional","conclusion":"当前事业主题的条件性判断","supportRefs":["本候选紫微事实ID"],"counterRefs":[],"counterReview":"检查了目标宫、三方四正、四化层级与定位缺口","conditions":"成立条件或缺失资料","alternatives":"替代解释与撤回条件","ruleRefs":["关联这些事实的规则ID"]}
```

结构、状态、引用、整段重复门禁与规则关联要求和 baziReasoning 相同，但事实只能来自同一候选的紫微体系。五个主题必须逐候选各一项，不可用本命结构一项代替事业、财运、关系或限运。本命结构须同时引用 base、命宫事实和至少一条事业/财运/关系联宫规则；事业、财运、关系须分别引用官禄、财帛、夫妻宫事实和对应联宫规则；限运须引用 transformations 规则，并继续满足下述 timingChain。错挂其他主题规则或只引用 base/四化清单会返回 `MISSING_TOPIC_RULE` 或 `MISSING_TOPIC_EVIDENCE`。ziwei-timing 如果只有年份、大限标签或四化星名清单，仍须保持 unresolved；只有完成分层落宫、主题宫联读、跨层差异和现实问题作用链后，才可在明确范围内收窄为 conditional。conditional 仍不是事件预测或现实发生概率。

v5 起的 `ziwei-timing` 必须填写 `timingChain`；当前新报告使用 v6：

```json
{"target":"general","years":[2026],"transformationRefs":["同候选四化事实ID"],"cycleRefs":["同候选大限事实ID"],"palaceRefs":["同候选主题宫事实ID"],"crossLayerReview":"本命、大限、流年与流年宫职如何分层核对","missingLinks":["尚未闭合的现实或传统解释环节"],"realityBasis":{"status":"not-provided","summary":"当前没有可核对的现实触发资料","source":null},"withdrawalConditions":"哪些新资料或反例出现时撤回本判断"}
```

years 必须来自当前 evidence；三组事实引用均须非空、属于同一候选，并同时纳入该项 supportRefs/counterRefs。`transformationRefs` 只能指向四化事实，`cycleRefs` 只能指向运限事实，`palaceRefs` 只能指向主题宫事实；target 为 career/wealth/relationships 时，须分别至少包含官禄/财帛/夫妻宫，general 则按实际问题列出所用主题宫。现实资料未提供时，source 必须为 null、missingLinks 至少一项，ziwei-timing 强制 unresolved。若宿主声明资料已提供，须给出来源说明；这只是可追溯声明，不证明资料真实，也不证明传统解释正确。只有 `missingLinks=[]` 时结构上才允许 conditional，宿主仍须人工核对完整作用链和正文强度。

旧报告不自动迁移：重新生成 v6 模板，保留经核对的正文，填写真实的 timeReference，并逐项补齐两体系所需 reasoning、八字运年 years/timingChain、紫微 timingChain 与 reasoningRefs/premiseStatus 后再检查，不能只替换版本号。v5 在完全不含相对时间词时可兼容读取；v3/v4 八字单体系也可兼容读取，但建议在下一次资料或正文变更时迁移 v6。旧 schema 的紫微/综合必须重建为 v6。只有报告 schema 更新不要求改写 chartId/evidenceId；若实际命盘、证据年份或相对时间基准也变更，则必须重新核对对应引用。

### 正文与论证的前提一致性

写完 baziReasoning 与 ziweiReasoning 后，逐条核对正文。涉及强弱、喜忌和扶抑的 claims，定位同一候选的 strength、balance、selection；涉及大运、流年或当前 evidence 年份时，另定位 bazi-timing，检查年份范围、边界、主题作用和撤回条件。可以自然承接前文，不必反复抄整张条件表；但不能在后段用“可任负荷”等较弱前提替代“偏旺、比劫偏重且财轻”。若仅确认生财路径存在，正文就不把它写成已选扶抑方向；selection 或 bazi-timing 未决时，事业、财运、建议也不能悄悄给出确定喜用、对应职业或行动年份。

涉及紫微结构、事业、财运、关系和限运的 claims，须定位同一候选的对应 ziwei topic，检查主题宫、关联宫、时间层、定位缺口与撤回条件是否仍在正文中。只有星曜或四化清单时，不把它写成性格定论、现实事件或逐年行动日程；ziwei-timing 未决时，正文不能悄悄给出确定事件和行动时点。综合 claim 若依赖两体系，正文的结论强度服从两边所引前提中更保守的状态。

逐年核对正文实际解释的每个紫微主题：从该年主题宫职定位到本命物理宫，再读取该宫的 surroundedIndices 与各关联宫事实，回应其支持、反例和缺口。不能用本命官禄联宫代替已经换位的流年官禄联宫，也不能用同年关系主题的联宫分析代替事业主题；全量引用十二宫不等于完成文字论证。生年或大限只有本命落宫而没有 scopePalace 时，不能概括成所有层次都完成“双宫职定位”，须分层保留缺口。尚未展开联宫时，把相关表述明确保留为待核问题，不写成已有充分依据的年度主题。

核对须覆盖宫位清单之后的解释句：逐句把参与推断的宫位和星曜回配到该年该主题的物理宫集合，不能因前句清单正确就跳过后文。若另引集合之外的本命或大限背景，须标明其层次并说明与本题的作用依据，不得称为该主题的三方四正；其他年份或主题中的正确宫位也不能直接移入本段。v6 `report-check` 与快速档 `answer-check` 会对以“YYYY(年)(的)流年官禄/财帛/夫妻(宫)落(在)本命<宫>(（地支）)”开头的段落自动核对：段首落宫须与当前命盘一致，段内以“宫名+地支”“宫名(宫)（地支）”“宫名宫位于地支”或“宫名(宫)(括号)+本宫星曜”写出的本命宫须在该集合内，否则返回 `PALACE_SCOPE_MISMATCH`；确需另引集合外背景时，在同一分句写明“三方四正之外”或“不属本题”。单候选命盘核对全部可见文字；多候选只核对能唯一归属某一候选的文字，`answer-check` 对多候选答复返回 `palaceScope: "skipped-multi-candidate"`。星曜缩写（如“空劫”）、其他写法和多候选混写仍须人工逐句核对。

crossSystem 逐项核对 target 对应的具体问题、两体系各自的命盘依据及未闭合环节。insufficient 也须说明此主题究竟在哪一步无法比较；不能仅替换“事业/财运/关系”标题后复用同一段泛泛说明。若某体系未能提供该主题的对应依据，直接说明该项缺口，不借其他主题的事实填充对照。

正文与论证不一致时，回到事实和取法判断哪一边有误，再修正；不能为通过核对就把所有结论一律降为未决。通用现实建议与命盘推论区分，运年建议须另有该年依据。核对在report-check/render之前完成，渲染后确认正文与自动规则摘要没有矛盾。程序不自动理解这项语义；有结构校验结果不等于完成前提核对。维护验收例时可记录具体段落与裁决，日常用户报告无需附内部审稿清单。

### 事实断言的值类型

value 保留 context 原类型，不要对对象或数组调用 JSON.stringify。例如原事实为对象 `{ "示例字段": 1 }`，对应断言写成：

```json
{"factRef":"对应事实ID","value":{"示例字段":1}}
```

若原事实本来是字符串（例如日主），value 才是字符串。断言可选；遇到类型错误应先按原值修正，不把删掉断言当作事实核验的替代。
