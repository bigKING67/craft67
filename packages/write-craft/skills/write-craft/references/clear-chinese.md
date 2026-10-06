# Clear Chinese

Use this reference for Simplified Chinese drafting and editing. The goal is
natural, professional writing that a capable non-specialist can understand on
the first reading without losing precision.

## Give each unit one job

- A heading should carry a finding, boundary, or question when that helps a
  scanning reader; avoid empty labels such as “项目背景” when a meaningful
  statement is available.
- A paragraph should develop one topic. Split it when the actor, time, claim, or
  reasoning step changes.
- A sentence should make the main relationship visible. Long sentences are
  acceptable when one idea requires qualification; they fail when several
  claims compete for attention.

Before polishing sentences, write one private core sentence: “这是什么／现在到
哪一步／这次读者最需要知道什么”. It is a compass, not a required opening.
When evidence does not support a conclusion, the core can be a question,
boundary, or progress statement instead of a confident claim.

## Delete by meaning, not by word count

For each paragraph, privately name the fact, reason, distinction, condition or
next action it adds to the reader's answer. Apply the test across the whole
answer, including headings, prose, lists and tables. If a contribution is
already complete elsewhere, edit the smallest passage that repeats it; keep
unique information in the same paragraph. Before deleting, locate where every
necessary fact, condition and uncertainty will remain. A claim that it is
“covered elsewhere” is not enough; check the actual retained wording.

Choose which occurrence to keep by its job in the argument. Preserve the early
core answer and decisive reason; deleting them because details recur later
makes the reader reconstruct the conclusion. Do not delete a separately usable
summary or a condition that qualifies a different claim. Prefer a local edit
to regenerating an otherwise sound draft. After deletion or movement, reread
for broken references, detached qualifications and headings without content.
If no edit improves the reading without loss, leave the passage unchanged.

A heading should not consume a sentence merely announcing its own subject. For
example, after “主要风险是供应商停止维护”, start the paragraph with the supplied
consequence or mitigation rather than “供应商停止维护是本方案的主要风险”.
If neither is supplied or needed, the heading itself can be a sentence in the
surrounding paragraph; an empty section is unnecessary.

Keep the reasoning that earns the conclusion. A shorter draft that drops why
an option fits the stated priorities, or hides its limiting condition, is worse.
Do not set a compression percentage, shorten every sentence, or count repeated
terms as repeated meaning. End after the last useful piece of information;
a second summary is not mandatory.

### Example: merge repeated scope and status into their useful location

This is synthetic material, not a prescribed outline or length.

**Repetitive draft**

> 拟用一张交接卡记录当天未办完的借用事项，先在前台试用；尚未试用，印制费用未询价。
>
> 交班人填写物品、存放位置和下一步动作，接班人处理后填写日期。只覆盖借用事项，不包含采购。
>
> 本期范围仅为借用事项，采购不在范围内。试用尚未开始，印制费用仍未询价。

**Edited draft**

> 拟在前台试用交接卡，记录当天未办完的借用事项，不包含采购。交班人填写物品、存放位置和下一步动作，接班人处理后填写日期。
>
> 方案尚未试用，印制费用未询价。

The edit moves the scope beside the proposed activity and keeps the two unknowns
once. It preserves who does what and when; it adds no reason, benefit or approval
gate. A separate acceptance check about procurement would serve a different
purpose and should not be deleted merely for mentioning the same boundary.

### Example: replace defensive disclaimers with positive statements

This is synthetic material. The draft is faithful but defends every sentence;
the reader has to strip the negations to find what will happen.

**Defensive draft**

> 本方案先在家居类目试点自动生成商品详情图，出图质量合格后再扩展类目和产量。这是实施顺序，不是缩减完整需求，目前仍是待验证方案。这里选家居类目仅用于说明流程，不代表最终类目。
>
> 试点不要求覆盖全部类目，也不要求建成完整设计平台。每天 200 张是后续目标，不是试点验收门槛。
>
> 此前的内部演示使用固定模板，只能说明生成链路曾经跑通，不能证明真实商品的出图质量。本文仅重组表达，未修改代码或部署。
>
> 附录：实施说明。试点不要求覆盖全部类目或完整设计平台，每天 200 张不作为试点门槛……

**Edited draft**

> 先用一个类目试点自动生成商品详情图，出图质量合格后再扩展类目和产量，目标是每天 200 张。下文以家居类目为例，试点类目由运营确认。
>
> 试点只要求做好一个类目的出图，不要求建成完整设计平台。
>
> **现状**：内部演示用固定模板跑通了生成链路，真实商品的出图质量尚未验证。
>
> 附录：实施说明（试点范围见正文）……

The edit keeps every supported fact: the sequence, the full goal, the example
status of the category, the later target, the excluded platform, and the
evidence limit of the demo. The sequence now carries “not a reduction” without
saying so; the limit is stated once as a status; the appendix points back
instead of repeating the scope; the author's editing note is gone because it
is not about the work.

## Put actors and actions back into the sentence

Prefer “运营人员提交需求，剪辑人员审核初稿” to “实现需求提交与初稿审核闭环”.
Name the actor when ownership matters. Passive or subjectless Chinese is valid,
but it should not hide responsibility, failure, or the next action.

Turn noun piles into actions:

- “进行方案可行性的验证” -> “验证方案是否可行”
- “完成对素材的检索与筛选” -> “检索并筛选素材”
- “实现效率层面的全面提升” -> state whose time changes, in which step, and
  how it will be measured; otherwise mark it as an unverified goal.

Do not inflate a short update. “已完成接口联调和本地测试；下周补监控，目前
没有需要管理层协调的事项” is clearer than expanding three facts into a project
proposal. `完成本地测试` still does not mean `测试通过` or `已经上线`.

## Keep judgments beside their basis

Place a conclusion next to the source-supported reason, condition, or evidence
gap that qualifies it. For example: “方案值得继续比较，因为它复用现有素材；
但尚无同批耗时对照，暂不能确认效率收益。” Do not add a reason merely to make
the paragraph feel complete. If the source gives only a goal, call it a goal.

## Treat jargon deliberately

For every term unfamiliar to the reader, choose one action:

- **Replace:** use an accurate ordinary phrase when nothing is lost.
- **Teach:** name the term once, explain what it does in this situation, then
  reuse it consistently.
- **Cut:** remove detail that does not help this reader understand or decide.

Do not replace a precise term with a vague benefit word, and do not
infantilize a non-technical reader by removing precision. If the reader will
meet the term in later discussions, withholding its name makes the document
less useful.

A plain-language rewrite must explain a term, not merely move it into a shorter
sentence. For example, `120 个已缓存查询样本` can become `120 条能够直接从缓存中
读取结果的查询`; keep the sample boundary and do not generalize that result to
uncached queries, writes, or the whole system.

## Preserve qualifications

Do not delete or silently strengthen:

- numbers, populations, time windows, preconditions, and exceptions;
- the source and date of evidence when freshness matters;
- uncertainty or competing explanations;
- the distinction between “不能”“暂不支持”“尚未验证”“计划实现”;
- constraints that change cost, time, risk, or the decision.

Use “预计”“目标”“假设”“待验证” only when those are the true evidence states.
Avoid decorative hedging; uncertainty should be specific enough to act on.

## Keep the whole answer within a hard length limit

`SKILL.md` defines what the limit covers. When drafting to it, count
conservatively and leave margin instead of drafting to the exact edge. Shorten
headings, remove repeated conclusions, flatten low-value structure, and combine
compatible qualifications before removing a fact that changes the decision.

## Remove abstract filler

Words such as “赋能”“抓手”“闭环”“智能化”“全链路”“全面提升” are not forbidden,
but each must do more than signal importance. Replace it with the mechanism,
owner, observable result, or test when possible.

Do not add symmetrical slogans, repeated conclusions, unnecessary quotation
marks, or mechanical “首先、其次、最后” transitions merely to sound polished.
Vary sentence rhythm only after the logic is clear.

## Keep the author's voice

When examples of the author's writing exist, preserve their level of warmth,
directness, and formality. Correct ambiguity and stiffness without turning every
document into ceremonial corporate prose. Read the final draft aloud; revise
places that require backtracking or sound unlike something a person would say.

## Finish the editorial pass

Read the complete draft in order, not just the sentences changed last. For a
short update this can be a brief self-check, not a separate workflow or output.

- **Structure:** can the reader follow the explanation using the supplied
  information? Put prerequisites before what depends on them. Parallel sections
  may remain parallel; do not invent a causal bridge to make them flow.
- **Paragraph contribution:** identify what each paragraph adds. Merge or cut
  a restatement that adds no fact, condition, reason, action, or useful contrast.
  Apply this across headings, summaries, prose, lists, and tables. Preserve a
  summary with an actual independent reading purpose and repeated boundaries
  that add acceptance checks;
  repeating a precise term is not itself redundant meaning.
- **Sentences:** check who acts, what the action applies to, what pronouns refer
  to, and how conditions qualify the claim. Repair missing relationships from
  supported material. Do not force short sentences or remove useful connectives.
- **Wording:** check accurate meaning, natural collocations, and consistent
  terminology and tone. If synonym substitution leaves an awkward sentence,
  reconstruct it around its intended meaning. Keep already natural wording.
- **Presentation and ending:** headings should help navigation, tables should
  expose a comparison, and emphasis should identify something important. Remove
  low-value containers and repeated closing summaries, not necessary conditions.

Keep editing commentary out of clean copy. For example, `不能把节省时间写成
已经验证的效果` tells the writer what to do; a reader-facing version is
`实际节省时间尚未验证`. Relevant uncertainty belongs in the document; a defense
of the writer's choices does not. End when the reader's task is served.

Choose gaps by the reader's task, not simply because the source mentions them.
With the same source stating that the old process is unspecified, an explanation
of the proposed process can omit that absence; a requested old/new comparison
must disclose that the old side cannot be reconstructed from the material.
Neither version may invent the old process. A comparison of steps and a
measurement of elapsed time are distinct questions; preserve that distinction.

After editing, recheck facts, conditions, authority, and the total length. Do not
trade meaning for smoothness or describe self-editing as an independent test.

## Final reader check

Before delivery, confirm that a reader can identify:

- what problem or opportunity matters;
- what is recommended and why;
- what is in scope, and any exclusion they would otherwise assume;
- what evidence is known and what remains unverified;
- what resources, risks, and trade-offs matter;
- what, if anything, they must decide or do next.
