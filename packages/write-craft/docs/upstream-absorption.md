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

- `SKILL.md` owns routing, task modes, evidence boundaries, question policy,
  delivery order, and reference loading.
- `references/decision-documents.md` owns decision framing, information
  layering, scenario use, and decision-relevant technical constraints.
- `references/clear-chinese.md` owns Chinese expression, terminology, precision,
  and naturalness.
- `references/document-presentation.md` owns platform-neutral visual hierarchy,
  semantic emphasis, and rendered-document verification; platform writes stay
  outside Write Craft.
- `references/source-integrity.md` owns faithful explanation, two-way coverage,
  relevant unknowns, and unresolved source conflicts.
- `references/reader-testing.md` owns fresh-context acceptance and fallback.
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
