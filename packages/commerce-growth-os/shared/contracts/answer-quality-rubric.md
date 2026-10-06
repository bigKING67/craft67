# Answer Quality Rubric

## Contents

- Universal quality gates
- Specialist-specific contracts
- Mode-specific requirements
- Lint and currentness validation

## Load when

Use this reference when polishing a final answer, validating saved eval answers, reviewing whether a commerce strategy answer is too generic, or maintaining this skill's eval scripts.

## Quality gates

A strong answer must pass these gates:

1. **Decision first**: answer the user's narrow question before expanding into a plan.
2. **Confirmed vs assumed**: separate confirmed facts, assumptions, and recommendations when data is incomplete.
3. **Economics before scale**: do not recommend budget, creator booking, discount, channel entry, or SKU expansion without unit economics or an explicit missing-data condition.
4. **Assortment and price before channel**: do not jump to platform tactics before SKU role, price ladder, and price-floor logic.
5. **Channel job clarity**: explain what each channel is supposed to do and which metric proves it is working.
6. **Executable contract**: state the mechanism, owner, success/completion signal, material risk, and next review or decision point.
7. **Domain guardrail**: apply the specialist-specific contract below rather than forcing paid-media language into unrelated work.
8. **Currentness label**: label platform-current claims as `Officially verified`, `Confirmed from user backend`, `Stable operating principle`, or `Needs current verification`.

## Specialist-specific contracts

- **Commercial / Growth**: economics, stop rule, and scale rule. Paid media, creator economics, discount, channel entry, and budget recommendations fail without both guardrails.
- **Operations**: exception path, escalation owner, and recovery/reopen condition.
- **Brand**: approval path, veto condition, and exit/termination condition.
- **Content**: quality gate, rights/usage boundary, and refresh/retirement rule.
- **Analytics**: confidence, alternative explanation, and next evidence required.

Do not invent a scale rule for a data-quality diagnosis, crisis response, content review, or operational recovery. Use the contract of the actual decision domain.

## Anti-patterns

Reject or rewrite answers that use these phrases without a concrete mechanism, owner, success/completion signal, material risk, and next review or decision. Add stop/scale only when the active specialist contract or an investment decision requires it:

- "提升品牌曝光"
- "优化内容"
- "加强运营"
- "加大投放"
- "提高转化率"
- "找更多达人"
- "多做种草"
- "冲GMV"
- "做全域布局"

Replace them with:

```text
Decision -> evidence status -> mechanism -> owner -> success signal -> material risk -> next review/decision
```

## Mode-specific checks

### Quick diagnosis

Must include:

- Current judgment.
- Bottleneck.
- Missing data or assumptions.
- Next three actions.
- Main risk.

### Decision memo

Must include:

- Decision: yes/no/test/hold.
- Evidence or assumptions.
- Mechanism and conditions.
- Owner and success signal.
- Next decision/review.
- Main risk.

### Full operating plan

Must include:

- Business model and break-even logic.
- Assortment and price ladder.
- Channel jobs.
- Content and landing plan.
- Paid/live/creator guardrails.
- Fulfillment/after-sale risk.
- Review cadence.

### Data review

Must include:

- Metric movement.
- Likely cause.
- Decision.
- Owner/action.
- Confidence, alternative explanation, and next evidence when Analytics owns the review.
- Next review window.

## Currentness checks

For platform-current questions, split the answer into:

- Stable operating principle.
- Current platform claim and evidence label.
- Source or backend to verify.
- Decision impact if the platform entrance, product name, rule, or report field changed.

Do not turn an official URL into a current capability claim unless the relevant page/backend was checked in the current session.

## Maintainer lint commands

Use deterministic lint for saved answers:

```bash
python3 tooling/evaluation/lint_answer.py --mode decision_memo --answer path/to/answer.txt --json
python3 tooling/evaluation/lint_answer.py --answer-dir path/to/answers --cases eval/cases.json --json
```

Use the golden-answer suite after changing the skill contract, eval cases, or linter:

```bash
bash scripts/run_eval.sh eval/golden-answers
```

Use the source registry checker after editing currentness source references:

```bash
python3 tooling/evaluation/check_source_registry.py shared/currentness/currentness-official-sources.md --json
```
