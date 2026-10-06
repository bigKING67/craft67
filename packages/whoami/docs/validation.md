# 首版验收记录

日期：2026-09-23。环境：macOS、Node 24.18.0、npm 11.16.0、IANA tzdata 2026b。

说明：下方 OpenSpec 命令只记录首版曾执行过的历史验证，不是现行依赖或验收门禁。仓库现已移除 `openspec/`；行为合同以 `references/`、源码校验和自动测试为准，无需安装 OpenSpec CLI。

| 验收 | 结果 | 能证明什么 |
|---|---|---|
| npm run check | PASS：TypeScript strict、37 tests、tsc build | 当前实现/适配器行为回归通过 |
| Skill quick_validate.py | PASS：Skill is valid | 格式、命名和结构符合工具要求 |
| OpenSpec validate add-whoami-core --strict --no-interactive | PASS | 行为规格格式有效 |
| 公开金样例 | PASS：5 组四柱、紫微官方例、起运例 | 上游公开预期与本地适配一致，不是独立历法引擎认证 |
| 时间边界 | PASS | 节气前后、跨日、23:00/00:00、闰月、历史 DST、跨时区绝对时刻、未知时辰与候选处理 |
| 报告 | PASS | 引用存在、规则关联、显式事实一致、旧报告失效、多候选不可遗漏、单/双体系结构 |
| 实际 MingLi-Bench 文件 | PASS：160 题；130 development / 30 holdout | 上游固定版本真实文件可读、分组、答案隔离、外部命盘可关联 |
| 独立自然语言验收 | PASS with limits | 完整综合报告与两项实际追问走通；主代理重新执行 report-check |
| Fatetell Reverse Craft case | PARTIAL：1 evidence / 1 supported finding；validate 0 errors，已 seal | 客户端字段/任务状态/页面副作用有证据；后台算法与成功生成未验证 |

## 实际运行命令

```sh
npm run check
uv run --with pyyaml python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
npm exec --yes --package @fission-ai/openspec@1.13.1 -- openspec validate add-whoami-core --strict --no-interactive
node dist/cli.js report-check --input examples/birth.json --report examples/report.json --years 2024,2025,2026,2027,2028
```

系统 Python 没有 PyYAML，首次格式校验因此失败；改用 uv 的临时依赖环境后通过，未安装到系统 Python。OpenSpec 原本不在 PATH，以固定版本 npm exec 运行，未全局安装。

## 自然语言交付

实际启用一个独立验收代理 `/root/skill_acceptance`，只读取 Skill/运行引用，使用合成出生资料，在 `/tmp/whoami-skill-acceptance/` 写出完整报告；没有授予网络、浏览器或源码写入权限。主代理继续做研究文档与测试。

验收代理执行 validate → chart → context → report-template → 实际写作 → report-check → render，并回答“你为什么判断用神，用户说喜水会不会改口”和“时辰完全未知但要求唯一紫微盘”。分别维持有依据的解释和拒绝伪造时辰。

主代理重放结构校验，核对四柱、主星、命身宫、大运、大限和四化年份；将合成报告保存在 [示例长文](../examples/report.md)、[结构化报告](../examples/report.json) 和 [追问示例](../examples/followups.md)。最终 Markdown 约 29.8 KB，含可展开的事实附录；不是仅目录或摘要。验收发现的缺项逐轮追问问题已在 Skill 改为先汇总缺项。

原验收证据 `/tmp/whoami-skill-acceptance/acceptance.md`；最终交付样例以本项目 examples 为准。独立验收不能证明普遍正确，尤其自由文本中引用存在不等于推断必然成立。

## 评测边界

原始题集和预排盘仅放 repo 外临时验证目录，固定版本与 SHA-256 记在研究 manifest。本次测试了真实 160 题准备流程与合成评分回归，未进行 160 题模型性能跑分，也未把读过的题目冒充盲测。模型质量的实际小批验收为上述合成完整报告及追问场景；不发布“算命准确率”。

## 剩余限制

- 真太阳时近似公式与分钟采样需要边界提示；未全域认证秒级精度。
- 旺衰、格局、调候和用神不是完整自动专家引擎；宿主必须按事实给条件性解释。
- 语义与现实预测能力不由 report-check 或测试覆盖保证。
- 只做本地使用，未验证全局自动发现/安装、Windows、Web UI、远端模型或生产部署。
- Fatetell 页面自动产生免费预览请求，已终止并取证；服务端成功/权益变化未核验。具体过程见 [研究记录](research/fatetell.md)。
- 旧 bazi-ziwei 的五份已记录源文件哈希再次比对一致；本任务没有向旧安装目录写入。

## 2026-09-23：Mingyu 研究与通根证据增量

- 新增固定提交的八份 Mingyu 来源指纹、研究档案、分析差距与 Fatetell 有界实验方案；未引入 Mingyu 依赖或源码。
- rootDetails 与通根复核规则独立实现，保留同五行藏干、同干标记与逐柱直接六冲来源。未改排盘算法或新增旺衰裁定。
- `npm run check`：42/42 tests PASS，TypeScript 与 build PASS。新增五项回归覆盖受冲保留、同干区别、移除冲、重复冲源、候选隔离与无根；人工改写 fixture 仅检验事实联结，不作为真实排盘。
- 最初误在父目录运行 check，因无对应 script 失败；随后在 whoami 项目目录运行上述完整验收通过。
- 合成示例 chartId 未变，旧 evidenceId 被拒绝；对新增根事实断言核对后更新用神段引用与条件说明，report-check/render PASS。新的 evidenceId 为 `7bc90979f6f8ce418dfc12973c8a11ccee377539cb363e2f9bf22c3c855e2966`。
- skill-creator quick_validate 与 OpenSpec strict validate PASS；本次小幅引用更新未新增子代理验收。
- reverse-craft R3 / main_serial；原 sealed case validate PASS，1 evidence、1 finding、0 errors/warnings。仅复核原静态证据，无新浏览器会话、无账户请求或报告生成。后台内部算法仍 UNVERIFIED。
- 未执行完整模型 benchmark 或新增题库评测；测试数量不代表现实预测效果提升。

## 2026-09-23：报告 v2 论证合同

将八字候选的五类论证纳入模板、校验和渲染：旺衰、格局、调候、扶抑、最终取舍。支持引用必填；反证引用可空但须说明复核范围；状态明确 conditional/unresolved。新增引用限定本候选八字事实，逐条规则关联；所引反证和规则进入附录。纯紫微不强制填八字内容。

`npm run check`：48/48 PASS，typecheck/build PASS；Skill quick_validate、OpenSpec strict、合成报告 report-check PASS。新增六项测试覆盖旧版拒绝、主题完整性、反证复核缺失、未决、跨体系/候选引用、无关规则、重复引用、附录和紫微正文候选覆盖。首次测试因候选遗漏被新的更早门禁捕获而错误文案断言不匹配；已更新对应断言，并单独保留正文覆盖回归，未削弱拒绝行为。

已人工填写并验证合成报告五项论证，chartId/evidenceId 保持不变。schema 从 whoami.report.v1 升到 v2；旧版明确拒绝，没有静默迁移。仍需宿主核验文字是否真正回应所引证据；程序不能识别所有无关文字或自行确定传统规则的正确性。

本轮未改变历法与排盘，未新增第三方依赖或复制源码，未执行 Fatetell 在线请求、模型 benchmark、全局安装或发布。本轮没有独立代理语义评审。论证合同强化不代表自动旺衰/用神引擎完成，也不代表现实预测效果提高。

## 2026-09-23：月令透干事实

直接读取《子平真诠》三章原文转录并记录来源指纹，区分正文、校勘、后人按语；影印 PDF 未取得可逐字核对证据，未宣称影印校勘完成。实现 monthExposure，将月支藏干与年/月/时干精确匹配，单列日主同字，保留未透藏干与重复柱位。未引入第三方源码或依赖，未裁定月令司权或自动成格。

`npm run check`：52/52 PASS、typecheck/build PASS。四项新增回归覆盖示例庚两透、异干同五行、多个透干、日干单列与候选隔离。Skill 格式、OpenSpec strict、report-check PASS。样例 chartId 保持不变；旧 evidenceId 正确拒绝，核对透干与十神后更新格局论证及渲染，证据 ID 为 `e134e807a907fa036c9060f9a495705580bc82ce0aa9af1653adb379a8b51e6d`。

规则校验只证明可复算的关系和引用；古籍成败条件尚未系统计算。未新增 Fatetell 在线实验、模型跑分或独立代理语义评审。

## 2026-09-23：财格候选前提核对

新增 src/wealth-review.ts：月支财星同干透出为窄入口，八组显干条件逐组列位置与 pending，支持/风险/救应并存，judgment 保持 unresolved。没有扩大为自动成格或破格，也没有复制第三方源码。

`npm run check`：59/59 PASS，typecheck/build PASS；Skill quick_validate、OpenSpec strict 和示例 report-check PASS。七项新增回归覆盖近似十神误替换、救应缺项、日主误计、候选隔离与支持风险并存等。合成报告核对财印同透后补充格局段，chartId 未变、旧证据版本拒绝，当前 evidenceId 为 `726f8809fdfb387d52cecc04e6171b2204f5dd7300dc9db34632949cc27924bf`。

传统原文转录重新读取。计算仅识别显干前提，旺衰、位置和制化有效性未自动裁定；测试不证明理论或现实预测效果。没有 Fatetell 在线请求、额外代理、模型 benchmark 或全局安装。

## 2026-09-23：紫微四化落宫

新增 ziwei-transforms 模块，将生年、大限、流年四化分层定位到本命宫，流年额外按固定宫位 index 映射宫职。大限范围筛选沿用原计算的农历年闭区间。缺星、重名、缺四化槽与缺宫职明确保留，不猜测。未修改原排盘或引入依赖。

`npm run check`：66/66 PASS，typecheck/build PASS；Skill 格式、OpenSpec strict、报告校验 PASS。七项新增回归覆盖主辅星、跨层、宫位数组换序、大限交界、缺失/歧义、无请求年份和候选隔离。示例实际核对 2026 四化落宫后添加运年说明，原 chartId 不变，旧 evidenceId 拒绝，新证据为 `7bde9f2b54147ffbd2f165b3eec3846760571d1ddb11af187412222111766c78`。

核对本地 iztro@2.6.1 运限源码及作者四化说明；库适配和结构测试不构成现实效果认证。大限宫职、宫干飞化、自化、流月流日尚未实现。本轮未做 Fatetell 在线操作、模型跑分或独立代理语义评审。

## 2026-09-23：独立端到端质量验收

新增普通与边界完整报告、追问和时间敏感性比较，启用一个隔离验收代理。发现并修复无关规则夹带、单体系跨体系断言、跨候选拼盘印证三个缺陷；69/69 测试及类型/构建通过。修正断言示例类型与报告未决措辞。工程 PASS，有限样本语义复核 PARTIAL，详见 [质量报告](quality/2026-09-23.md)。未开展 Fatetell 在线实验或全题库模型跑分。

## 2026-09-23：双盘分歧专门验收

五个追问暴露无依据二选一、年界差异误标互补、混合输入误标冲突；修订分析指引并降低两份示例中过强的共同印证。一次定向变体复测通过，事实复算及报告检查通过。未改核心代码，未重跑上轮69项全量检查。范围、原稿与限制见 [专门验收记录](quality/2026-09-23-cross-system.md)。

## 2026-09-23：财印相邻窄条件

新增 wealthReview.sealPlacement，按年/月/日/时固定柱序检查全部显干财印配对，返回 adjacent-risk / no-adjacent-pair / not-applicable，保留中间柱位。相邻风险与隔位并存时不抵消；日主不参与配对但仍占位置；不相邻不升级为成格。

实际核对《子平真诠·论财》原文转录的正反配置并记录来源指纹。`npm run check`：74/74 PASS，类型检查、构建通过；五项新回归覆盖正反配置、无配对/入口外、数组换序和月令外显财。Skill quick_validate 通过。OpenSpec 首次裸命令因未全局安装退出127，随后使用项目记录的 @fission-ai/openspec@1.13.1 固定版本命令严格验证通过。

三份现有报告已逐候选核对；删除唯一新增的 sealPlacement 字段后，重新计算的证据哈希与各报告旧哈希完全一致，确认其他事实和规则未变。旧报告在新证据下被拒绝；新增位置风险进入原例和边界例的格局反证，更新证据ID后校验、渲染通过。普通例 not-applicable，未补造位置判断。[证据记录](quality/2026-09-23-seal-placement-evidence.json)保留旧新哈希与实际位置输出；定义与反例见[研究记录](research/wealth-review.md#财印位置的窄判断)。

已解决的是显干相邻位置条件；合化、通关、强弱、克制有效性和整格成败未自动裁定。本轮无独立代理语义评审、Fatetell 在线实验、模型跑分、全局安装或发布；传统正反命例仅用于结构核对，不证明现实效果。

## 2026-09-23：财旺生官分支反例

新增 wealthReview.officerBranch：既有透财入口且显官时，显干伤官/七杀作为直接采用原文分支的反例返回 blocked；无上述显干反例为 pending，入口外为 not-applicable。所有状态保留具体观察和范围。没有实现自动身强、财旺、合化救应或整体成败判断。

`npm run check`：79/79 PASS，类型检查与构建通过。五项新增回归覆盖伤官阻断、官杀不混用、食神不作伤官、藏杀不作显杀、入口外与候选隔离。Skill格式、OpenSpec严格验证通过。另以合成出生2003-08-11 02:00与04:00实际排盘，分别复现 blocked 与 pending；该例是开发功能对照，不是盲测或现实效果样本。

三份现有报告去除新增 officerBranch 后的旧证据哈希完全匹配，chartId未变；旧报告在新证据下被拒绝。逐候选核对分支状态并补入格局条件说明后，重新校验和渲染通过。边界样例的辛日候选无显官，庚日候选有显官且为pending，未混用。[旧新证据记录](quality/2026-09-23-officer-branch-evidence.json)、[合成追问答复](../examples/acceptance/officer-branch/response.md)、[计算摘录](../examples/acceptance/officer-branch/computation.json)。

原文限制与工程解释见[财官分支研究](research/wealth-review.md#财旺生官分支的反例检查)。本轮没有独立代理语义评审、Fatetell请求、全题库模型跑分、全局安装或发布；工程通过不证明传统理论或现实预测准确性。

## 2026-09-23：规则复核命令

新增 `rule-review --input ... --years ...`，直接复用当前命盘证据，输出财格候选的 Markdown 复核摘要。显示八组显干前提、财印位置、财官分支反例与未决条件，逐候选绑定事实和证据ID；不增加传统规则、不改变命盘/证据生成，不调用模型或写入用户文件。未知时辰沿用退出2及needs-input JSON；不支持的参数拒绝。

`npm run check`：83/83 PASS，类型检查、构建通过。新增四项CLI行为回归覆盖stdin、证据绑定、具体阻断来源、双候选不同状态、入口外、财印全部配对、缺时辰及非法参数。实际运行构建后CLI生成[单候选输出](../examples/acceptance/officer-branch/rule-review.md)和[双候选输出](../examples/acceptance/boundary/rule-review.md)，逐项核对。Skill格式与OpenSpec严格校验通过；三份已有完整报告无需迁移，当前证据校验仍通过。

本入口只提升已有规则的可读性和可用性，不是完整自动命理专家，也不代表预测能力增强。本轮无独立代理语义评审、在线Fatetell操作、全局安装或发布。

## 2026-09-23：自动复核进入完整报告

八字/综合渲染在正文前自动保留财格复核及其事实附录，纯紫微隔离。86/86测试及类型/构建通过；三份既有报告重渲染，候选、链接和证据版本核对通过；Skill与OpenSpec通过。一个独立代理实际完成三组局部追问，未将分支阻断扩为整盘破格、未将藏印视为救应完成，也未按好结论择时辰。不是完整长文独立审查或现实预测验证。详细方法、失败记录与限制见[验收记录](quality/2026-09-23-integrated-rule-review.md)。

## 2026-09-23：新样例完整长文与追问

一个隔离代理完成1996合成样例的全流程长文与追问；主代理复算并发现年份行动顺序缺少依据、同星生年与大限四化选择性遗漏两类问题，修订报告与分析指引。六项原值断言、报告校验/渲染、10:10重算及旧报告拒绝通过。本轮无核心代码变更，未重复上轮86项全量测试。独立初稿不是最终推荐版本，方法与限制见[完整验收记录](quality/2026-09-23-full-report.md)。

## 2026-09-23：自动四化分层核对

针对上一轮实际出现的“只写生年禄、遗漏同期大限忌”，新增基于现有证据的分层展示。紫微/综合报告按每个请求年份连接生年、对应大限与流年；同星不同四化同时列明，保留本命宫与流年宫职。纯八字不插入。事实和规则自动进入可定位附录，不依赖模型主动引用。不新增传统吉凶规则、不改排盘、报告schema或evidenceId。

`npm run check`：94/94 PASS，类型检查与构建通过。八项新增回归涵盖生年禄/大限忌/流年禄并存、大限跨年、宫职分层、缺星/歧义、无年份与无副作用、流年宫职缺失（即使没有跨层差异）、报告自动引用及单体系隔离。首次测试把2028只有流年权的太阴误作跨层差异，发生一项失败；核对事实后改为明确断言它不应出现，并保留天机权/忌作为正例，未改变实现迎合错误预期。

四份已有报告实际重生成，逐候选覆盖、附录锚点、原证据ID核对通过；Skill格式与OpenSpec严格检查通过。范围与文件大小见[渲染记录](quality/2026-09-23-ziwei-layers-evidence.json)，可查看[1996样例](../examples/acceptance/full-1996/report.md)开头的四化分层。该例2026/2027保留天同生年禄及2018—2027大限忌，2028不再带入旧大限。

缺星、歧义及缺宫职显示缺口，不选第一个目标、不用本命宫名补猜流年宫职。相同四化重复不累计概率；未显示差异不等于吉凶已裁定。本轮没有新增独立代理语义评审、模型效果对照、Fatetell请求、全局安装或发布。

## 2026-09-23：出生资料差异命令

新增 `compare --before ... --after ... --years ...`，按选定候选的同名事实项比较两端原值，列变更输入、变化及未变事实、证据绑定。两端使用同一解析年份。未知时辰和未选多候选退出2；多候选必须显式选择比较组合，不自动配对或确认出生时间；单候选的不确定输入仍保留ambiguous与警告。不接受报告文件、不写入或重绑报告。

`npm run check`：102/102 PASS，类型检查、构建通过。八项新增回归覆盖同输入、同一时辰起运变化、跨时辰事实变化、只改地点显示文字的绑定变化、多候选选择及非法ID、未知时辰、区间状态、CLI单侧/双侧stdin及退出码。Skill格式与OpenSpec严格检查通过。

实际构建后CLI生成[1996样例对照](../examples/acceptance/full-1996/compare-output.json)，逐项匹配上一轮人工核对的time-compare：仅input.time与bazi.cycles值变化，旧新绑定均一致对应。另实际运行双候选未选→退出2→指定两个不同候选→退出0流程，保留未定状态，见[运行摘要](quality/2026-09-23-compare-evidence.json)。四份既有完整报告仍通过原证据校验，不需迁移。

bindingMatch只表示两端证据版本相同；即使为true，也没有验证任何未提交的报告正文。候选ID属于各自命盘，不能仅按编号跨输入配对。本轮无独立代理自然语言验收、Fatetell请求、全局安装或发布。

## 2026-09-23：v0.2.0 确定性与验收证据加固

修复同一四柱候选丢失起运范围、多候选以 input.time 冒充体系覆盖、春节前紫微流年过滤使用公历出生年三项问题；新增地点/经度/时区 provenance、文件级自然语言验收与严格运行回执绑定。公开 golden 增加农历四柱及十二宫完整结构。八份当前主报告、1996 compare、两份 rule-review 与 cross-system 计算输出已按新引擎重算；历史质量回执保留原 ID，不回写成新版本结果。

独立 reviewer 未发现 blocker/high，并复现缺失 temperature 被字符串化、部分 provenance 隐藏其余来源缺失两项 P2；修复与回归完成。`npm run check` 为 111/111 PASS，TypeScript/build PASS；Skill quick_validate PASS。固定前向样例内容问题计数为零，但缺实际模型运行回执，`acceptance-check` 按设计返回 PARTIAL。完整范围、证据与剩余限制见 [v0.2.0 加固记录](quality/2026-09-23-v020-hardening.md)。未全局安装、发布、push、调用远端模型或处理真人资料。

## 2026-09-23：多候选起运范围渲染与第二组前向验收

八字/综合报告新增按候选自动生成的出生时间与起运范围段落；显示采样数、不同起运数、出生与真太阳时偏移、起运最早/最晚民用时，并把对应 `bazi.cycles` 事实纳入附录。纯紫微报告保持隔离。边界完整报告已重渲染，两个候选的起运范围分别绑定各自事实。

新增 `semantic-forward-002` 固定套件，覆盖 23:00±2 分钟形成的两个候选。独立代理只读取冻结 Skill、任务和 context；原始回答分别保留两个候选四柱、起运范围、八字和紫微事实，拒绝按有利结果倒选时辰。独立最终复核发现 C1 使用本命天同权、流年天同禄时遗漏同星 2019—2028 大限化忌；三层均落本命官禄。原稿保持不变，内容评审如实修正为 PARTIAL、`premiseOmissions=1`。

最终 `npm run check` 为 113/113 PASS，TypeScript strict 与 build PASS；Skill quick_validate PASS。最终复核同时指出单候选测试不能防多候选串线，随后增加真实双候选分段断言和纯八字正向分支。第一套 manifest 为内容 PASS，第二套原始回答为内容 PARTIAL；另行绑定的 remediation 修订稿补齐 C1 三层天同，独立内容复核五项计数为零。三个 manifest 均无 runtime receipt，`runtimeVerified=false`，最终状态均为 PARTIAL。主报告与按 2026—2028 绑定的边界报告 `report-check` PASS。首次只传 2026 检查边界报告时按设计返回 STALE_REPORT，补齐原绑定年份后通过；没有修改产物来绕过门禁。完整方法见[多候选前向验收记录](quality/2026-09-23-multicandidate-forward.md)。

## 2026-09-23：验收上下文强绑定与第三组边界前向验收

`acceptance-check` 现在读取每个 input/context，以 context.years 和当前引擎重算完整 evidence；未知时辰只接受重算一致的 needs-input chart。跨输入 context、事实篡改、与当前引擎不一致的旧计算结果和 needs-input 冒充 evidence 均拒绝。运行回执与内容评审边界不变。

新增 semantic-forward-003：春节前样例正确区分公历 2000-01-15、紫微农历年 1999、八字立春年界、己卯与请求年份 1999/2000/2026；未知时辰样例拒绝补中午、造盘和给出 2026 唯一结论。原始农历边界回答五项语义计数为零，但 322 字符未达到冻结任务 350 下限，整体如实记为 PARTIAL；独立修订为 355 字符并通过内容复核，未覆写原稿。

`npm run check` 为 115/115 PASS，TypeScript strict、build 与 Skill quick_validate PASS。001、002 原稿、002 修订稿、003 原稿和 003 修订稿五个 manifest 均通过新的 input/context 重算门禁；全部仍因缺少 runtime receipt 返回最终 PARTIAL。完整证据见[验收上下文绑定记录](quality/2026-09-23-acceptance-context-binding.md)。

## 2026-09-23：DST 重复小时前向验收

新增 semantic-forward-004，固定纽约 2021-11-07 01:30 的 earlier/later 两个真实分支。earlier 为 −04:00 / 05:30Z，later 为 −05:00 / 06:30Z；四柱、紫微基础和 2026 事实相同，但 input.time、bazi.cycles 与证据绑定不同。确定性 compare 保存两个变化事实和 27 个未变事实键。

独立回答分别为 260、268 个非空白字符，准确保留各分支 offset、绝对时刻、未来起运值及未来日期的 −04:00；拒绝按命理解读结果选择 DST 分支，并要求核对带时区/夏令时信息的出生记录。内容复核五项计数均为零，reviewStatus PASS；因无 runtime receipt，最终状态按合同为 PARTIAL。详细证据见[DST 前向验收记录](quality/2026-09-23-dst-forward.md)。

## 2026-09-23：确定性错误绑定与 DST 缺失时间

`acceptance-check` 新增 `whoami.error.v1` context error 重放：只接受当前引擎针对同一 input 与显式 years 实际产生的确定性 `InputError`。错误码、说明、命令或年份不一致会拒绝；能正常计算的输入不能冒充失败。CLI 的 context 错误仍写 stderr 并退出 1。

`semantic-forward-005` 固定纽约 2024-03-10 02:30 的春季 DST 缺口。独立回答为 230 个非空白字符，拒绝用 `later` 自动改成 03:30，也没有生成四柱、星曜、起运或流年。内容复核五项计数为零、reviewStatus PASS；缺 runtime receipt，最终状态为 PARTIAL。`npm run check` 为 117/117 PASS，TypeScript strict 与 build PASS。详细证据见[确定性错误前向验收](quality/2026-09-23-context-error-forward.md)。

## 2026-09-23：运行回执信任边界

`whoami.runtime-receipt.v1` 现在明确只表示文件与声明参数绑定。完整 v1 回执返回 `runtimeBound=true`，但没有受信宿主 attestation 或 provider readback 时固定 `runtimeVerified=false`、最终 PARTIAL；手写内部一致 JSON 不再能升级为 verified。回执参数和产物错绑仍按原合同拒绝，内容 FAIL 仍返回 failed。

定向回归覆盖完整自写回执的降级、缺回执、字段缺失、参数错绑、产物漂移和路径边界。完整工程结果及独立复核见[运行回执信任边界记录](quality/2026-09-23-runtime-receipt-trust.md)。

## 2026-09-23：外置 Ed25519 runtime attestation

新增 `whoami.runtime-receipt.v2` 与 `--trusted-runtime-key`。验收器要求调用方显式提供 manifest 目录树外的 Ed25519 SPKI PEM 公钥，以 SPKI DER SHA-256 绑定 keyId，并验证包含 suiteId、运行身份、全部生成产物哈希、rubric 哈希与完整 review 的递归 canonical payload。公钥或签名不匹配、缺外置密钥、使用清单内密钥、非规范 base64、非绝对 startedAt，以及未重签篡改 rubric/review 均拒绝；等价对象键顺序重排保持同一 payload。

v1 仍是 `runtimeBound=true`、`runtimeAttested=false`、`runtimeVerified=false`；v2 签名通过后才有 runtimeAttested，且运行声明完整时才有 runtimeVerified。只有 runtimeVerified 与 review PASS 同时成立才返回 verified；review PARTIAL/FAIL 不因签名升级。详细合同与测试边界见[外置 attestation 记录](quality/2026-09-23-runtime-attestation-v2.md)。

2026-09-24 独立复审确认原 high 与 P2 均关闭：未重签修改 review 状态或任一计数、同步替换 rubric 与普通回执绑定均被拒绝；所有嵌套对象键顺序重排保持同一 payload 并可验签。`npm run check` 为 117/117 PASS，Skill quick_validate PASS；七份固定前向清单重放无错误，仍因没有真实 v2 attestation 保持 PARTIAL。

## 2026-09-24：外部宿主签发交接

新增 `attestation-prepare` 与 `attestation-finalize`。prepare 从 receipt=null 的 draft manifest 和 `whoami.runtime-run.v1` 重算并冻结 canonical payload；finalize 不读取私钥，只以清单外受信公钥重新核对请求、验签，并在 stdout 返回结构化 v2 receipt 及其精确序列化 bytes/base64/hash。它不接受 output 参数，不创建或覆盖回执文件。函数与 CLI 的合成端到端链路已走通；错绑运行、篡改请求、错误签名与清单内公钥均拒绝。测试夹具以外部宿主身份持久化返回字节后，最终 `acceptance-check --trusted-runtime-key` 为 verified。完整合同与限制见[外部签发交接记录](quality/2026-09-24-runtime-attestation-workflow.md)。

`npm run check` 为 120/120 PASS，TypeScript strict 与 build PASS；Skill quick_validate PASS，文档与规格范围 152 个本地链接无缺失。当时的 `openspec/` requirement 只作 Markdown 同步；后续审计确认它不参与运行或验收并已删除，现行合同以 `references/` 与自动测试为准。

独立审查先后复现了三项已废弃写入设计的问题：父符号链接检查后切换导致目录外写入；ENOSPC 部分写入被误报为已有文件并留下截断目标；以及第一轮 canonical 父目录加临时文件方案仍可在真实父目录被重命名、原路径换成目录外符号链接后写出边界。本机 Node/macOS 无法用 `/dev/fd/<dirfd>/...` 创建相对目录句柄文件，Node 也没有可移植 `openat`。最终实现因此删除 output API 和文件写入边界，由外部受信编排器负责持久化；finalize 前后 manifest 目录条目不变。

纯 stdout 版本最终独立复审 PASS，未发现 High/P1/P2/P3。源码定向测试 8/8、dist 工作流探针 3/3 均通过；源码与构建版 CLI 均拒绝 `--output`。复审对 finalize 前后的 manifest 与信任公钥目录逐文件比对名称和内容哈希，确认没有变化；外部夹具持久化精确 `serializedReceipt` 字节后，最终验收为 verified。此前目录替换和部分写入问题已退出 whoami 工具的信任边界，外部编排器的安全持久化仍须单独验收。

## 2026-09-24：Codex 运行时证据能力审计

新增 `npm run audit:codex-runtime`，只读取当前 Codex CLI 版本并在临时目录生成/解析 app-server experimental JSON schema，不启动模型、不读取认证信息、不调用网络。`codex-cli 0.156.1` 的现场 schema 声明 upstream `x-oai-attestation` opaque client token，但没有 manifest/payload bindings；internal/experimental raw response 事件声明 response/thread/turn ID，但本轮没有认证 provider readback。审计因此固定返回 insufficient、`canUpgradeAcceptance=false`，没有放宽 acceptance-check。

新增三项失败封闭合同测试；`npm run check` 为 123/123 PASS，TypeScript strict 与 build PASS。Skill quick_validate 与文档本地链接检查 PASS。实现、官方接口依据和剩余真实宿主 blocker 见 [Codex 运行时证据审计](quality/2026-09-24-codex-runtime-evidence.md)。

## 2026-09-24：报告高风险现实断言门禁

故障注入确认：保持合法 chart/evidence 绑定、factRefs 与 ruleRefs，只把第一条 claim 改为“命主必死，并且投资稳赚，婚姻必然离婚”，旧校验仍会放行。新增统一文本门禁后，同一输入返回 `UNSAFE_REPORT_CLAIM`。门禁覆盖 title、uncertainty、正文与条件、五类八字论证文本和跨体系说明，拒绝死亡/寿命确定性预测、疾病诊断、保证收益/确定性盈亏及必然婚变；明确否定语境允许，转折后的新断言重新检查。

新增三项行为合同；报告定向测试 29/29 PASS，`npm run check` 为 126/126 PASS，TypeScript strict 与 build PASS。全部 example report JSON 的用户可见自由文本扫描无非否定命中；Skill quick_validate 与文档本地链接检查 PASS。规则保持窄范围，不替代前向验收 rubric 的人工 `unsafeClaims` 复核，也不声称完整自然语言语义认证。详细证据见 [报告高风险现实断言门禁](quality/2026-09-24-report-safety-gate.md)。

## 2026-09-24：报告正文—八字论证前提绑定 v3

报告 schema 升级为 `whoami.report.v3`。含八字事实的 claim/crossSystem 必须以 reasoningRefs 绑定每个候选的具体 strength/pattern/climate/balance/selection 论证，premiseStatus 由所引状态派生。缺失、重复、跨候选或无关绑定拒绝；提到旺衰、格局、调候、扶抑、用神/喜忌时要求对应主题。任一所引论证 unresolved 时不能标为 conditional，也不能显式写“已经成立、无需核对、唯一用神”；明确否定这些结论允许。render 在相关正文下显示前提状态与候选/主题。

8 份 report JSON 在不改正文、事实引用和 reasoning status 的前提下迁移，7 份现有 Markdown 重渲染；77 条 claim 分为 unresolved 46、conditional 13、not-applicable 18，7 条 crossSystem 均保持 unresolved。构建版 report-check 以各自原输入和年份重放 8/8 PASS。报告定向测试 33/33、全量 `npm run check` 130/130 PASS，TypeScript strict/build、Skill quick_validate 与本地链接检查 PASS。构建版 CLI 对 v2 schema 返回 `INVALID_REPORT`，对未决前提显式升级返回 `UNRESOLVED_PREMISE_CLAIM`，均退出 1 且 stdout 为空。v2 不能只改 schema；完整证据与剩余语义边界见 [报告前提绑定 v3](quality/2026-09-24-report-premise-binding-v3.md)。

## 2026-09-24：前向验收绑定 v3 报告

acceptance case 新增可选 report artifact。提供时，验收器要求 context 为同 input/years 可重算的 evidence，并以该 evidence 直接执行当前 `validateReport`；needs-input/context error、旧 schema、证据漂移和无效正文均拒绝。result、v1/v2 runtime receipt 与 v2 attestation payload 的逐 case bindings 同步包含 report 哈希；manifest 含 report 而回执漏绑时失败。无 report 的旧 case 保持兼容。

新增 `semantic-forward-006`：固定“用户要求直接把木写成唯一用神”的合成任务，绑定 353 字符交付答复与完整 v3 报告。内容复核五项计数均为零、reviewStatus PASS；报告七节正文保留条件性/未决前提并拒绝唯一化。缺可信 runtime receipt，最终状态如实为 PARTIAL。构建版 CLI 重放全部 8 份固定 manifest 成功；定向 acceptance/attestation 测试 10/10、`npm run check` 132/132 PASS，TypeScript strict/build 与 Skill quick_validate PASS。该样例是本次维护会话固定的合成回归，不是独立宿主或领域专家证明。完整证据见 [前向验收报告绑定](quality/2026-09-24-acceptance-report-binding.md)。

## 2026-09-24：前向答复—报告一致性窄门禁

`acceptance-check` 现在拒绝空白 response，并对所有 response 执行高风险现实断言门禁。case 绑定含八字论证的 report 时，答复若以“唯一用神、结论已定、无需核对条件”等措辞把报告的 conditional/unresolved 前提升级为确定结论，返回 `RESPONSE_REPORT_CONTRADICTION`；“尚不足以定为唯一用神、不支持结论已定”等限制语境允许。result 新增逐 case 的 responseSafety、reportValidation、responseReportPremise 状态。

故障注入确认 response-only 的“投资稳赚不赔”、空白答复和 report/response 前提冲突均失败；semantic-forward-006 的否定性答复三项检查均 PASS。源码入口重放 8 份 manifest、10 个 case 全部成功。构建版 CLI 的正常/越级/高风险三项探针也分别得到 PARTIAL、`RESPONSE_REPORT_CONTRADICTION`、`UNSAFE_REPORT_CLAIM`，失败样例均退出 1 且 stdout 为空。报告/acceptance/attestation 定向测试 43/43、`npm run check` 132/132 PASS，TypeScript strict/build、Skill quick_validate 与本地链接检查 PASS。门禁只覆盖高置信显式冲突，不替代完整语义等价审查。完整记录见 [答复—报告一致性门禁](quality/2026-09-24-response-report-consistency.md)。

## 2026-09-24：前向答复逐段绑定报告 claim

报告型 case 现在必须同时提供 `whoami.response-claims.v1`。sidecar 绑定 report 哈希，并按原顺序、原文字覆盖每个非空 response 段落；每段至少引用一个 report claim，reasoningRefs 必须等于所引 claims 的论证引用并集，premiseStatus 取最保守状态。result、runtime receipt 与 attestation payload 同步纳入 responseClaims 哈希；无 report 的旧 case 继续兼容。

`semantic-forward-006` 已补三段映射，artifactCount 从 7 增至 8，四项 caseChecks 均为 pass。故障注入覆盖 sidecar 孤立/缺失、错绑 report、段落漂移、reasoningRefs 缺项和回执漏绑；哈希同步后的构建版 CLI 篡改探针退出 1 并返回 `RESPONSE_CLAIMS_MISMATCH`。定向 acceptance/attestation 测试 10/10、全量 `npm run check` 132/132、8 份固定 manifest/10 个 case 重放、Skill quick_validate 与 168 个本地链接均 PASS。完整实现、证据与边界见 [逐段答复绑定](quality/2026-09-24-response-claims-binding.md)。

## 2026-09-24：移除 OpenSpec 工程脚手架

现场审计确认 `openspec/` 仅含 5 个 Markdown 文件，共 266 行、21,994 字节，用于保存初始 proposal、design、tasks 与 25 条 requirement/49 个 scenario。它没有 package、TypeScript、源码、测试、CLI 或 Skill 运行依赖；有效行为合同已由 `references/`、源码校验、132 项自动测试和质量记录承载。目录内 tasks 还未同步最新 responseClaims，已经形成重复维护漂移。

当前全局 AGENTS、Codex rules、配置和已安装 Skills 均无 OpenSpec 入口，本机也没有 OpenSpec 可执行文件或全局 npm 包。仓库记录只能证明它是在 2026-09-23 执行已批准实现计划时由工程模板创建，不能证明用户曾单独要求采用 OpenSpec。经用户明确确认后删除整个目录；历史验证记录继续保留并标明不是现行门禁。删除后 `npm run check` 132/132 PASS、TypeScript strict/build PASS，Skill quick_validate PASS；当前行为合同不依赖 OpenSpec。

## 2026-09-24：精简 Skill 日常运行上下文

`SKILL.md` 原先在日常资料与范围段内展开 report/responseClaims、context error、runtime receipt、Ed25519 prepare/finalize 与 Codex runtime audit 的维护细节。完整合同已在 `references/acceptance.md`，普通命理解读无需加载这些内容。现改为按任务路由：日常解读只保留隐私和范围边界；维护 Skill、自然语言回归或接入真实宿主证明时，必须完整读取验收合同。行为约束没有删除，仅从常驻入口移到按需引用。

SKILL 从 7,310 字节降至 6,323 字节，减少 987 字节；Skill quick_validate PASS，46 个 Markdown 文件、168 个本地链接无缺失。本次只调整 Skill 指令分层，不改计算、报告 schema、验收器或测试行为。

## 2026-09-24：按报告模式生成术语速查

`render` 现在按报告模式加入“术语速查”。八字模式只解释日主、月令、透藏、通根、十神、旺衰、格局、调候、扶抑、用神与运年等本报告会用到的八字词；紫微模式只解释命身宫、星曜、三方四正、四化、限年与宫位/宫职分层；综合模式合并两组。解释均保留条件和边界，不把术语写成固定人格、事件预测、概率或现实决策指令，也不改变 report JSON、事实引用或论证结论。

报告测试分别锁定 combined、bazi、ziwei 三种模式的包含与排除关系，并要求资料与风险提示后先显示七节用户正文及跨体系对照，再进入术语速查、自动核对、详细论证和事实附录。六份成对 report JSON/Markdown 用构建版 CLI 原年份重渲染；同名 H2 区块的正文保持逐字一致，只改变区块顺序。普通综合样例的“核心结论”从第 80 行提前到第 13 行，边界样例从第 122 行提前到第 15 行。`full-1991/receipt.json` 同时修正为当前 v3 chartId/evidenceId 及实际 artifact 哈希，四项文件哈希复核均 PASS。

自动显示同时去除支持材料中的内部候选键：单候选使用“当前命盘”，多候选按稳定顺序使用“候选 1”“候选 2”；前提主题按候选归并。六份样例在“可核对的命盘依据”之前均不再出现 candidate ID，附录仍完整保留原始 ID、事实引用和规则引用。`ordinary` 旧报告的 uncertainty 曾主动写出单候选内部 ID，现改为“当前只生成一张命盘候选”；除此之外 report 正文、结构、引用、chartId 与 evidenceId 不变。

报告定向测试 33/33 PASS；全量 `npm run check` 为 132/132 PASS，TypeScript strict 与 build PASS。Skill quick_validate PASS；现行文档范围 46 个 Markdown、168 个本地链接无缺失。术语速查只降低阅读门槛，不证明传统解释正确，也不提高现实预测有效性。

## 2026-09-24：合成用户路径的正文阅读分层

以 `ordinary` 合成资料和 2026—2028 年范围重放 `report-check`，当前 report v3、chartId 与 evidenceId 绑定通过。实际阅读发现，原主文前 91 行有 19 行始终展开的“依据／传统解释把握／条件与限制／八字论证前提”，信息虽必要，但连续打断自然解读。

渲染现将每条 claim 的传统解释把握、未决/条件性状态和完整 conditions 合并为正文可见的“解释边界”；事实链接与具体论证主题进入紧随正文的 `<details>`。crossSystem 保留关系判断和前提状态可见，具体对照依据可展开。折叠不改变 report JSON、校验、引用、前提状态或高风险措辞门禁。

六份成对样例按原年份重渲染，共 56 条 claim、6 条 crossSystem，生成 62 个一一对应的依据展开区。逐项检查确认 56 条 claim 原文精确保留、56 条 conditions 全部直接可见、附录前无内部 candidate ID、附录内原始 ID 完整。报告定向测试 33/33、全量 `npm run check` 132/132、TypeScript strict/build、Skill quick_validate、`full-1991` 四项 artifact 哈希均 PASS；46 个现行 Markdown 的 168 个本地链接无缺失。该验收改善的是阅读层级，不构成独立宿主、命理专家或现实预测有效性证明。

## 2026-09-24：追问答复与维护证据分层

复核五份当前用户追问样例，确认 `ordinary/followups.md` 混入了不存在的 `context.json`、两份未保存的候选盘文件、内部候选 ID、临时目录命令、退出码和可能已被系统清理的产物声明；根示例与 `full-1996` 样例也残留程序状态或精确绑定标识。相关计算差异已有仓库内稳定对照文件，维护过程则已由质量记录承载，不需要继续出现在用户答复中。

当前追问统一改为先直接回答，再给必要依据和改变条件；候选用具体时刻或自然名称表示，只链接现存的出生资料、报告与对照文件。未知时辰答复直接说明不能生成唯一紫微盘，并要求提供时辰或范围，不再展示命令、退出码和临时路径。两个明确标为 baseline 的历史快照未改写。

五份当前追问的展示层扫描未发现 `/tmp/`、内部候选编号、不存在的 chart/context 文件、退出码或命令行片段；5 个本地链接全部存在。`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS；README、SKILL、docs 与 references 共 46 个现行 Markdown、168 个本地链接无缺失。本轮只调整追问样例和写作契约，不改计算、报告 schema 或验收器；文本复核不能证明传统解释或现实预测有效。

## 2026-09-24：精简日常入口与维护文档分层

现场检查发现，README 首页展开了八条前向 manifest 命令、运行回执、Ed25519 签发和 Codex runtime audit；日常必读的 `references/input-and-cli.md` 也包含 benchmark、验收与宿主证明细节。普通排盘虽然不执行这些流程，仍要承担维护系统的阅读成本。

README 现改为快速使用、四步日常工作流、项目边界、维护入口和明确限制，从 9,649 字节降至 4,691 字节。输入与 CLI 契约只保留资料字段、日常命令、出生资料对照和时间口径，从 9,529 字节降至 6,872 字节。benchmark 的完整命令与边界移入原有 `references/acceptance.md`；自然语言验收、运行回执、外部签发和 runtime audit 继续由同一维护契约承载，没有删除 CLI 功能，也没有新增目录或框架。

以 `examples/birth.json` 和 2024—2028 年重放日常路径，`chart`、`context`、`report-check`、`render` 均退出 0。`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS；README、SKILL、docs 与 references 共 46 个现行 Markdown、153 个本地链接无缺失。链接数减少来自首页移除重复的历史验收链接，不是目标文件丢失。本轮只调整文档装载层级，不改变计算、报告 schema、验收器或发布状态。

## 2026-09-24：压缩 Skill 报告入口并保持行为语义

`SKILL.md` 的解读与交付段原先重复展开 v3 字段绑定、自动渲染顺序、候选覆盖、起运范围、四化分层和用户展示细节；这些强制要求已经逐项存在于日常必读的 `references/report.md`。入口现保留完整遵守报告契约的强制指令、`report-template` → 写作与前提核对 → `report-check` → `render` 的执行顺序，以及同一 context/years、五项八字论证、未决前提、多候选事实、人工语义核对和用户展示等关键不变量。

压缩前后按 13 项义务核对：v3 与真实 ID、五项八字主题、reasoningRefs/premiseStatus、候选与模式覆盖、起运范围、四化分层、自然候选标签、可见解释边界、旧报告重核及人工语义检查全部有强制入口或报告契约落点，13/13 PASS。`SKILL.md` 从 7,171 字节降至 5,928 字节，减少 1,243 字节；没有为减少长度放宽条件、例外、证据等级或完成标准。

合成报告 `report-check` 与 `render` 均退出 0；`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS，46 个现行 Markdown 的 153 个本地链接无缺失。本轮未调用外部模型或独立宿主，也没有改写带历史 Skill snapshot 的固定前向样例；结果证明当前合同与本地流程仍一致，不构成模型普遍表现或现实预测有效性证明。

## 2026-09-24：旺衰与扶抑的两类最低条件结论

针对“事实很多但只能写尚未裁定”的问题，重新核对《子平真诠·论十干得时不旺失时不弱》和《滴天髓阐微·体用》的当前公开转录。前者支持不能只凭月令判强弱，并区分通根与显干帮扶；后者要求根据强弱和具体负荷进入扶抑分支，同时保留旺极、弱极等例外。原文没有提供数量阈值，本轮没有发明加权分数或自动身强标签。

分析契约新增两类最低结论：至少一处同类根未见直接六冲并另见印比支持时，可条件性确认“并非无根、存在支持基础”，但不能直接写身强；月令所藏某十神同干透出且同类负荷另有可定位支持时，可把该负荷列为优先比较分支，但不能直接写成该负荷最强、日主偏弱或现实结果。只有最低结论及其限制均有事实支持时，相关 reasoning 才可从 unresolved 收窄为 conditional。

主合成样例据此重写：旺衰由 unresolved 改为 conditional，确认午根、受冲寅根和甲印构成支持基础；扶抑由 unresolved 改为 conditional，把申月庚财两透相对根印支持列为第一比较分支，并明确只有“普通格、偏弱、财为主要负荷、比劫实际可用”同时成立时才讨论比劫帮身任财。格局、调候和最终用神继续保持 unresolved。财运与追问正文同步展示这条推理，不再用泛化的五行资源类比代替取法；两庚不重复计权，也没有写成财旺或现实财运判断。

更新前后 chartId 与 evidenceId 不变；`report-check` 返回 valid，重新 `render` 的输出与 `examples/report.md` 字节一致。`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS；来源 manifest JSON 有效，46 个现行 Markdown 的 153 个本地链接无缺失。本轮没有增加核心自动裁定、报告 schema 或新依赖，也未经过传统命理领域专家审校；条件性收窄提高解释深度，不证明传统理论或现实预测有效。

## 2026-09-24：旺衰最低条件正例与双反例

用当前核心重算三份合成输入，核对“未冲同类根”和“额外印比支持”必须同时成立。正例庚辰、甲申、丙午、庚寅中，午中丁根未列直接六冲，月干甲偏印提供独立支持，主报告可保留 strength=`conditional`；寅根受申冲、申月和两庚财荷继续作为反证，不据此判身强。

反例 A 己巳、壬申、甲寅、壬申保留月、时双壬偏印，但唯一寅中甲根同时受两申直接冲，因此只满足额外支持、不满足未冲根。反例 B 辛酉、丁酉、甲寅、己巳保留一处未受直接六冲的寅中甲根，但除日干及该根事实外没有独立印比，因此只满足未冲根、不满足额外支持。两例的最低规则结果均为 NOT MET，也都不能反推身弱。

正例重算标识与当前主报告完全一致；反例 A 复用历史消融的出生输入，以当前核心及原 2026—2028 年范围重算，未改写旧 context 快照或其 manifest；反例 B 使用新固定的合成出生输入。三例形成 `PASS+PASS`、`FAIL+PASS`、`PASS+FAIL` 的最小真值对照。完整记录见 [旺衰最低条件正例与双反例](quality/2026-09-24-strength-minimum-contrast.md)。本轮只收紧 Skill 分析合同并增加轻量验收记录，没有新增自动旺衰逻辑、报告 schema、依赖或工程框架。

## 2026-09-24：负荷优先比较最低条件正例与双反例

把第二条最低结论明确为合取条件：月支所藏食伤、财或官杀之干至少一处同干透出，并且在月支来源及选作透出证据的柱位之外，另一柱位还能定位同类负荷。食神/伤官、正财/偏财、正官/七杀分别归组，但保留正偏身份；同一透干或同一柱的透藏不能重复满足两个条件。

主合成样例的申中庚偏财透年、时两柱，形成 `PASS+PASS`，所以财荷可以优先与根印支持比较。反例 A 己巳、壬申、甲寅、壬申中，申藏庚七杀未透，但年、时支另藏庚，形成 `FAIL+PASS`；反例 B 辛未、戊戌、乙卯、壬午中，戌藏辛七杀只透年干，日、时柱没有另一处官杀，形成 `PASS+FAIL`。两种反例均不得由本条把 balance 收窄为 conditional，也不能反推相应负荷很轻。

三例均由当前核心按固定年份重算；正例标识与主报告一致。反例 B 同盘的财分支满足最低条件，不能借给官杀分支，进一步确认必须逐月藏干、逐负荷类别判断。完整记录见 [负荷优先比较最低条件正例与双反例](quality/2026-09-24-load-minimum-contrast.md)。本轮没有新增自动负荷评分、核心标签、报告 schema、依赖或工程框架。

## 2026-09-24：财格候选入口与成格未决分层

明确区分核心已经确认的候选入口与仍未裁定的格局成败：`wealthReview.status=candidate-only` 且 candidates 非空时，pattern 可以条件性写“财格候选入口已满足”，但同段必须说明只确认候选身份；`judgment=unresolved`、旺衰、位置、合化、制化、救应和格局用神继续未决。`outside-scope` 只表示本模块入口未满足，不得改写成无财格、财格失败或 not-applicable。

当前主样例申藏庚偏财且年、时两透，pattern 从 unresolved 收窄为 conditional，只确认偏财格候选入口。两个近失配保持入口外：庚午、戊子、丁巳、甲辰虽年干见庚正财，但子月不藏财；己巳、壬申、甲寅、壬申虽申藏戊偏财且年干见己正财，但己戊不同干。前者防止其他柱显财冒充月令财，后者防止同五行或同财类异干冒充同干透出。

主报告仅将 pattern 及只引用 strength/pattern 的性格段前提改为 conditional；仍引用 climate 或 selection 的段落继续 unresolved。chartId 与 evidenceId 不变，`report-check` 返回 valid，重新 `render` 与示例 Markdown 字节一致。`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS；49 个现行 Markdown 的 167 个本地链接无缺失，`openspec/` 仍不存在。完整边界与重算标识见 [财格候选入口与成格未决的分层验收](quality/2026-09-24-pattern-candidate-boundary.md)。本轮未新增自动成格逻辑、报告 schema、依赖或工程框架。

## 2026-09-24：丙火申月调候候选边界

以中国国家图书馆藏、1926 年文明书局《滴天髓·穷通宝鉴》第 2 卷扫描本为主来源，逐页核对 PDF 第 32—33 页（书页 31—32），并与维基文库转录交叉检查。“七月丙火”条目确认壬水为该版本下的调候复核候选，紧接段落同时保留壬多取戊制及壬、戊多寡条件；没有采用现代白话解释代替古籍版本，也没有吸收功名、富贵等结果断语。

运行参考将适用入口限定为同一候选的 `dayMaster=丙` 与 `month.branch=申`。主样例满足两项，申中壬、戊均未同干透于年/月/时，因此 climate 从“尚未找到具体候选”的 unresolved 收窄为 conditional，只确认来源特定的壬水候选；selection 仍为 unresolved。两个近失配分别保留丙日但改为巳月、保留申月但改为甲日，形成 `PASS+FAIL` 与 `FAIL+PASS`，均不得套用该条目。

主报告 chartId/evidenceId 保持不变，`report-check` 返回 valid，重新 `render` 与示例 Markdown 字节一致。`npm run check` 为 132/132 PASS，TypeScript strict 与 build PASS；Skill quick_validate 在隔离的 `uv --with pyyaml` 环境中 PASS；54 个现行 Markdown 的 179 个本地链接无缺失。结构化报告为 28,589 字节、SHA-256 `a92d530ebd2161970562c69f8bfe09ad3e84338dea59f98e6d9f89fce1a3443a`；Markdown 为 67,067 字节、SHA-256 `21253175017d4157f3f5f105c1eff2cb47e9f46ae9524dbb7c9fb304c401165f`。完整来源、正反例与限制见[调候候选边界](quality/2026-09-24-climate-candidate-boundary.md)。本轮未新增自动调候表、评分、核心标签、报告 schema、依赖或工程框架，也不以测试证明传统理论或现实预测有效。

## 2026-09-24：最终取舍状态边界

最终取舍不再按 strength、pattern、climate、balance 的状态数量投票。`selection=conditional` 必须在明确范围内提出具体取用方向，并写全成立前提、反证和撤回条件；候选入口、支持基础或尚待比较的分支不能直接升级成最终方向。其他 topic 尚有 unresolved 时仍允许范围完整的局部候选，四个 topic 都是 conditional 时也不会自动得出统一喜用。

固定三例覆盖两侧边界：`strength-balance` 在普通格且暂偏弱的限定语境中明确落到印星木候选，保留 conditional；主样例的支持基础、偏财格入口、壬水调候候选和财荷优先比较没有收敛为同一具体方向，保持 unresolved；`full-1991` 的财、杀、食伤分支仍依赖未裁定的强弱和主要负荷，也保持 unresolved。完整判断见[最终取舍状态边界验收](quality/2026-09-24-selection-status-boundary.md)。

三份构建版 `report-check` 均返回 valid；主样例重新 `render` 后与 `examples/report.md` 字节一致。主报告 chartId / evidenceId 保持为 `a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789` / `3d0b34bd617494d53f269cc99fa79edf01647a9ebb72b0fc6a806970d096ea9e`。结构化报告为 28,901 字节、SHA-256 `404cd7584a2258984e35dbc80a0bdeecf9c5e88a748ef3209af2a1088b874b50`；Markdown 为 67,379 字节、SHA-256 `f0607f656424cba05bcc392437da07bc1fdd0b74ba4c7dc801ce87ec325caa1e`。Skill quick_validate PASS；57 个现行 Markdown 的 192 个本地链接无缺失；`openspec/` 仍不存在。

本轮只改运行参考、研究说明、质量记录和主样例文字，没有修改 `src/`、`tests/`、报告 schema、依赖或自动语义门禁。最近一次全量代码门禁仍是前一阶段已记录的 `npm run check` 132/132 PASS；selection 文档收口后未重复运行，不能把该历史结果表述为本轮新验证。结构检查和人工语义复核也不证明传统理论或现实预测有效。

## 2026-09-24：年度标签与行动日程边界

审计主合成报告发现，原运年段在列出 2024—2028 的八字年度柱和紫微四化星名后，直接把五年依次定义为校准、学习、展示、流程化和审视机会；职业段也把甲辰、乙巳、丙午、丁未、戊申分别连接到补能力、展示、沉淀流程和转型。这里缺少逐年四化落宫、流年宫职、主题宫星曜、三方四正、跨层差异及八字作用链，星名与年序不足以证明该行动日程。

主报告现保留年表事实与两个窄差异：2026 丙午与本命日柱同柱，2028 戊申再次进入原局申寅冲结构；两者只触发进一步复核，不推出升职、离职、迁移、换团队或扩张。五年固定任务表已删除。若要给年度主题，必须补齐分层落宫与同一现实问题的作用论证；职责、预算、合作和风险复盘按现实机会执行，不等待命理年份。完整边界见[年度标签、四化清单与行动日程](quality/2026-09-24-yearly-timing-boundary.md)。

主样例与 1996 对照样例的构建版 `report-check` 均返回 valid；主样例重渲染与 `examples/report.md` 字节一致，旧固定日程措辞扫描无命中。主报告 chartId / evidenceId 不变。JSON 为 29,180 字节、SHA-256 `b6296386bb0cab9abca77a8053fb3d612ae4f4a0c4353b4c5bfd4d4613239ea1`；Markdown 为 67,658 字节、SHA-256 `3b16cd0087c12abcc43ec10b53d9f478743b00cec56c195822d76ad9b4a7aace`。Skill quick_validate PASS；58 个现行 Markdown 的 193 个本地链接无缺失；`openspec/` 仍不存在。

本轮只改紫微运行参考、研究与路线记录、质量记录及主样例文字，没有修改四化计算、测试、报告 schema、依赖或自动校验器。最近一次全量代码门禁仍为前序已记录的 `npm run check` 132/132 PASS，本轮没有重复执行。结构校验与文本收紧不证明紫微理论或现实预测有效。

## 2026-09-25：紫微论证前提绑定 v4

报告 schema 升级到 `whoami.report.v4`：ziwei/combined 逐候选填写本命结构、事业联宫、财运联宫、关系联宫、限运与四化五类 `ziweiReasoning`。引用紫微事实的 claim 按章节绑定对应主题，综合判断同时绑定同一候选的八字与紫微前提；`premiseStatus` 取所引两体系论证中的最保守状态。v3 仅兼容八字单体系历史报告，v3 紫微/综合失败封闭。

六份当前报告迁移到 v4，构建版 `report-check` 全部 valid，重渲染与当前 Markdown 逐字节一致；固定 `semantic-forward-006` 的 v3 八字报告继续 valid，acceptance-check 四项 caseChecks 均 pass，但因无可信 runtime receipt 保持 partial。v3 综合 baseline 返回 `INVALID_REPORT`，v3 八字 baseline 继续 valid。`full-1991` 收据四项哈希一致。`npm run check` 为 135/135 PASS，TypeScript strict 与 build PASS；Skill quick_validate PASS，现行范围 59 个 Markdown 的 205 个本地链接无缺失；`openspec/` 仍不存在。

主报告 chartId/evidenceId 未变；JSON 为 35,266 字节、SHA-256 `975eab95a62eb1a6669d2c6552f992601e88630ca5f32e7c978e0712e0bfe617`，Markdown 为 72,272 字节、SHA-256 `f66b68fae2e24d9b6b14703145c2df6c7d88adc4cdf192132f1f82d4c1af0686`。完整边界与证据见[紫微论证前提绑定 v4](quality/2026-09-25-ziwei-premise-binding-v4.md)。结构、引用和窄范围措辞门禁不构成传统学理审校、完整自然语言语义认证或现实预测有效性证明。

## 2026-09-25：v4 紫微单体系前向样例

新增 `semantic-forward-007`，固定用户要求从2024—2028四化清单直接给出升职、收入和关系结果的诱导任务。维护者编写的 v4 紫微模式报告逐候选覆盖本命结构、事业、财运、关系和限运五类 ziweiReasoning；七节正文按主题绑定，timing 与依赖它的 advice 保持 unresolved。358 个非空白字符的交付答复拒绝事件日程，并说明本命落宫、流年宫职、主题宫、三方四正、跨层差异、定位缺口、现实触发和撤回条件。

构建版 `report-check` 返回 valid；`acceptance-check` 的 responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass，五项问题计数为 0、reviewStatus=PASS、artifactCount=8。没有可信 runtime receipt，runtimeBound/runtimeAttested/runtimeVerified 均为 false，最终状态保持 partial。固定样例回归 7/7 PASS，全量 `npm run check` 为 136/136 PASS，TypeScript strict 与 build PASS；九份 semantic-forward manifest 均由当前构建版 CLI 重放成功，三个旧研究 manifest 使用另一 schema，不计入 acceptance-check 套件。Skill quick_validate PASS；现行范围 60 个 Markdown 的 209 个本地链接无缺失；`openspec/` 仍不存在。

完整产物、指纹和证据边界见[v4 紫微年度越界前向验收](quality/2026-09-25-ziwei-forward-v4.md)。该样例由主代理编写与复核，不是独立模型盲测或命理专家证明；结构门禁仍不能自动认证紫微作用链的传统学理正确性。

## 2026-09-25：紫微限运作用链 v5

报告 schema 升级到 `whoami.report.v5`。`ziwei-timing` 现在必须以 `timingChain` 绑定目标主题、证据包内年份、同候选四化/大限或流年/主题宫事实、跨层复核、现实依据、未闭合环节和撤回条件；三组引用须纳入本项论证依据。现实资料未提供时 source 必须为 null、缺口不得为空，限运状态强制 unresolved。声明已提供现实资料只建立来源可追踪性，conditional 还要求缺口为空；程序不据此认证来源或传统推论。

v3/v4 仅兼容八字单体系历史报告，旧 schema 的紫微/综合报告失败封闭。六份活跃报告迁移至 v5 并按原输入与年份重算为 valid、重新渲染；`semantic-forward-007` 同步迁移并更新 report/responseClaims/manifest 绑定，358 字符交付答复保持不变。其 acceptance-check 四项 caseChecks 均 pass、五项计数为 0、reviewStatus=PASS，仍因没有可信 runtime receipt 保持 partial。

新增两组行为合同覆盖作用链引用、年份、字段位置和现实触发状态；`npm run check` 为 138/138 PASS，TypeScript strict 与 build PASS。九份 semantic-forward manifest 均由当前构建版成功重放，原始 PARTIAL 评审未被改写。Skill quick_validate PASS；现行范围 61 个 Markdown 的 216 个本地链接无缺失；`openspec/` 仍不存在。主报告 JSON 为 36,706 字节、SHA-256 `d2bcd21e1c473c7845b26c65343f925715852a5fd99f31ed78da4a2309914061`，Markdown 为 73,260 字节、SHA-256 `6a4dfc60fe90b6391f23a7ceff91721fd4316fd562b1339383f7c1d4f034dd51`。完整证据与限制见[紫微限运作用链 v5](quality/2026-09-25-ziwei-timing-chain-v5.md)。

## 2026-09-25：紫微年度正文与作用链绑定 v5

含紫微事实的 claim/crossSystem 只要出现当前 evidence 的具体年份或年份区间，现在必须逐候选绑定 `ziwei-timing`，且文字涉及的全部年份都在同候选 `timingChain.years` 中。常见区间会覆盖中间的每个已请求年份；范围外的出生年和文献年份不触发限运绑定。新增未决限运前提后，段落 `premiseStatus` 服从最保守状态。

主报告补 2 条、1996 综合样例补 5 条、普通综合样例补 1 条年度前提绑定；边界双候选与 semantic-forward-007 原已合规。新增回归覆盖“年份段只绑事业主题”和“2026—2028 链条漏掉 2027”两种绕过。`npm run check` 为 139/139 PASS，TypeScript strict 与 build PASS；五份紫微/综合报告扫描无漏绑，六份活跃报告的构建版 report-check 均为 valid，007 acceptance-check 四项 caseChecks 均 pass。九份 semantic-forward manifest 重放成功；Skill quick_validate PASS，62 个现行 Markdown 的 221 个本地链接无缺失，99 个 JSON 可解析，`full-1991` 收据哈希无漂移，`openspec/` 不存在。主报告 JSON 为 36,924 字节、SHA-256 `515cdb2dd06558ce9f24ffb257cc871e3edc7f06bb48c65e0ec2123f0ee057ff`，Markdown 为 73,312 字节、SHA-256 `a7dfd18ffb9c3ba7eac05eca68fc37db46be721664dee484f91349e65b473b09`。完整证据与剩余相对时间语义边界见[紫微年度正文与作用链绑定 v5](quality/2026-09-25-ziwei-year-claim-binding-v5.md)。

## 2026-09-25：报告相对时间基准 v6

报告 schema 升级到 `whoami.report.v6`，顶层冻结 `timeReference.asOfDate` 与 IANA `timeZone`。所有用户可见报告自由文本中的“今年/本年/明年/后年/去年/前年”按冻结日期年份解析；结果必须已在 evidence.years。含紫微事实的 claim/crossSystem 继续要求同候选 `ziwei-timing` 与完整 timingChain.years；“下个大限/下一大限/下一个大限”因无法唯一定位而失败封闭。v5 只兼容不含相对年份的既有报告，v3/v4 仍只兼容八字单体系历史报告。

六份活跃报告迁移到 v6，固定 `2026-09-25 / Asia/Shanghai`，按原输入和年份由构建版 report-check 全部返回 valid 并重新渲染。`semantic-forward-007` 保持冻结 v5 字节不变，以验证窄兼容路径；其 acceptance 四项 caseChecks 均 pass、reviewStatus=PASS，仍因无可信 runtime receipt 保持 partial。

新增回归覆盖日期解析、限运绑定、年份越界、模糊大限、无效日期/时区、v5 拒绝相对年份及“未来年份/今后年份”误报。`npm run check` 为 140/140 PASS，TypeScript strict 与 build PASS；九份 semantic-forward manifest 由当前构建版全部重放成功，既有内容评审不变。Skill quick_validate 通过隔离 PyYAML 环境 PASS；AGENTS/README/SKILL/references/docs 范围 62 个 Markdown、232 个本地链接无缺失；不读取 private，private 与 node_modules 之外 90 个 JSON 可解析；`full-1991` 收据四项哈希一致；`openspec/` 不存在。

主报告 JSON 为 37,012 字节、SHA-256 `2c036c7bdaf8698d80d9e314aa2d31c4d97b6bfc562a76738ec7f31db5b455bc`，Markdown 为 73,432 字节、SHA-256 `20b350481a0465002d9ae742271e93b31f859d0a540ec3fcba092f9b26108575`，chartId/evidenceId 未变。完整实现、样例与限制见[报告相对时间基准 v6](quality/2026-09-25-relative-time-reference-v6.md)。结构门禁只固定文字含义和前提绑定，不证明传统理论或现实预测有效。

## 2026-09-25：v6 相对时间前向样例

新增 `semantic-forward-008`。任务与量表先于答复固定，要求从 `2026-09-25 / Asia/Shanghai` 解析明年=2027、后年=2028，并把用户所说的模糊周期改写为 context 中明确的当前 2022—2031、后续 2032—2041。v6 紫微报告在事业、财运、关系段同时绑定各自主题与 `ziwei-timing`，限运作用链保留现实资料和逐年关系缺口，因此全部相关正文保持 unresolved。

405 个非空白字符的交付答复逐项拒绝保证升职、收入翻倍和婚变；responseClaims 逐段绑定 report claim、论证引用与最保守状态。构建版 acceptance-check 的 responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass，五项问题计数为 0、reviewStatus=PASS、artifactCount=8。没有可信 runtime receipt，最终状态保持 partial。

自动回归新增 1 项；`npm run check` 为 141/141 PASS，TypeScript strict 与 build PASS。十份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 63 个现行 Markdown、239 个本地链接无缺失；不读取 private，private 与 node_modules 之外 95 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与证据限制见[v6 相对时间前向验收](quality/2026-09-25-relative-time-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 缺年停机与补算前向样例

新增双 case `semantic-forward-009`。第一阶段绑定只含 2026 的 baseline context；178 个非空白字符的答复把明年解析为 2027，发现它不在 evidence.years 后停下，不生成 report 或编造 2027 四化。第二阶段以同一 input 补算 2026—2027：chartId 保持不变，evidenceId 从 baseline 的 `821d437569b9eaf0d0cdddd3fbd029f9c9bdb441d93dbf6f87082cce7f3f74eb` 更新为 `2fca890776d377112b8dc47edddb526a4f9e1bd8afa687bfbf719362de949f28`。

补算后的 v6 紫微报告绑定新 evidenceId；事业正文保留明年=2027，同时绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。434 字符答复明确区分“补齐年份事实”和“作用链/现实触发已经闭合”。第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；无可信 runtime receipt，最终状态保持 partial。

自动回归新增 1 项；`npm run check` 为 142/142 PASS，TypeScript strict 与 build PASS。十一份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 64 个现行 Markdown、248 个本地链接无缺失；不读取 private，private 与 node_modules 之外 101 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 缺年补算前向验收](quality/2026-09-25-relative-year-expansion-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 跨年时区前向样例

新增双 case `semantic-forward-010`，固定同一绝对时刻 `2026-12-31T16:30:00Z`。锁定 Temporal 实现将它换算为上海 `2027-01-01T00:30:00+08:00` 与洛杉矶 `2026-12-31T08:30:00-08:00`；宿主据此分别冻结 `2027-01-01 / Asia/Shanghai` 和 `2026-12-31 / America/Los_Angeles`，再把“明年”解析为 2028 与 2027。出生资料时区仍为上海，洛杉矶报告没有被出生时区或机器日期覆盖。

两份 context 来自同一 input，chartId 一致，years 分别为 `[2027, 2028]` 与 `[2026, 2027]`，evidenceId 随年份范围变化。两份 v6 紫微报告只绑定各自 evidenceId；事业段、timingChain 与 responseClaims 分别覆盖对应年份，并继续保留现实岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。上海 452 字符、洛杉矶 450 字符答复均说明 report-check 只校验已经冻结的日期与证据绑定，不声称自动认证绝对时刻换算。

两 case 的 responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass，五项问题计数为 0、reviewStatus=PASS、artifactCount=13；缺可信 runtime receipt，最终状态保持 partial。自动回归新增 1 项；`npm run check` 为 143/143 PASS，TypeScript strict 与 build PASS。十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 65 个现行 Markdown、260 个本地链接无缺失；不读取 private，private 与 node_modules 之外 109 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 跨年时区前向验收](quality/2026-09-25-cross-zone-year-boundary-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 历法限定相对时间前向样例

报告时间门禁新增历法限定窄模式：“农历明年”“明年按农历”“过完/过了春节或立春”“春节/农历新年/立春前后”等不能再由公历 `asOfDate` 静默解析，统一返回 `AMBIGUOUS_RELATIVE_TIME`，要求先写明公历年份与体系年界。明确的“2027 紫微流年按农历年标签”“八字 2027 年界按立春口径”继续允许；门禁不因“农历年标签”或“立春年界”关键词本身误杀。

新增双 case `semantic-forward-011`。第一阶段 245 字符答复说明普通明年按 `2026-09-25 / Asia/Shanghai` 指向 2027，但公历元旦、紫微农历新年和八字立春年界不能混为同一日期，因此停下且不生成 report。第二阶段按用户澄清只采用 2027 紫微农历年标签；v6 紫微报告绑定同一 2026—2027 context，正文不再含被拒绝表达，事业段同时绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。411 字符答复继续保留现实资料与作用链缺口。

第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 145/145 PASS，TypeScript strict 与 build PASS。十三份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 66 个现行 Markdown、269 个本地链接无缺失；不读取 private，private 与 node_modules 之外 114 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 历法限定相对时间前向验收](quality/2026-09-25-calendar-qualified-relative-time-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明传统历法或现实预测有效。

## 2026-09-25：v6 年度以下时间粒度前向样例

报告时间门禁新增细分粒度窄模式：“上半年/下半年/年初/年中/年底/年末”、季度、相对月份、相对星期，以及“三个月内/未来十天”等持续时间不能再由年度 evidence 承载，统一返回 `UNSUPPORTED_TIME_GRANULARITY`。明确的“2027 年度主题”“月份资料尚未提供”“流月与流日未计算”继续允许；春节、农历新年或立春前后的表达仍先由历法限定门禁拒绝。

新增双 case `semantic-forward-012`。第一阶段 265 字符答复说明普通明年按 `2026-09-25 / Asia/Shanghai` 指向 2027，但当前 context 没有半年、季度、月、周、日或精确节气证据，因此停下且不生成 report。第二阶段按用户澄清只采用 2027 年度事业主题；v6 紫微报告绑定同一 2026—2027 context，正文不再含被拒绝的细分时间，事业段同时绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。395 字符答复继续保留现实资料与作用链缺口。

第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 147/147 PASS，TypeScript strict 与 build PASS。十四份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 67 个现行 Markdown、278 个本地链接无缺失；不读取 private，private 与 node_modules 之外 119 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 年度以下粒度前向验收](quality/2026-09-25-subannual-time-granularity-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 模糊时间范围前向样例

报告时间门禁新增范围未定义窄模式：“近期、不久、很快、过阵子、什么时候、短期内、未来一段时间”等不能再由宿主自行换算，统一返回 `AMBIGUOUS_TIME_HORIZON`。它与 `AMBIGUOUS_RELATIVE_TIME` 的历法年界歧义、`UNSUPPORTED_TIME_GRANULARITY` 的已知粒度证据不足分开；明确 YYYY 年度主题或明确日期范围后才可继续，后者还必须具备相应粒度 evidence。

新增双 case `semantic-forward-013`。第一阶段 230 字符答复说明用户的时间词没有确定年份或起止范围，当前 context 只有 2026—2027 年度 evidence，因此停下且不生成 report。第二阶段按用户澄清只采用 2027 年度事业主题；v6 紫微报告绑定同一 context，正文不再含被拒绝的模糊时间，事业段同时绑定 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain。365 字符答复继续保留现实资料与作用链缺口。

第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 149/149 PASS，TypeScript strict 与 build PASS。十五份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 68 个现行 Markdown、287 个本地链接无缺失；不读取 private，private 与 node_modules 之外 124 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 模糊时间范围前向验收](quality/2026-09-25-vague-time-horizon-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 多年范围闭区间前向样例

报告时间门禁新增相对多年范围和明确年度闭区间两层检查。“未来三年、三年内、接下来五年、这几年、近几年、长期会怎样”等返回 `AMBIGUOUS_YEAR_RANGE`，要求先明确首尾年份及是否包含当前年；升序 `YYYY—YYYY 年度`闭区间任一年缺少 evidence 时返回 `TIME_RANGE_OUT_OF_SCOPE` 并列出缺年。普通“长期观察/积累”和大限周期标签不被误报。

新增三 case `semantic-forward-014`。第一阶段 244 字符答复识别多年范围未定义后停下；第二阶段在用户选择 2027—2029 后，以 baseline context 精确识别缺少 2028、2029，254 字符答复继续停下。第三阶段使用同一 input 补算 2026—2029：chartId 保持，evidenceId 更新；v6 紫微报告采用明确年度闭区间，timingChain.years 覆盖 2026—2029。387 字符答复继续保留现实资料与逐年作用链缺口。

前两 case 的 responseSafety pass，其余三项 not-applicable；第三 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=14；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 151/151 PASS，TypeScript strict 与 build PASS。十六份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 69 个现行 Markdown、298 个本地链接无缺失；不读取 private，private 与 node_modules 之外 130 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 多年范围闭区间前向验收](quality/2026-09-25-multiyear-range-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 绝对时点与命名历法点前向样例

报告时间门禁新增绝对月日星期与命名历法点两类检查。evidence 年份内或没有年份的月、日、星期返回 `UNSUPPORTED_TIME_GRANULARITY`；带相对/明确年份或事件语境的春节、农历新年与节气返回 `UNSUPPORTED_CALENDAR_POINT`，要求先明确公历日期、历法、时区和日级 evidence。早于冻结报告年份且不在 evidence.years 的历史年月只在报告标题与 `timingChain.realityBasis.source` 中允许，claim、论证与建议仍会拒绝；裸的年度边界说明也继续允许。

新增双 case `semantic-forward-015`。第一阶段 244 字符答复区分两类时点后停下，不生成 report；第二阶段按用户澄清只采用 2027 年度事业主题，v6 紫微报告绑定同一 2026—2027 context，允许历史出生日期和裸年界说明，不再包含被拒绝的未来绝对时点。370 字符答复逐段绑定 timing、career 与 advice，并继续保留现实资料、跨层作用、定位缺口和撤回条件。

第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 153/153 PASS，TypeScript strict 与 build PASS。十七份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 70 个现行 Markdown、307 个本地链接无缺失；不读取 private，private 与 node_modules 之外 135 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 绝对时点与命名历法点前向验收](quality/2026-09-25-absolute-calendar-point-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 数字日期与日内时点前向样例

报告时间门禁新增带判断语境的数字日期与日内时点检查。`2027-03-15`、`2027/03/15`、`2027.3.15`、`3.15` 等数字日期用于升职、结果、行动或窗口判断时返回 `UNSUPPORTED_TIME_GRANULARITY`；今晚、明早、明天上午、上午九点、09:30 等相对日内时点或钟点用于事件判断时返回 `UNSUPPORTED_TIME_OF_DAY`。出生时间、冻结日期、太阳时和周期边界等非事件事实继续允许，避免因格式误伤可复算资料。

新增双 case `semantic-forward-016`。第一阶段 258 字符答复区分数字日期与日内时点后停下，不生成 report；第二阶段按用户澄清只采用 2027 年度事业主题，v6 紫微报告绑定同一 2026—2027 context，保留 `2026-09-25` 冻结日期，但不再把数字日期或钟点用于事件判断。376 字符答复逐段绑定 timing、career 与 advice，并继续保留现实资料、跨层作用、定位缺口和撤回条件。

第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 155/155 PASS，TypeScript strict 与 build PASS。十八份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 71 个现行 Markdown、316 个本地链接无缺失；不读取 private，private 与 node_modules 之外 140 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 数字日期与日内时点前向验收](quality/2026-09-25-numeric-date-time-of-day-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 歧义与非法日期时刻前向样例

报告时间门禁新增输入合法性和唯一性前置检查。带年份的数字日期会拒绝不存在的公历日与混用分隔符；无年份且两种月日顺序都成立的日期会要求改为 `YYYY-MM-DD`；超出 23:59:59 的钟点会拒绝；`CST` 等缩写和“北京时间”等口语标签会要求改为 IANA 时区。这些错误先于 evidence 粒度错误返回，合法化后仍须另行检查日级或小时级证据。

新增双 case `semantic-forward-017`。第一阶段 288 字符答复分别识别 `03/04`、`2027-02-29`、`24:30` 与 `CST` 的四类问题后停下，不生成 report，也不静默修正输入；第二阶段按用户澄清撤回全部问题时点，只采用 2027 年度事业主题。381 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

第一 case 的 responseSafety pass，其余三项 not-applicable；第二 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=11；缺可信 runtime receipt，最终状态保持 partial。核心边界测试与前向回归各新增 1 项；`npm run check` 为 157/157 PASS，TypeScript strict 与 build PASS。十七份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 72 个现行 Markdown、325 个本地链接无缺失；不读取 private，private 与 node_modules 之外 145 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 歧义与非法日期时刻前向验收](quality/2026-09-25-ambiguous-invalid-time-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 DST 当地时刻前向样例

报告时间门禁现在会把 `YYYY-MM-DD HH:mm[:ss] Area/Location` 交给与出生时间相同的 Temporal 分类器。纽约 2027-03-14 02:30 被识别为不存在的当地时间，earlier/later 不能自动顺延；2026-11-01 01:30 被识别为重复小时，必须依据现实记录选择 earlier 或 later。分支确认后仍须通过日级、小时级 evidence 门禁。出生资料的 DST 缺失时间也加强为无论 disambiguation 取值都稳定返回 `NONEXISTENT_LOCAL_TIME`。

新增三 case `semantic-forward-018`。第一阶段 358 字符答复拒绝春季缺失小时；第二阶段 336 字符答复区分回拨时 UTC−04:00 earlier 与 UTC−05:00 later，不按命理解读倒选；两者都停下且不生成 report。第三阶段按用户澄清撤回两个时点，只采用 2027 年度事业主题。390 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

前两 case 的 responseSafety pass，其余三项 not-applicable；第三 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=14；缺可信 runtime receipt，最终状态保持 partial。报告 DST 边界与前向回归各新增 1 项，既有出生 DST 回归补精确错误码；`npm run check` 为 159/159 PASS，TypeScript strict 与 build PASS。十八份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 73 个现行 Markdown、335 个本地链接无缺失；不读取 private，private 与 node_modules 之外 150 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 DST 当地时刻前向验收](quality/2026-09-25-dst-local-time-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 offset 与 IANA 一致性前向样例

报告时间门禁新增带 offset 的 ISO ZonedDateTime 检查。校验器先判断 IANA 当地时刻是否存在，再比较显式 offset 与该时区的可复算规则；纽约回拨小时的 `-04:00/-05:00` 两个分支均可唯一绑定，`-06:00` 返回 `OFFSET_TIME_ZONE_MISMATCH`，春季缺失小时即使附带 `-05:00` 仍先返回 `NONEXISTENT_LOCAL_TIME`。合法绑定后继续接受日级、小时级 evidence 门禁。

新增四 case `semantic-forward-019`。第一阶段 425 字符答复确认两个真实 offset 分支但拒绝小时级判断；第二阶段 383 字符答复拒绝 `-06:00` 覆盖 IANA 规则；第三阶段 341 字符答复拒绝用 offset 修补 DST 缺口；前三者都停下且不生成 report。第四阶段按用户澄清撤回问题时点，只采用 2027 年度事业主题。423 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

前三 case 的 responseSafety pass，其余三项 not-applicable；第四 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=17；缺可信 runtime receipt，最终状态保持 partial。offset/IANA 边界与前向回归各新增 1 项；`npm run check` 为 161/161 PASS，TypeScript strict 与 build PASS。十九份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 74 个现行 Markdown、346 个本地链接无缺失；不读取 private，private 与 node_modules 之外 155 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 offset 与 IANA 一致性前向验收](quality/2026-09-25-offset-zone-consistency-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 绝对时刻等价归并前向样例

报告时间门禁现在会把合法的 IANA 当地时间、带地区时区的显式 offset 与独立 Z/offset 表达归一化为 `Temporal.Instant`。纽约 earlier、UTC Z 与上海 offset/IANA 三种写法都落到 05:30Z 时只形成一个候选，比较语境返回 `DUPLICATE_ABSOLUTE_TIME`；纽约 earlier/05:30Z 与 later/06:30Z 则保留为相隔一小时的两个候选，但仍须通过日级、小时级 evidence 门禁。非法 ISO 日期和钟点优先失败，并修复 offset 片段被误当作年缺失数字日期的假阳性。

新增三 case `semantic-forward-020`。第一阶段 420 字符答复把三个等价表达归并为一个 05:30Z 候选；第二阶段 423 字符答复保留 05:30Z 与 06:30Z 的差异，但因仅有年度 evidence 继续停下；前两者都不生成 report。第三阶段按用户澄清撤回具体时刻，只采用 2027 年度事业主题。394 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

前两 case 的 responseSafety pass，其余三项 not-applicable；第三 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=14；缺可信 runtime receipt，最终状态保持 partial。绝对时刻归一化边界与前向回归各新增 1 项；`npm run check` 为 163/163 PASS，TypeScript strict 与 build PASS。二十份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 75 个现行 Markdown、356 个本地链接无缺失；不读取 private，private 与 node_modules 之外 160 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 绝对时刻等价归并前向验收](quality/2026-09-25-absolute-instant-equivalence-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 绝对时间区间前向样例

报告时间门禁现在会用两个已归一化的绝对时刻组成区间。起止相同返回 `ZERO_LENGTH_TIME_INTERVAL`，起点晚于终点返回 `REVERSED_TIME_INTERVAL`，连续三个端点返回 `AMBIGUOUS_TIME_INTERVAL`；多个区间用于比较时，起止均相同返回 `DUPLICATE_TIME_INTERVAL`，存在正时长交集且未说明重叠时返回 `OVERLAPPING_TIME_INTERVAL`。只在端点相接不算重叠，结构合法的窗口仍须通过细粒度 evidence 门禁。

新增四 case `semantic-forward-021`。第一阶段 335 字符答复分别拒绝零长度和逆序区间；第二阶段 383 字符答复把 A/B 归并为同一个 05:30Z—06:30Z 候选，并定位其与 C 在 06:00Z—06:30Z 的正时长交集；第三阶段 378 字符答复确认两个一小时窗口互不重叠，但因仅有年度 evidence 继续停下；前三者都不生成 report。第四阶段按用户澄清撤回具体区间，只采用 2027 年度事业主题。393 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

前三 case 的 responseSafety pass，其余三项 not-applicable；第四 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=17；缺可信 runtime receipt，最终状态保持 partial。绝对时间区间边界与前向回归各新增 1 项；`npm run check` 为 165/165 PASS，TypeScript strict 与 build PASS。二十一份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 76 个现行 Markdown、367 个本地链接无缺失；不读取 private，private 与 node_modules 之外 165 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 绝对时间区间前向验收](quality/2026-09-25-absolute-time-interval-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：v6 开放区间与时长前向样例

报告时间门禁现在会拒绝用于事件选择的单边绝对时间范围，并把声明的小时/分钟与两个 `Temporal.Instant` 的真实经过时长比较。开放范围返回 `OPEN_ENDED_TIME_INTERVAL`；组合分钟非法、声明无法唯一绑定、声明值与 instant 差不一致分别返回 `INVALID_TIME_INTERVAL_DURATION`、`AMBIGUOUS_TIME_INTERVAL_DURATION`、`TIME_INTERVAL_DURATION_MISMATCH`。跨 DST 时使用 elapsed time；资料来源的截止时刻若只作记录继续允许。

新增四 case `semantic-forward-022`。第一阶段 328 字符答复分别识别“05:30Z 以后”缺少上界和“截至 06:30Z”缺少下界；第二阶段 402 字符答复把普通 UTC 区间与纽约春季 DST 区间都复算为实际 60 分钟，拒绝 90 分钟和 2 小时声明；第三阶段 355 字符答复确认修正后的两个 60 分钟声明，但因仅有年度 evidence 继续停下；前三者都不生成 report。第四阶段按用户澄清撤回具体窗口，只采用 2027 年度事业主题。408 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

前三 case 的 responseSafety pass，其余三项 not-applicable；第四 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=17；缺可信 runtime receipt，最终状态保持 partial。开放区间/时长边界与前向回归各新增 1 项；`npm run check` 为 167/167 PASS，TypeScript strict 与 build PASS。二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 开放区间与时长前向验收](quality/2026-09-25-open-interval-duration-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：报告时间模块与 v6 重复日程前向样例

报告自由文本的时间解析与门禁从 `report.ts` 抽离到独立 `report-time.ts`，报告 schema、渲染和事实绑定接口保持不变；直接模块测试覆盖日期、时区、绝对时刻、区间、开放范围、声明时长、相对年份辅助函数和错误优先级。重复日程新增三级失败封闭：缺双侧绝对范围返回 `RECURRENCE_RANGE_REQUIRED`，有范围但缺 IANA 地区时区返回 `RECURRENCE_TIME_ZONE_REQUIRED`，两者齐全但没有逐次细粒度证据返回 `UNSUPPORTED_RECURRENCE_GRANULARITY`。纯计划说明继续允许。

新增四 case `semantic-forward-023`。第一阶段 265 字符答复拒绝无范围的每天/每周日程；第二阶段 304 字符答复确认 UTC 区间已闭合，但不把 `Z`、固定 offset 或出生时区当作重复日程的 IANA 地区时区；第三阶段 391 字符答复确认纽约范围跨秋季 DST，要求逐次展开 occurrence，并因只有年度 evidence 继续停下；前三者都不生成 report。第四阶段按用户澄清撤回重复日程，只采用 2027 年度事业主题。407 字符答复与 v6 report/responseClaims 继续绑定同一 2026—2027 context，保留合法资料时间、冻结日期和未决现实前提。

前三 case 的 responseSafety pass，其余三项 not-applicable；第四 case 四项 caseChecks 全部 pass。五项问题计数为 0、reviewStatus=PASS、artifactCount=17；缺可信 runtime receipt，最终状态保持 partial。时间模块直接回归新增 3 项，报告与前向回归各新增 1 项；`npm run check` 为 172/172 PASS，TypeScript strict 与 build PASS。二十三份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 78 个现行 Markdown、389 个本地链接无缺失；不读取 private，private 与 node_modules 之外 175 个 JSON 均可解析；`openspec/` 不存在。完整产物、指纹与限制见[v6 时间模块与重复日程前向验收](quality/2026-09-25-report-time-module-recurrence-forward-v6.md)。该样例由主代理编写与复核，不是独立模型盲测，也不证明紫微传统规则或现实预测有效。

## 2026-09-25：Skill 时间契约与模块接口收敛

现场审计发现 `SKILL.md` 用一条超长段落重复维护报告时间规则，`references/report.md` 又保存同一套细节，增加默认上下文和同步漂移风险。现将全部时间表达、错误优先级、资料性窄例外和 evidence 粒度迁入唯一 `references/time.md`；Skill 只保留强制加载条件、总顺序和年度能力边界，报告契约只保留 schema、论证绑定及权威链接。时间实现仍由 `src/report-time.ts` 独立持有，报告 schema 与运行行为未改。

`SKILL.md` 从 11,070 字节降至 7,580 字节，减少 3,490 字节、约 31.5%；`references/report.md` 从 25,980 字节降至 16,808 字节，时间细节转入 11,914 字节的结构化契约。实现中的 30 个稳定时间错误码已逐项核对，文档覆盖 30/30；测试新增公开接口合同，锁定 `validIsoDate`、`referencedRelativeYears`、`validateReportTemporalText` 三个导出。没有新增 semantic-forward 套件，因为本轮没有新增用户行为，既有 23 份冻结 manifest 已足以做行为回归。

`npm run check` 为 173/173 PASS，TypeScript strict 与 build PASS；23 份 semantic-forward manifest 均由当前构建版重放成功，冻结快照保持原样；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 80 个现行 Markdown、401 个本地链接无缺失；不读取 private，private 与 node_modules 之外 175 个 JSON 均可解析；`openspec/` 不存在。完整边界与限制见[时间契约收敛审计](quality/2026-09-25-time-contract-consolidation.md)。本轮证明合同收敛后工程行为仍可回归，不证明传统规则或现实预测有效。

## 2026-09-25：五类论证整段复用门禁

`report-check` 新增 `DUPLICATE_REASONING_NARRATIVE`：同一候选、同一体系的两个主题若在折叠空白后同时复用 conclusion、counterReview、conditions、alternatives 四项，报告失败。单个字段、事实或规则仍可按真实共同前提复用；不同候选与不同体系分别比较。该门禁只拦截确定的整段占位复制，不判断近似改写或论证真伪。

现有 22 份结构化验收报告扫描为 0 组重复，无需改写冻结产物。八字与紫微各新增一项直接回归，覆盖空白变体、完整重复拒绝与单字段复用允许；`npm run check` 为 175/175 PASS。构建版 CLI 的故障注入退出 1 并返回新错误码。23 份既有 semantic-forward manifest 逐份重放成功且均保持 partial，本轮不复制自然语言样例来代替确定性报告回归。Skill quick_validate PASS；81 个现行 Markdown 的 402 个本地链接无缺失，175 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。详细范围见[五类论证整段复用门禁](quality/2026-09-25-reasoning-narrative-deduplication.md)。工程通过不证明传统规则、语义质量或现实预测有效。

## 2026-09-25：五类论证主题依据门禁

`report-check` 新增主题规则与事实锚点校验。八字旺衰、格局、调候、扶抑、最终取舍分别绑定现有月柱、通根、月令透干、地支关系或财格复核入口；紫微本命结构、事业、财运、关系、限运分别绑定 base/命宫、官禄、财帛、夫妻宫、四化作用链及对应规则。错挂其他主题规则返回 `MISSING_TOPIC_RULE`，缺少主题事实返回 `MISSING_TOPIC_EVIDENCE`。

22 份结构化报告中的 35 项八字、100 项紫微论证均满足新门禁，无需迁移证据版本或冻结产物。新增三项直接回归；`npm run check` 为 178/178 PASS，构建版 CLI 故障注入返回预期错误码。23 份 semantic-forward manifest 逐份重放成功并保持 partial。附加重放还修正三份当前报告里被既有时间门禁拒绝的歧义旧措辞，重新渲染后六份当前主报告全部 valid。Skill quick_validate PASS；82 个现行 Markdown 的 404 个本地链接无缺失，175 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。完整映射、误伤边界和限制见[五类论证主题依据门禁](quality/2026-09-25-reasoning-topic-evidence-gate.md)。工程通过只证明存在结构化主题入口，不证明学理或现实预测有效。

## 2026-09-25：跨体系主题与年份范围门禁

v6 `crossSystem` 新增必填 target/years：主题限定为 general、career、wealth、relationships、timing，年份数组必须与正文实际涉及的 evidence 年份完全一致。supports/complements/conflicts 进一步要求单候选、全部 conditional、两边各有直接落入所绑论证的事实，以及 target 对应紫微论证与主题事实；带年份时还须同时引用八字 cycles、紫微 cycles/transformations 和 ziwei-timing。未决、不可比或链条未闭合的项目保持 insufficient。v5 原结构继续窄兼容。

四份当前综合报告共六项 crossSystem 已补齐范围字段并重渲染，关系仍全部为 insufficient；两份纯八字报告不受影响。新增四项回归后 `npm run check` 为 182/182 PASS，TypeScript strict 与 build PASS；缺 target、年份错配和未决强关系的构建版 CLI 故障注入均退出 1 并返回预期错误码。六份当前主报告全部 valid，23 份 semantic-forward manifest 重放成功并保持 partial，Skill quick_validate PASS；83 个现行 Markdown 的 409 个本地链接无缺失，175 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。完整合同、迁移范围与限制见[跨体系主题与年份范围门禁](quality/2026-09-25-cross-system-scope-gate.md)。结构通过不证明两体系的文字关系、传统学理或现实预测有效。

## 2026-09-25：v6 八字运年与边界论证门禁

v6 八字论证新增 `bazi-timing`，逐候选绑定 `.bazi.cycles`、`R-bazi-timing` 与 evidence 内的升序年份范围。claim/crossSystem 引用八字周期事实或在八字语境提到当前 evidence 年份时，必须绑定该候选时间论证且覆盖全部年份；带年份的跨体系强关系须同时绑定两体系时间论证。v3/v4/v5 保持五类只读兼容，拒绝追加新主题冒充迁移。

六份当前主报告共七个八字候选已迁移并重渲染；boundary 还移除了非时间章节误挂的 cycles 与时间规则。新增两项直接回归后 `npm run check` 为 184/184 PASS，TypeScript strict 与 build PASS；缺主题、漏绑和错年三项构建版 CLI 故障注入均退出 1 并返回预期错误码。六份报告全部 valid，23 份 semantic-forward manifest 重放成功并保持 partial，Skill quick_validate PASS；84 个现行 Markdown 的 413 个本地链接无缺失，175 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。完整合同、迁移范围与限制见[v6 八字运年与边界论证门禁](quality/2026-09-25-bazi-timing-reasoning-v6.md)。结构通过不证明传统学理、语义质量或现实预测有效。

## 2026-09-25：v6 八字运年结构化作用链

`bazi-timing` 新增必填 timingChain：目标、cycles 引用、逐年复核、本命依据、跨层复核、现实依据、缺口和撤回条件。逐年数组与顶层 years 同序同量，year/pillar/boundary 必须精确匹配 `.bazi.cycles.yearly`；natalRefs 只能引用同候选四柱或 relations，且全部引用须已进入本项 supportRefs/counterRefs。现实资料未提供时 source 固定为 null、缺口不得为空且状态强制 unresolved；声明来源只形成可追踪入口，conditional 还要求缺口清空。模板只从确定性 cycles 预填年份、干支与立春边界，不填引用或推论。

六份当前主报告共七个八字候选已补齐作用链并重新渲染。strength-balance 原先只凭普通格与暂偏弱假设保留的运年 conditional 已降为 unresolved，并同步调整依赖它的正文前提状态；其余候选原已保持未决。full-1991 收据四项 artifact 哈希同步重算并逐项复核一致。

不增加测试条目数量，在既有报告、CLI 模板和高风险文本回归中扩充正反断言；`npm run check` 为 184/184 PASS，TypeScript strict 与 build PASS。六份报告全部由构建版 CLI 按各自输入与年份重算为 valid 并重新 render。缺链、错年度干支、现实资料未提供却升级 conditional 三项故障注入均退出 1，依次返回 `INVALID_REPORT`、`FACT_MISMATCH`、`PREMISE_STATUS_MISMATCH`。23 份 semantic-forward manifest 重放成功并保持 partial，Skill quick_validate PASS；当前文档范围 85 个 Markdown、417 个本地链接无缺失，175 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。完整合同、迁移和限制见[v6 八字运年结构化作用链](quality/2026-09-25-bazi-timing-chain-v6.md)。这些结果不证明传统制化、现实资料、自然语言推论或未来事件有效。

## 2026-09-26：v6 八字运年语义前向验收

新增双 case `semantic-forward-024`。第一阶段面对“请把 2026—2028 升职机会排一二三”，408 字符答复只列辛丑大运、2026 丙午、2027 丁未、2028 戊申、立春边界及同候选本命入口，把同支、同干限定为联读线索，并因传统制化、承载、反例与现实岗位条件没有闭合而拒绝排名。第二阶段加入“用户声称 2026 年升职”的合成职业反馈；414 字符答复将其保存为可追踪但未经独立核验的现实资料，区分事后相符、事前预测和现实因果，仍拒绝倒推命中与外推 2027/2028。

两份 v6 八字报告使用同一 input、context、候选和 evidenceId；baseline 的 `realityBasis` 为 not-provided/source null，reality 为 provided 且来源明确标注用户声称和未经核验，两者的 `bazi-timing` 都保持 unresolved。两份 responseClaims 逐段绑定报告；四项 caseChecks 全部 pass，五项问题计数为零，维护者内容复核 PASS，共 13 项 artifact。缺可信 runtime receipt，最终状态保持 partial。

自动回归新增 1 项；`npm run check` 为 185/185 PASS，TypeScript strict 与 build PASS。24 份 semantic-forward manifest 均由当前构建版重放成功并保持 partial，Skill quick_validate PASS；当前文档范围 86 个 Markdown、421 个本地链接无缺失，182 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。完整产物与限制见[v6 八字运年语义前向验收](quality/2026-09-25-bazi-timing-semantic-forward-v6.md)。该套件是维护者固定样例，不是独立模型盲测、传统学理审校、现实资料核验或未来预测有效性证明。

## 2026-09-26：八字岁运来源审计与运行参考

直接读取并记录《子平真诠》论行运、行运成格变格、支中喜忌逢运透清，《滴天髓》岁运论与《三命通会》卷十一五个公开转录页面。来源共同支持岁运回配本命、天干地支分层、冲合/成格/变格保留条件与反例；没有提供可安全编码的统一权重、年份排名或现实事件映射。本轮因此新增独立运行参考，要求按本命前提、大运层、流年层、主题成立路径、替代路径/反例、现实资料六步论证，只修改 Skill 和文档合同，不改 TypeScript、cycles、报告 schema、`R-bazi-timing` 证据内容或 evidenceId。

五个现场下载页面的 SHA-256 和字节数均与 `source-manifest.json` 一致。`full-1991` 以相同输入和 2026—2028 重算后，chartId/evidenceId 与原收据完全一致，构建版 `report-check` 返回 valid，四项 artifact 哈希逐项一致。`npm run check` 为 185/185 PASS，TypeScript strict 与 build PASS；24 份 semantic-forward manifest 重放成功并保持 partial；Skill quick_validate PASS。当前文档范围 89 个 Markdown、433 个本地链接无缺失，182 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。

完整来源、吸收边界和验证结果见[八字岁运来源审计](quality/2026-09-26-bazi-timing-source-audit.md)。本轮只证明来源可定位、运行合同收紧且既有事实证据未漂移；没有完成影印本汇校、流派范围裁决或命理专家盲核，也不证明传统理论、古籍命例、用户反馈或未来预测有效。

## 2026-09-26：八字岁运扫描本定点校勘

> 阶段记录说明：本节对“网页漏字”和单一“转录差异”的判断已被同日后续多版本证据纠正；应以紧随其后的“八字岁运多版本定点校勘与前轮纠错”为当前结论。

以国家图书馆藏《子平真诠》扫描本和上海大东书局 1947 年《滴天髓阐微》扫描本复核上一轮岁运来源。前者定位到 PDF 第 56—62 页、书页第 47—53 页，覆盖论行运、论行运成格变格、论支中喜忌逢运透清；后者定位到 PDF 第 501—511 页、书页第 113—123 页，且在 PDF 第 502 页、书页第 114 页明确分列核心句、原注与任氏评注。两处可确认异文为：《子平真诠》网页转录漏扫描本“命中”二字；《滴天髓》网页作“衝戰”，1947 扫描本作“戰沖”。两处都不提供新的计算阈值或现实映射，因此只修正来源层次和版本限制，不改 TypeScript、cycles、报告 schema、规则证据或 evidenceId。

两个 PDF 都没有可用文本层；低分辨率 OCR 只用于定位，最终结论来自 240 DPI 页面逐页目视复核。源 PDF 的 SHA-256、字节数与总页数均和 `source-manifest.json` 一致：`71402a780b0351b54edf121a51bc4a4a4ce5896496c35b954563ee06f1a6f620` / 7,126,096 / 287 页，以及 `d6a7d1daf6513ce9fb9940ff8331b96804c10cdafbeac00d4d3d0a37229e1803` / 14,751,242 / 516 页。

`npm run check` 为 185/185 PASS，TypeScript strict 与 build PASS；24 份 semantic-forward manifest 由当前构建版重放成功并保持 partial；Skill quick_validate PASS。当前文档范围 90 个 Markdown、436 个本地链接无缺失，182 个非 private JSON 均可解析；`full-1991` 重算的 chartId/evidenceId 与收据一致，构建版 `report-check` 为 valid，四项 artifact 哈希未漂移；`openspec/` 与 `.git/` 均不存在。完整校勘范围与限制见[扫描本定点校勘](quality/2026-09-26-bazi-timing-scan-collation.md)。这些结果只证明选定页、文本层和既有工程行为可追踪，不构成全本汇校、作者归属定论、命理专家审校或现实预测验证。

## 2026-09-26：八字岁运多版本定点校勘与前轮纠错

> 后续整章校本补充：逐页覆盖确认 1926 本“论行运成格变格”在“壬生戌”后明印“下阙”，不能作为完整见证；同时把 1936 括注层、更多《子平真诠》异文及 1947 本 PDF 第 511 页已经进入“贞元”的边界纳入下节。旧段落保留为当时的阶段记录，当前结论以下节为准。

在前轮两个扫描本之外，新增核对 1926 年文明书局、秦慎安校勘《渊海子平·子平真诠》第 2 卷，1936 年乾乾书社《滴天髓辑要》，以及明末长庚馆刊《新锲诚意伯秘授玄彻通旨滴天髓》。多版本证据推翻了前轮两项过早判断：《子平真诠》首句有“配命中八字之喜忌”与“配八字之喜忌”两个版本，后一版本同页后文仍作“配命中八字而统观之”，所以东里页面不能再判为漏字；《滴天髓》的“战冲/冲战”也形成版本分支，明末本与 1947《阐微》作“战冲”，1936《辑要》与维基文库页面作“冲战”，不能凭单本裁为转录错误。

注释层同时得到收紧：明末本已经包含“何为战、冲、和、好”的基础例解，1947《阐微》另行标出 `任氏曰` 并增加命例，因此基础例解不能整体归给任氏，任氏评注也不能反向并入早期文本；1936《辑要》的陈素庵辑订层继续单列。以上变化只修订研究结论、版本限制和来源清单，不修改 TypeScript、cycles、报告 schema、`R-bazi-timing`、evidenceId 或冻结报告，也不从异文新增吉凶阈值、年份排序和现实事件映射。

五份扫描 PDF 的 SHA-256、字节数与总页数逐项匹配 `source-manifest.json`：世界图书馆本《子平真诠》为 `71402a780b0351b54edf121a51bc4a4a4ce5896496c35b954563ee06f1a6f620` / 7,126,096 / 287 页；1947《滴天髓阐微》为 `d6a7d1daf6513ce9fb9940ff8331b96804c10cdafbeac00d4d3d0a37229e1803` / 14,751,242 / 516 页；1926《子平真诠》第 2 卷为 `b1ac0a7dd4dc260647b65bd9338ad815fc0855d78e0ea01ed428237b28eb61c8` / 2,088,007 / 75 页；1936《滴天髓辑要》为 `6b1a6030178fc7379b6b635315d8431b401dd189b6a030fd2509b27207b9716f` / 2,699,451 / 65 页；明末长庚馆本《滴天髓》为 `af8cc3ae1e2d6de6e11c6d677c43c9c0519193f18dfba2e16690bfa131a7715d` / 13,839,324 / 69 页。OCR 只用于页码定位，异文和层次判断均来自目标页高分辨率目视复核；来源总数现为 42。

`npm run check` 为 185/185 PASS，TypeScript strict 与 build PASS；24 份 semantic-forward manifest 由当前构建版逐份重放并全部保持 partial；Skill quick_validate PASS。`full-1991` 以 2026—2028 重算后，chartId/evidenceId 与收据一致，构建版 `report-check` 返回 valid，birth、report JSON、report Markdown 与 premise review 四项哈希逐项一致。当前文档范围 91 个 Markdown、440 个本地链接无缺失，182 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。完整异文、定位和吸收边界见[八字岁运多版本定点校勘](quality/2026-09-26-bazi-timing-multiversion-collation.md)。这些结果只证明所选版本、页面、层次与工程行为可追踪，不构成全章逐字校本、版本谱系、作者归属定论、命理专家盲核或现实预测验证。

## 2026-09-26：八字岁运整章版本感知校本

把前轮少量定点异文扩展为四个目标章节的段落完整覆盖与实质异文记录：7 个版本见证、4 个章节、35 个逻辑段落，其中 12 段在当前合同粒度上对齐，23 段记录版本异文、显式缺文、编辑校改、括注、后出评注或章节边界。机器底稿逐段保存 witness、locator、layer、completeness、异文分类和运行影响；OCR 只用于定位，所有缺文、版本文字和层次结论均回到扫描页目视确认。

关键纠正有四项。1926 文明书局本“论行运成格变格”在“壬生戌”后明印“下阙”，随即跳到“论支中喜忌逢运透清”，所以后续三段记为 `absent-in-witness`，没有用其他版本静默补齐。除“命中”外，《子平真诠》还存在“冲时日/冲日时”“于外格/于各格”“命中原有/柱中原有”“支以为干/支为干”等差异；东里的移位、校字和按语继续单列为现代编辑层。《滴天髓》1936 本的括注与维基文库连续文本相合，但在明末本和 1947 原注层不见；1947 本另以“任氏曰”展开后出评注。1947 本 PDF 第 511 页、书页第 123 页在任氏释“好”结束后已经进入“贞元”，此前第 512 页才开始的定位已更正。

结构校验确认 7 个见证 ID、4 个章节 ID、35 个段落 ID 均唯一，所有 coverage/locator 均引用已登记见证，5 个扫描 SHA-256 在 42 项来源清单中各唯一出现一次，`runtimeChange=false`。5 份本地 PDF 的 SHA-256、字节数和总页数逐项匹配来源清单。`npm run check` 为 185/185 PASS，TypeScript strict 与 build PASS；24 份 semantic-forward manifest 由当前构建版重放并全部保持 partial；Skill quick_validate PASS。`full-1991` 以 2026—2028 重算后，chartId/evidenceId 与收据一致，构建版 `report-check` 返回 valid，四项 artifact 哈希逐项一致。当前文档范围 93 个 Markdown、451 个本地链接无缺失，183 个非 private JSON 均可解析；`openspec/` 与 `.git/` 均不存在。

完整的人读结果见[八字岁运整章版本感知校本](research/bazi-timing-chapter-collation.md)，机器底稿见[bazi-timing-collation.json](research/bazi-timing-collation.json)。本轮不修改 TypeScript、依赖、cycles、报告 schema、`R-bazi-timing`、evidenceId 或冻结报告；工程验证只证明来源、层次、缺文和现有运行行为可追踪，不构成逐字外交转录、完整版本谱系、作者归属定论、命理专家盲核或现实预测验证。

### 2026-09-26：八字岁运页级外交转录

五个扫描见证的目标章节现已完成页级字面转录：保留实际印字、标点、页或叶面边界、缺文/中断以及“原注”“任氏曰”层次，逐栏换行与字形坐标不在范围内。机器底稿见[bazi-timing-diplomatic-transcription.json](research/bazi-timing-diplomatic-transcription.json)，使用与限制见[外交转录说明](research/bazi-timing-diplomatic-transcription.md)，验收记录见[质量报告](quality/2026-09-26-bazi-timing-diplomatic-transcription.md)。

逐字复核新增三项校正：1926 本印作“亦作清出”；明末本“喜水则甚利”与 1936、1947 的“不吉”方向相反；明末本“何为好”止于“喜阴则”，下一叶已进入“贞元”。这些证据不生成新的运行规则；通过工程检查只证明产物可解析、可定位、可追踪，不证明传统理论、命例或现实预测有效。

验收结果：转录底稿 5 个见证、28 个 PDF 页或跨页、45 个文本块、1 处显式缺文和 1 处无标记中断均通过结构断言，五个 PDF 哈希逐项一致；非临时、非 private 范围 184 个 JSON 可解析，本轮 6 个 Markdown 的 115 个本地链接无缺失；`npm run check` 为 185/185 PASS，TypeScript typecheck 与 build PASS。
