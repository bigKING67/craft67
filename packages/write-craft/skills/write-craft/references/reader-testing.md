# Reader testing

Read this reference for every consequential Draft or Rewrite, as `SKILL.md`
defines it. Reader testing checks whether the final document works without the
author's conversation history. It is not a confidence ritual and must not be
claimed unless a genuinely fresh context received only the final document and
test questions.

## Contents

- Review order and revision budget
- Prepare answerable understanding points
- Run a human reading test
- Use an independent model context when appropriate
- Interpret results without confusing disagreement with misunderstanding
- Revise within a fixed budget

## Review order and revision budget

Treat drafting, source review, and any reader test as one bounded quality
workflow. After the first draft, apply the two-way check in
`source-integrity.md` before asking a blind reader to interpret the document.
Use a genuinely independent context for review only when the capability is
available and authorized; otherwise self-check and do not claim independence.

When independent review is used to assess writing quality, give the editor the
request and complete draft as a separate reading task. A long source checklist
is not a substitute for reading the prose continuously. The source reviewer
must confirm or reject the editor's proposed issues against the request and
sources before revision. Keep preferences distinct from located problems and
preserve necessary actors, conditions and checks.

If a fact or reader check finds a blocking issue, or a confirmed editorial check
locates an actual problem such as duplicated meaning or an unsupported argument,
use at most one additional revision. Remove, narrow, or correctly label
unsupported claims; repair the located problem without dropping necessary
conditions. Do not revise merely to satisfy a reviewer's format preference.
Then rerun the affected checks, including source fidelity after an editorial
change. All three kinds of feedback share this one revision budget; a later
reader test does not reset it. If a blocking conflict, unsupported claim or
located editorial problem remains, do not call the document ready; surface the
unresolved limitation. Keep clean copy free of testing instructions; if
validation status is requested or required for acceptance, report the missing
check separately and concisely.

## Prepare answerable understanding points

Before testing, derive the important understanding points from the source and
the communication purpose. Choose neutral questions a real reader would ask.
Cover only the dimensions relevant to this document, such as purpose, process,
evidence, scope, resources, risks, uncertainty, and requested action. Use
questions with checkable answers; do not ask whether the prose “feels good” or
embed the desired answer in the question.

Examples:

- What problem is this proposal trying to solve now?
- What is recommended for the first stage, and what is explicitly excluded?
- What evidence supports the recommendation?
- Which benefits are observed, estimated, targeted, or still unverified?
- What people, time, budget, or dependencies are required or still unknown?
- What could make the proposal fail or cause the team to stop?
- What decision or action is requested from the reader?

## Run a human reading test

For exploratory validation, use three to five real, de-identified documents
when available; include at least one source whose technical detail currently
buries the main point. This is a practical starting range, not evidence of broad
generality.

Use a reader who did not write the source, join the project discussion, or see
the comparison version. Give them only the candidate document. Ask them to:

1. freely restate what the document says;
2. answer the neutral understanding questions; and
3. identify what remains unclear or requires more context.

Do not explain the project until this first round is complete. Record:

- whether the reader understood the purpose, workflow, boundaries, and status;
- what the author had to explain afterward;
- where the reader reread or struggled to find the point, plus actual reading
  time when practical; and
- how much structural, factual, and sentence editing remains before sending.

Do not substitute a synthetic example for a missing real document or describe
the author's self-review as an independent reader result.

Use a compact record such as:

```text
Document and source revision:
Communication purpose and intended reader:
Reader independence (what they had seen before):
Candidate revision:
Reading time and reread locations:
Free restatement:
Question / answer / source-grounded result:
Extra explanation the author had to provide:
Remaining structural / factual / sentence edits:
Test status: completed / partial / not run
Limitations of this comparison:
```

## Use an independent model context when appropriate

Give the reader only the final document and questions. Ask it to answer each
question, cite the section that supports the answer, list ambiguities, identify
assumed background knowledge, and flag contradictions. Do not include the
author's intent, prior discussion, expected answers, or suspected defects.

Model review expands coverage; it does not replace human calibration for claims
about real readers. A successful model response means the stage executed, not
that its answer was correct.

## Interpret and revise

Complete source-integrity review before blind reading. Do not spend a reader
test on a draft already known to contain unsupported claims.

Compare the reader's answer with the source-grounded understanding points:

- If the source contains a material fact, the draft omits it, and the reader
  says “文档未说明”, the reader is correct and coverage failed.
- If the source is genuinely unknown and the draft says so, lack of a definite
  answer is not a writing failure.
- If the draft adds a false fact and the reader repeats it accurately,
  comprehension succeeded but source integrity failed.
- A reader can understand a proposal and still disagree with it or ask a normal
  business question. Disagreement is not evidence of unclear writing.

Fix the document, not the test, when a material question cannot be answered,
within the shared budget above. Report first-draft and revised results
separately. Do not keep trying until one favorable output appears or polish
indefinitely for minor preferences.

## Fallback prompt

When no independent context is available or authorized, do not claim the test
was executed. Provide this prompt for a new conversation only when the user asks
for a testing aid; do not append it to clean copy by default. When validation
status is requested or required for acceptance, report the unrun check separately
without substituting this prompt for evidence:

```text
你是一名没有参与该项目、不了解此前讨论的独立读者。只根据下面的最终文档回答问题；不要用常识补齐文档没有提供的信息。

请先回答我附上的每个问题，并为每个答案指出文档中的依据。然后单独列出：
1. 无法从文档回答的问题；
2. 含义不明确或可能有两种解释的表述；
3. 文档默认读者已经知道、但没有解释的背景；
4. 前后矛盾、把目标写成结果或把假设写成事实的地方；
5. 读者可能因此做出错误决定的遗漏。

如果文档没有给出答案，请明确写“文档未说明”，不要猜测。

【待测试文档】
<粘贴最终文档>

【读者问题】
<粘贴 5 至 8 个问题>
```
