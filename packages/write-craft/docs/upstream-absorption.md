# Upstream absorption

Write Craft is a fusion layer, not an automatic mirror. Upstream files remain
unchanged under `upstreams/`; reviewed behavior is independently expressed in
the installable Skill. A source is not considered absorbed merely because its
repository is pinned.

| Source | Decision | Current local use | Deliberately not adopted |
| --- | --- | --- | --- |
| Anthropic `doc-coauthoring` | Partial, independent re-expression | Context-aware drafting and fresh-reader testing | Mandatory opt-in, 5–10 questions by default, section-by-section ceremony, host-specific artifact commands |
| Anthropic `internal-comms` | Reference only | Future format vocabulary | Weekly updates, newsletters, and incident templates in the current trigger surface |
| `writing-clearly-and-concisely` | Partial, principles only | One topic per paragraph, concrete language, remove waste | English punctuation and grammar rules, universal active-voice enforcement, mandatory subagent copyedit |
| Composio `content-research-writer` | Reference only | Future public-article research review | Hook optimization, publishing checklist, invented example citations, and broad blog routing |
| Arjun `plain-language` | Selective absorption | Preserve truth while translating jargon and the reader's path | English-specific sentence examples as reusable copy |

## Local behavior map

- `SKILL.md` owns scenario routing and the rules shared by every scenario: task
  modes, editing-authority principle, evidence boundaries, question policy,
  delivery order, and reference loading.
- `references/decision-documents.md` is the default scenario reference: its
  commitments, reading order, reader versions, decision framing, information
  layering, usage-scenario use, and decision-relevant technical constraints.
- `references/clear-chinese.md` owns Chinese expression, terminology, precision,
  and naturalness.
- `references/document-presentation.md` owns platform-neutral visual hierarchy,
  semantic emphasis, and rendered-document verification; platform writes stay
  outside Write Craft.
- `references/source-integrity.md` owns faithful explanation, two-way coverage,
  relevant unknowns, and unresolved source conflicts.
- `references/reader-testing.md` owns the review order, the shared revision
  budget, fresh-context acceptance, and fallback.
- `references/readme.md` is the README scenario reference.
- `references/source-map.md` records provenance and rejected behaviors for the
  installed product without requiring upstream files at runtime.
- `scripts/validate.py` checks source and immutable historical evidence;
  `scripts/release_check.py` separately binds a release candidate to current
  behavior evidence.
- `scripts/eval_contracts.py` owns the shared deterministic source, digest, and
  status primitives. `scripts/eval_behavior.py` owns the v2 compatibility
  adapter, v3 evaluation flow, fact review, and optional blind-reader review.
  `scripts/eval_structured_output.ts` gives those isolated review stages three
  schema-bound terminating submission tools; Python still enforces the
  case-specific contracts after extraction. These are development tools, not
  installed Skill requirements.
- `evals/release-policy.json` fixes the current release evidence contract;
  changing the policy is a reviewed product decision, not a way to waive a
  failing candidate.

## Update policy

`scripts/upstream_status.py --remote --json` may report remote drift, but it
never updates a pin. A future update must review the exact commit range, revise
this matrix and the lock together, and rerun source, package, and behavioral
validation.

## ljg-skills：写作质量整改的参考评审

评审日期：2026-09-26。来源：[lijigang/ljg-skills](https://github.com/lijigang/ljg-skills)，
固定版本：`fdea0bea5133246de418d19015f65eeb18699623`（master）。
这是已阅读的外部参考及拟吸收方案，不是已经完成的运行时改造或效果验证。
未新增 upstream checkout、安装依赖或修改 `upstreams.lock.json`；该 lock 仍管理
现有本地上游检出。本节固定链接用于复核这次非 vendored 来源评审。

### 已读范围与许可

- [ljg-writes/SKILL.md](https://github.com/lijigang/ljg-skills/blob/fdea0bea5133246de418d19015f65eeb18699623/skills/ljg-writes/SKILL.md)，文件声明版本 8.0.1。
- [ljg-writes/Workflows/WriteEssay.md](https://github.com/lijigang/ljg-skills/blob/fdea0bea5133246de418d19015f65eeb18699623/skills/ljg-writes/Workflows/WriteEssay.md)。
- [ljg-plain/SKILL.md](https://github.com/lijigang/ljg-skills/blob/fdea0bea5133246de418d19015f65eeb18699623/skills/ljg-plain/SKILL.md)，文件声明版本 5.0.0。
- [ljg-paper/SKILL.md](https://github.com/lijigang/ljg-skills/blob/fdea0bea5133246de418d19015f65eeb18699623/skills/ljg-paper/SKILL.md) 与 [ReadingGuide.md](https://github.com/lijigang/ljg-skills/blob/fdea0bea5133246de418d19015f65eeb18699623/skills/ljg-paper/ReadingGuide.md)。只评审解释方法与阅读检查，不评审其模板、脚本和宿主集成。
- 仓库根 [LICENSE](https://github.com/lijigang/ljg-skills/blob/fdea0bea5133246de418d19015f65eeb18699623/LICENSE) 为 MIT，Copyright (c) 2026 lijigang。
  本次只记录独立概括的分析，不复制上游正文、模板或代码。如后续复制或实质改编，
  须按实际使用路径复核许可并保留版权及许可声明，更新第三方 notices。

### 选择性吸收，而非合并 Skill

| 来源方法 | 对应的本地问题 | 拟落点与边界 |
| --- | --- | --- |
| ljg-writes：先核对内容，再连续通读修改中文；换词无效时重组整句或整段 | 事实核对较细，语言编辑缺少统一执行步骤 | `clear-chinese.md` 定义编辑动作，入口负责调用；不另加固定 Agent 或额外模型调用 |
| ljg-writes：检查搭配、指代、条件、句间与段间联系 | 只删重复词，不能解决重复意思、跳跃或拗口 | 检查每段的信息作用和前后联系；已有自然表达保留，不用短句数、连接词数作机械门槛 |
| ljg-writes：分析流程不充当文章目录，结尾在问题回答后停止 | 成稿混入作者核查说明、过程标签和重复收束 | 修现有完整示范；内部审查语言不进入 clean 正文，实质性证据边界仍保留 |
| ljg-paper：具体对象与动作持续承担解释，案例之后不退回术语堆叠 | 开头场景易懂，但后文仍可能需要读者自行翻译 | `decision-documents.md` 用同一受来源支持的对象贯穿必要解释；新案例必须增加信息，不虚构业务事实 |
| ljg-paper：章节可递进也可并列，补充材料按新增信息取舍 | 重复与有用重申容易混淆，容易为了连贯补造因果 | 检查新增事实、条件、比较或独立阅读作用；不要求所有段落不可换序，不把并列强写成因果 |
| ljg-paper：能复述不等于读得轻松；阅读检查指出回读、缺背景与补推理的位置 | PASS 容易掩盖编辑成本与实际阅读困难 | `reader-testing.md` 和评测记录区分准确性、理解与编辑缺陷；模型结果不替代真人反馈 |
| ljg-plain：删除无用铺垫、解释具体动作、检查中文搭配 | 空泛表达与翻译腔 | 只作为补充参考；冲突处采用更符合业务文档的读者与用途判断 |

这些方法与现有部分原则重合，实施时应替换、合并薄弱指导和示范，不能再堆一份
重复清单。最值得吸收的是编辑动作和判断方法，而非某位作者的固定语气。

### 明确不采用

- 不引入默认 1000–1500 字、Org/Denote、固定保存目录、作者署名、ASCII-only、
  Emacs 或宿主工具要求；输出服从用户与目标平台。
- 不把业务提案改造成观点文章，不强制安排旧解释失败、反例、认知反转或迁移故事。
  机制和案例只能解释来源支持的关系；不能以补足论证为由改变已批准方案。
- 不采用 ljg-plain 的统一十二岁读者、强制口语/短词/短句、正文无子标题和句式配额。
  术语、书面语、长句和连接词是否保留，取决于准确性与阅读任务。
- 不采用无依据数字化置信度。没有数据或明确估计依据时，不能将不确定性改成百分比。
- 不迁入论文研究台账、个人笔记工作流或无限重试；保留本地有界修订与真实失败记录。

### 落地与验收顺序

1. 先修既有完整示范、clean 输出冲突与相关缺口规则，再把语言编辑移为所有适用
   中文成稿的基础步骤。保持事实、编辑权限、长度和关键条件不变。
2. 在现有评测中记录结构、句子、措辞与呈现的具体缺陷及位置；严重事实错误、
   交付违约、普通编辑问题分开，不新增单一总分掩盖问题。
3. 使用未参与规则调试的完整材料比较修改前后稿，记录剩余手工修改和阅读困难。
   保留必要的术语重现、摘要独立性与验收重申作为正例，避免为去重删掉关键边界。
4. 有行为证据后再更新安装包内 `source-map.md` 的实际吸收状态及必要的 notices。
   阅读过源码或静态验证通过，均不等于写作效果已改善。

当前状态：已独立落实基础中文编辑步骤、示范修订、相关缺口与 clean 交付边界，
并更新运行时来源记录。评测器已增加独立的通用编辑缺陷记录，判断可靠性仍待验证；未见材料对照与真人
验证尚未完成，不能据此宣称写作效果已经改善。

## 金字塔组织与信息贡献改造

本轮进一步把写作组织明确为中心回答、纵向依据、同层分组和逻辑顺序，并加入完整合成决策示范及跨形式删除检查。依据 Minto 的公开概念说明（https://www.barbaraminto.com/concept，2026-09-26）独立编写；未复制书籍或课程文字。ljg 来源固定版本与不采用项保持不变。

实现、细则迁移映射、首稿对照协议与证据层次见 `pyramid-writing-change.md`。此项不是另一份附加万能清单：主入口围绕写作动作组织，特定事实与形式边界迁入必读参考，保持原语义。任何效果判断以当前冻结候选的实际对照为准。

## better-readme：项目 README 场景

评审日期：2026-10-09。来源：[tommy0103/better-readme-skill](https://github.com/tommy0103/better-readme-skill)，
固定版本：`fa3dce198b4b6f798ffc61c6483e7e7aa15b8cde`（main）。仓库根
[LICENSE](https://github.com/tommy0103/better-readme-skill/blob/fa3dce198b4b6f798ffc61c6483e7e7aa15b8cde/LICENSE)
为 MIT，Copyright (c) 2026 tommy0103 and contributors。与 ljg-skills 相同，按非
vendored 来源评审处理：未新增 upstream checkout，未修改 `upstreams.lock.json`。

### 已读范围

- [skills/better-readme/SKILL.md](https://github.com/tommy0103/better-readme-skill/blob/fa3dce198b4b6f798ffc61c6483e7e7aa15b8cde/skills/better-readme/SKILL.md)
- [skills/better-readme/references/art-of-readme.md](https://github.com/tommy0103/better-readme-skill/blob/fa3dce198b4b6f798ffc61c6483e7e7aa15b8cde/skills/better-readme/references/art-of-readme.md)：
  该文件是 noffle《Art of README》的转存全文。原仓库
  `noffle/art-of-readme` 与 `hackergrrl/art-of-readme` 在评审日均已无法访问，
  原文的再使用条款无法核实；better-readme 仓库的 MIT 不能覆盖第三方原文。

### 吸收方式

Write Craft 的定位扩展为多场景写作，README 作为决策文档之外的第二个场景，
规则独立写在 `skills/write-craft/references/readme.md`，入口 `SKILL.md` 只负责场景
分流。共享规则（编辑权限、来源核对、中文表达、clean 交付）继续由现有 reference
负责，不在 README 场景里复制。

| 来源方法 | 本地落点 | 调整 |
| --- | --- | --- |
| 按读者判断是否适用的顺序组织 README，库与应用的安装/API 顺序不同 | `readme.md` 读者顺序 | 不为凑齐顺序补空章节 |
| 维护者内容迁出并留链接、每条事实只写一处、表格承载可扫读细节 | `readme.md` 改写规则 | 与 Write Craft 的“信息只放一处”合并表达 |
| 改仓库文件前检查未提交改动、测试中固定的文案和派生副本 | `readme.md` 仓库检查 | 只在直接改仓库文件时执行；未提交改动视为用户最新素材而非改写基线之外的内容；不采用“以默认分支为准”，以免回滚 feature 分支上的 README 改动；改测试须用户请求包含仓库改动 |
| 沿用旧 README 的说法前对照代码核实 | `readme.md` + `source-integrity.md` | 状态词（已实现、实验、计划、未验证）沿用来源核对规则 |
| 翻译按意思写、结构保持对齐、互相链接、更新锚点 | `readme.md` + `clear-chinese.md` | 默认保留 README 原有语言 |
| 以决策清单汇报改动 | `readme.md` 交付规则，`SKILL.md` 交付节注明例外 | 仅限在仓库中改文件；README 正文仍保持 clean |

### 明确不采用

- 不复制或转存《Art of README》原文；只吸收公开流传的读者漏斗原则。
- 不复制 better-readme 的正文措辞；本地规则独立表达。
- 不把完整 API 参考手册、运维手册或 changelog 纳入 README 场景。

当前状态：规则与路由已落地，新增两条 exploration 评测用例。2026-10-09 在 Pi
`1.0.0` 上以 `anthropic/claude-sonnet-5-5` 生成、`deepseek/deepseek-flash`
（judge thinking medium）评审：35 个 judge 校准 fixture 全部符合预期；4 条 smoke
回归、README 改写与路由用例均 PASS。README 改写用例此前一轮因 CONTRIBUTING 块标签
附带过程说明而 FAIL，收紧 `readme.md` 交付规则（标签只写目标路径）后通过。期间修复
评测器缺陷：Pi 子进程继承非 TTY 的 stdin 时会一直等待其关闭而超时，现在无输入时
显式使用 `/dev/null`。每条仅 1 次运行，无真人验收，不构成发布基线。

## qu-ai-wei 与 Humanizer-zh：中文去 AI 味

评审日期：2026-10-09。来源：[LifelongLazyLearner/qu-ai-wei](https://github.com/LifelongLazyLearner/qu-ai-wei)
`1d32e803f091ec90808a69683ebf49e8a970a5e7`（MIT）；[op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)
`f4518a8eab97b8bfebc66a89d34320a89bef6930`（MIT）。按非 vendored 来源处理，未修改 `upstreams.lock.json`。
已读 qu-ai-wei 的 `SKILL.md`、`references/`（pattern-catalog、editing-boundaries、whitelists、examples 等）与
`tests/fixtures/`，以及 Humanizer-zh 的 `SKILL.md`；两仓库中的脚本均未执行。

| 吸收的方法 | 本地落点 |
| --- | --- |
| 改写冲突时的保护顺序（事实含逻辑关系、证据强度与引用绑定 > 用户指定与受保护文字 > 作者口吻 > 自然中文 > 原格式） | `clear-chinese.md` 开头 |
| 排除不改写成反向事实；排序、同时与先后保持；未填槽位原样保留；同层叠加的模糊限定只留一个 | `clear-chinese.md` Preserve qualifications |
| 空洞对举骨架、无证据的意义拔高、机械三连（作为需检查的症状而非禁词） | `clear-chinese.md` Remove abstract filler |
| 前置状语堆叠、推论台阶、模糊关联与生造标签、同一对象轮换称呼 | `clear-chinese.md` 对应各节 |
| 引用随陈述移动；单一来源结论超出自身限制时保留结论与限制并呈现冲突 | `source-integrity.md` |

不采用：门检与打磨报告等固定输出（与 clean 交付冲突）、真人文本停手与授权判定（write-craft 的任务即授权改写）、
凭证检测（属宿主安全层）、品牌/自媒体/平台语体与白名单、AI 高频词表（词表式黑名单），以及句长节奏调节
（易诱导为变而变）。

同轮结构调整：`SKILL.md` 拆为通用核心与场景路由；`decision-examples.md` 与 `diagnosis.md` 从原文件拆出，按需读取；
合并决策参考与来源核对之间的重复规则。典型决策稿的必读量由约 1214 行降至约 1026 行，未达到 800 行的目标；
剩余大头是 `clear-chinese.md` 的“按意思删改”示范与 `source-integrity.md` 的状态规则。

当前状态：规则已落地，新增两条 exploration 用例；效果尚未经全量回归与真人验收确认。

### 三模型全量回归（2026-10-09）

评审统一用 `deepseek/deepseek-flash`（judge thinking medium），31 条用例，每条 1 次；评审协议错误
（引用原句不匹配、结构化提交漏项）用 `--rejudge` 重评，不计入失败。

| 生成模型 | 第一轮（拆分入口后） | 最终轮（修复后） |
| --- | --- | --- |
| `anthropic/claude-sonnet-5-5` | 30/31 | 31/31 |
| `deepseek/deepseek-flash` | 29/31 | 31/31 |
| `codex/gpt-5.5` | 22/31（4 条 regression 失败） | 23 PASS、3 FAIL、5 条因 DeepSeek 余额不足未完成评审 |

发现与处理：

- 拆分入口后 Codex 回归：同样 4 条 regression 用例在 main 旧版上全部通过、新版全部失败。原因是“不得从
  空缺编造审批、门槛、后果与后续安排”被挪出入口；该规则改为通用核心规则放回 `SKILL.md`，并附真实出现的
  反例，4 条随后全部通过。
- Codex 常以 `limit=200` 读取入口且不补读（40 次中 17 次）。`SKILL.md` 压缩到 200 行以内，`validate.py`
  强制该上限。
- 最终轮 Codex 剩余失败：诊断写入读者反应（已在入口加反例）、README 改写删除维护者内容未给去处（已把
  粘贴场景的交付块要求并入移出规则）、业务场景复述（上一轮通过，属模型波动，未改规则）。
- DeepSeek 官方账户余额耗尽后，改用 `volcengine-ark/deepseek-v4-1-flash-260910` 作评审：judge 校准 35 个
  fixture 的事实判断全部符合预期（唯一不符为实验性编辑检查）。用它重评 5 条未评审用例，4 条通过；Codex
  重跑上述 3 条失败用例全部通过。
- README 翻译：Codex 两次都不加语言切换行，原因是“结构严格对齐”与“顶部互链”在规则中冲突。改为明确语言
  切换行是唯一允许的差异；随后 Codex 2/2、Sonnet 1/1 通过。
- 结论：按每条用例的最新规则版本，三个生成模型的 31 条用例均已通过，但 Codex 的结果来自多轮拼合，且每条
  只跑 1～2 次；未经真人验收，不构成发布基线。
