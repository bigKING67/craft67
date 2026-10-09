# Decision documents

This is the scenario reference for decision and project communication: a draft
that must help a non-technical reader understand a complex proposal, follow
progress, compare options, approve a bounded next step, or decide not to
proceed. Read it for every Draft, Rewrite, or Diagnose in this scenario. It is
guidance, not a mandatory template. Complete synthetic examples live in
`decision-examples.md`.

## Contents

- Scenario contract
- Start from the decision
- Find the load-bearing idea
- Build a pyramid of findings
- Design the first reading layer
- Separate the decision entry from the engineering source when needed
- Use a source-supported scenario
- Layer the body by reader need
- Use the lightest table that fits the reader's task
- Keep decision-changing constraints visible (includes appendix rules)
- Keep the evidence boundary explicit
- A worked decision structure

## Scenario contract

**Commitments under preserve.** Budget, schedule, scope, staffing, acceptance,
approval state, and the chosen approach. This includes approved plans: do not
redesign one into a pilot or reopen a decision merely because another option
reads better.

**Reading order.** Lead with the bottom line that the reader needs. A decision
document normally lets a scanning reader find the problem, recommendation,
strongest reason, material uncertainty, and requested decision before
implementation detail. Decision-ready does not mean every document needs a new
decision. If neither the request nor the source specifies an approval, owner,
pilot, or next-step process, do not manufacture one from the gaps; explain what
the supplied material supports and keep consequential unknowns visible. Do not
invent an approval request when the source is only a status update. Do not
impose a fixed number of reasons or a stock “背景—方案—收益—总结” outline.

**Versions for different readers.** Change emphasis, order, and explanation
depth. Do not turn a source activity into a new audit duty, ongoing
confirmation requirement, acceptance purpose, or control process merely because
the execution version needs more detail.

**Optional forms.** Apply the usage-scenario (使用场景), appendix, and separate-decision-entry
rules below when those forms are requested or useful; their source boundaries
remain mandatory.

## Start from the decision

State the reader's task in one sentence. Distinguish these common outcomes:

- **Understand:** establish a shared model; do not invent an approval request.
- **Choose:** compare real alternatives using the same decision criteria.
- **Approve:** state the bounded resource, scope, risk, or next stage being
  authorized.
- **Act:** name the owner, next step, and trigger or deadline when supplied.

“Learn about the project” is not yet a decision. When no decision is required,
the document may end with a next step already supplied by the source; otherwise
it does not need to manufacture one.

## Find the load-bearing idea

Identify the one idea that makes the rest easier to understand. Express it in
plain language without losing its condition or uncertainty. Use it to organize
the explanation; do not give every implementation detail equal weight.

For a technical-to-business rewrite, translate this sequence:

`implementation mechanism -> changed workflow -> observable result -> decision value`

Use only the links the source states or clearly entails. A component list may
support a component-level explanation without supporting a changed workflow.
Do not skip directly from a mechanism to revenue, efficiency, quality, or
adoption unless evidence establishes that link, and do not fill an absent link
with a conventional process.

## Build a pyramid of findings

This applies the core “Group and reason” step to decisions. A finding must add
a supported meaning, not just name the group: “两方案都能按期交付，差别在费用与后续维护” says more than
“方案分析”. Do not derive that finding unless the source supports both parts.

Test the relationships before drafting:

- **Vertical support:** if the parent says “建议选甲”, its children must explain
  why that choice fits the stated criteria. Listing what 甲 contains is not
  enough. Evidence belongs under the reason it supports. If a premise is missing,
  narrow the judgment or expose the consequential uncertainty; do not supply it.
- **Horizontal grouping:** reasons for choosing, implementation steps and
  expected results have different jobs; do not mix them as three “advantages”.
  Compare alternatives with the consistent criteria described under “Layer the
  body by reader need”, preserving an unknown cell rather than guessing it.

Use the reader's situation and the change or difficulty only to establish the
question when it is not already obvious. Do not prepend a background story to a
short update. The answer can be a current state or a conditional conclusion;
writing about a project does not itself authorize recommending another project.

After drafting, read only the opening and the section claims: do they form a
coherent answer? Then read the support under each claim: does it explain or
substantiate the claim, or merely repeat it? Revise the grouping before wording.
This checks the argument, not the number or style of headings.

## Design the first reading layer

Open with the answer this reader needs, including the condition without which
it would be misleading. Choose the relevant problem, recommendation or current
state, decisive reason, limitation and requested action from the source. These
are selection criteria, not five compulsory sentences or a miniature copy of
the whole body. Put each supporting detail where it serves the argument once.

A short update can be one paragraph or a small list of completed work, remaining
work and relevant dependency. A proposal explanation can state the supported
use and then its constraints. A comparison can use one common-criteria table and
a decision paragraph that interprets it. Choose by the task; no format or
paragraph count is mandatory. If the form already answers the question, stop.

Use a separate summary when requested or when it has a real independent reading
purpose, such as a decision entry paired with a full engineering source. Write
it after the body is sound and include the conclusion. Do not add a summary to
a short report merely to satisfy “conclusion first”. A heading and its paragraph
should contribute different information, just as prose and a table should.

## Separate the decision entry from the engineering source when needed

When one document must serve both decision-makers and implementers, a short
summary at the top may still leave the first reading path too long. If the
existing engineering plan must remain complete, preserve it as the detailed
source and create a shorter decision entry that can stand on its own. The short
entry should contain only the supported elements needed for the decision. These
may include the recommendation, a representative workflow when the source
provides one, a bounded first-stage deliverable and acceptance method, explicit
non-goals, material unknowns, and a real next decision or action. Omit an
inapplicable element instead of filling it from convention. Link to the detailed
source for architecture and implementation mechanics instead of copying them
all.

If the short entry and engineering source are separate files, or may be split
after delivery, put an explicit pointer inside the short entry itself. Name the
included file, attachment, or exact section, for example `完整工程方案见文件二`.
Showing the engineering source later in the same response is not enough: the
short entry must retain the path when copied or sent on its own.

Use the reader's present task to choose detail, not the source's section count.
When the task is to confirm a first-stage scope and inputs, explain the complete
goal but develop the first stage. Category examples, historical tables and
later-stage mechanics may remain in the linked detailed source when they do not
change that decision. Do not reproduce every category list and illustrative
case merely to prove that the source was read. This does not authorize deleting
material the user explicitly asks to preserve in full, narrowing the approved
plan, or hiding a condition that affects the current choice.

Do not use the split to hide a constraint. Any fact that changes feasibility,
cost, timing, risk, acceptance, or the requested authorization must still
appear in the decision entry.

## Use a source-supported scenario

When an architecture description is too abstract and the source supplies the
necessary relationships, show one representative flow:

1. who begins the task and with what input;
2. what the proposed system or process does;
3. where a human reviews, changes, or rejects the result;
4. what output is produced;
5. how success and failure will be observed.

For a product explanation to business readers, place a supported scenario near
the opening when it helps explain the use before the architecture. Start with
the user's task, supplied input, proposed action, and observable output; include
the human role and boundary where supported. Keep approval requests or urgent
decision-changing facts first when that is the reader's task. A scenario is not
a compulsory opening for short updates, diagnoses, or sparse component lists.

Distinguish the evidence behind a case:

- A real case names only supplied materials, events, and observed results. Real
  input material alone does not establish that a proposed output was produced.
- An illustrative scenario explains supported behavior and is visibly labeled
  as illustrative. It must not invent customer history, an old manual process,
  pain, measured savings, capabilities, or successful results. A plausible
  before/after table also needs source support on both sides.
  For example, `目标减少人工核对时间` supports that goal, not `现在靠人工逐项
  核对` as a description of the existing process. Explain the proposed task
  directly when the current process is unspecified.
- When the source says real materials are still being prepared, add a brief
  relevant note and continue with the supported explanation. If the user has
  deferred supplying them, do not repeatedly request them or make the otherwise
  usable document depend on them. Do not call materials unfinished merely
  because the source does not mention them.

Give each presentation form a distinct job. A case can explain the use; steps
can add actionable sequence; a table can compare choices or acceptance criteria.
If these forms only repeat the same actors, inputs, actions, and outputs, merge
or remove one. Preserve necessary emphasis on consequential boundaries and the
independence of a short entry from its engineering appendix.
This also applies to prose: after a complete scenario, omit a paragraph that
only restates its purpose, output, and human boundary. For a usable explanation,
do not append an inventory of facts you avoided inventing. Omit irrelevant
absences; if one matters, retain `材料未说明` rather than claiming the activity or
record does not exist.

Label the scenario as an example when it is illustrative. Do not let an example
silently become a promise that every case behaves the same way. Each actor,
input, action, review point, output, and boundary must come from the source or a
clear entailment. Module names alone do not establish who initiates work, where
humans intervene, what gets recorded, or what happens next. If those links are
absent, explain the components without constructing a scenario.

## Layer the body by reader need

Choose only the sections the decision requires and the source can support.
Useful candidates include:

- current problem and why it matters now;
- proposal and representative use case;
- first-stage scope and explicit non-goals;
- alternatives and trade-offs, including the status quo when relevant;
- deliverables, owners, dependencies, and sequence;
- acceptance method and evidence needed;
- people, time, budget, and operational load;
- risks, mitigations, stop conditions, and fallback;
- requested decision or next action;
- technical appendix.

Use consistent criteria when comparing options. Do not praise one option for
speed and reject another for cost without showing both criteria for both
options. Follow the reader's supplied priority order. If the primary criterion
has no comparable evidence, say what cannot be ranked; do not manufacture a
winner from a cheaper price, a different population, an analogy or an adjacent
metric. “Delivered” need not mean “understood”, just as “tested” need not mean
“passed”. Adding “probably” does not supply the missing relationship.

Preserve a source's tentative recommendation as tentative under **preserve**.
When **propose** is authorized, new recommendations may interpret supported
trade-offs but must not claim an unmeasured advantage. Explain any condition
under which the available evidence supports a choice. If it supports no such
choice, give the comparison and its decision limit rather than force a winner.

## Use the lightest table that fits the reader's task

For a small, static comparison such as scope, stages, responsibilities, or
acceptance criteria, use the destination document's native table when it makes
scanning easier. Introduce a spreadsheet or another embedded data artifact only
when the task actually needs formulas, live data, filtering, calculation, or
independent data collaboration. A more powerful container is not automatically
a clearer one; it can add navigation, access, and maintenance overhead without
helping the decision.

## Keep decision-changing constraints visible

A technical fact belongs in the main body when it changes any of these:

- feasibility or supported use cases;
- cost, staffing, or operational burden;
- delivery time or dependencies;
- security, privacy, compliance, or rights;
- failure recovery or business continuity;
- acceptance thresholds or quality risk.

Explain the consequence in reader language, then place implementation mechanics
in the appendix if further detail is useful. Move detail to an appendix only when
it does not change the decision.

If the source supplies only decision-changing constraints and no implementation
mechanism, keep the constraints in the body and omit the appendix. Do not invent
placeholder mechanisms, new checks, owners, optionality, or `待补充` appendix
items merely to satisfy an appendix request, and do not pad the explanation with
hypothetical implementation examples. Omit the appendix cleanly: do not justify its absence by listing
conventional fields such as components, interfaces, or deployment methods that
the source did not mention, and do not add
`来源没有实现细节`, `没有可放入附录的内容`, or any other explanation for it.

## Keep the evidence boundary explicit

Use the strongest accurate verb:

- **observed / verified:** directly supported by current evidence;
- **estimated:** derived from stated inputs or a model;
- **expected:** a reasoned forecast, not yet observed;
- **targeted:** an intended outcome;
- **unknown / pending confirmation:** no adequate basis yet.

If the source explicitly leaves a relevant cost, duration, headcount, baseline,
or success threshold unknown, retain that uncertainty and its direct decision
impact. Which absences to surface, and at what granularity, follows
“Status, scope and missing information” in `source-integrity.md`. Smooth prose
must not conceal the gap or manufacture the process for closing it.

## A worked decision structure

The following example is synthetic. It demonstrates grouping and information
gain, not a fixed heading template.

**Source material**

> 甲方案每年 6 万元，能在 3 周内交付并启用，后续由供应商维护。乙方案每年 4 万元，交付并启用要 7 周，后续由本部门维护。目前本部门没有可安排的维护人员。业务要求 4 周内启用，先满足上线时间，再比较费用。两方案都能导出所需报表。建议采用甲方案，请负责人决定是否批准每年 6 万元费用。

**Weak organization**

> 建议采用甲方案。理由有三点：支持报表导出、安排供应商对接、每年费用 6 万元。

This mixes a shared capability, an unstated action and a cost as though they
were comparable reasons for the choice. Leading with a recommendation has not
established support for it.

**Complete rewrite**

> 建议采用甲方案，请批准每年 6 万元费用。甲可在 3 周内交付并启用，满足 4 周内启用的要求；乙需要 7 周，无法满足这一时间要求。
>
> 甲比乙每年贵 2 万元，但后续由供应商维护。乙需要本部门维护，而目前没有可安排的维护人员。两方案都能导出所需报表，因此这项能力不构成选择差异。

The first paragraph answers the decision and supplies the decisive timing
comparison. The second adds the cost trade-off, maintenance constraint and
non-differentiating capability. It does not repeat the recommendation in an
extra conclusion, nor turn the document into an implementation plan.
