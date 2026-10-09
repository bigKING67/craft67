# Diagnosis

Read this reference, together with `source-integrity.md`, for every Diagnose
request in every scenario. A scenario reference may add the problems typical of
its document type; these rules decide how any diagnosis is grounded.

## Diagnose what is actually present

In Diagnose, use `observed feature -> possible comprehension risk -> supported
revision direction`. For example: “原稿先列实现组件，最后才说明业务目的” is an
observed feature; “这种顺序可能让读者更难在接触组件时判断这些信息为何重要”
is a bounded comprehension risk; “把原稿已有的业务目的移到组件说明之前” is a
supported direction. Do not replace that chain with claims about how bosses
usually read, what they know, or when they stop reading.

Keep the middle step explicitly conditional: use “可能让……更难定位” or
“读者可能需要先……再……”, not unqualified predictions such as “读者需要先……
之后才能……”, “读者无法理解”, or “只能读完全文才知道”. Describe a missing
relationship or reader task as a feature of the text, not as proof that a reader
must guess, cannot understand, or will not know how to respond. Diagnose only
what the supplied text or summary makes observable. A summary that says
components appear first does not establish that the source lacks role
descriptions, inputs, outputs, or relationships. If the available material is
enough for the requested diagnosis, deliver the bounded diagnosis without
ending with requests to paste more material, choose a communication purpose,
or ask for another rewrite.
Respect the source's stated completeness. If the user identifies the supplied
text as the complete draft, do not relabel it as a summary, claim that the
original wording was unavailable, or append a caveat about not having seen the
full document.
Distinguish information that is absent from information that appears too late
or is hard to find. If the source states the business purpose near the end,
diagnose its position; do not say that the document has no purpose or never
explains what the work is for.
When the source already states what each component does, acknowledge those
actions and diagnose only the relationship, order, or decision framing that is
actually absent. Treat an unstated reader task as an observed gap; do not turn
it into a question the user must answer before receiving the diagnosis.
A Diagnose response is incomplete if it stops at problems and risks. Give at
least one prioritized, source-supported revision direction. Moving an existing
business purpose before the component paragraphs is a revision direction, not
an unauthorized full rewrite.
Describe an absent reader task as `文档没有说明读者需要做什么`, not as the
predicted outcome `读者看完不知道如何回应`. If component relationships are
missing, recommend adding them only when another supplied source supports them;
otherwise keep the stated component actions parallel. Do not tell the writer to
infer each component's business contribution from the component description.

Keep predictions about reader cognition or document effects conditional too.
Phrases such as `老板读完仍然不知道`, `读者只会记住`, or `阅读成本会下降`
claim an outcome; use them only when evidence supports that outcome. Otherwise
describe the observable order or omission and the comprehension risk it may
create.

**Source excerpt**

> 识别服务读取质检照片并标记异常区域。索引库保存设备编号和照片位置。任务队列记录每条检查任务的处理状态。查询接口按设备编号返回检查结果。我们希望借此减少人工查找异常照片的时间。原稿没有说明需要负责人批准什么。

**Request**

> 只诊断为什么负责人可能难抓住重点，不要重写。

**Bounded diagnosis**

> 影响理解最大的不是四个组件“没有解释”，而是信息顺序和组件关系没有建立。
>
> - **业务目的出现得晚。** 原稿先连续说明四个组件各自做什么，最后才说明希望减少人工查找异常照片的时间。这种顺序可能让读者更难在接触组件时判断这些信息为何重要。可以把原稿已有的业务目的前移，再保留必要的组件说明。
> - **组件动作已有，但关系未说明。** 原稿已经说明识别服务、索引库、任务队列和查询接口分别做什么；没有说明的是它们之间的先后、依赖或数据流。若原材料能支持这些关系，可以补充；如果不能，就保持并列说明，不要补造流程。
> - **阅读任务没有交代。** 原稿明确没有说明负责人需要批准、选择或配合什么。诊断可以指出这一空缺，但不能替作者制造审批事项。

This diagnosis acknowledges the supplied actions, limits criticism to the late
purpose, missing relationships, and absent reader task, and ends without asking
for more material or offering a rewrite service.
