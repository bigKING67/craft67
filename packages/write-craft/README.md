# Write Craft

Write Craft 把复杂技术方案、项目提案和工程说明重组为非技术决策者能够理解、判断并采取行动的文档，也负责项目 README 的审查与改写。它优先解决信息顺序、论证边界和读者理解，而不是只把句子润色得更顺。

## 当前开发候选状态

当前工作区候选尚未通过正式发布验收。已见样本中，来源约束有作用，但首稿仍可能重复；
在主代理定位具体问题后，Pi 的 DeepSeek Flash 曾在一次修订内完成修复。
这不证明模型能自主发现所有缺陷，也不代表用户已认可文风。当前按“起草—主代理审稿—
必要时一次修订”使用，最终仍需核对来源、结构与重复。实验性自动编辑检查默认关闭。
本地候选包用于审阅和隔离试用，不代表正式发布或已更新全局安装。

## 能力边界

- 改写已有工程方案：完整阅读原稿后，先给可用的老板版或决策版全文。
- 从材料起草决策文档：明确问题、建议、依据、取舍、投入、风险和待决事项。
- 只做诊断：指出结构、论证、术语和证据问题，不擅自改写全文。
- 项目 README：审查、改写和翻译，让潜在使用者快速判断项目是否适用；规则见 `skills/write-craft/references/readme.md`。
- 区分编辑权限：普通改写默认保留既定方案；只有用户明确允许时才提出方案变更。
- 默认交付纯成稿：不附 AI 过程说明；需要学习改法时再输出少量注解。
- 保留精度：不编造预算、工期、人员、效率、收益、指标或已实现能力。
- 双向核对来源：既拦截无依据新增，也保留影响本次阅读任务的条件与例外。
- 独立读者测试：在有独立上下文且获授权时执行；未执行时不冒充通过，仅在用户需要测试辅助时提供提示词。

当前不负责广告创意、产品 UI 微文案、飞书或 Word 的平台操作，也不替代完整的 API 参考手册、运维手册或开发者教程。需要文件或平台操作时，可将 Write Craft 作为内容层与相应能力组合。

## 安装与加载

先将 craft67 检出到已验证的提交，再从 `packages/write-craft` 加载或安装：

```bash
# 开发或评测：直接加载当前源码，不修改 Pi 的安装设置
pi --no-skills --skill skills/write-craft

# 日常使用：安装包子目录，不要安装 monorepo 根目录
pi install /path/to/craft67/packages/write-craft
```

要给同时读取 Agent Skills 目录的宿主使用，可将 `skills/write-craft/`
安装为 `~/.agents/skills/write-craft/`。源码目录、全局安装目录和当前会话
是三个不同状态：文件一致只证明安装内容一致，不证明已经运行的会话加载了
这个版本。升级后应新开会话或按宿主机制重新加载。

## 获取源码

仓库使用 Git submodule 固定上游参考版本。完整克隆源码时使用：

```bash
git clone --recurse-submodules https://github.com/bigKING67/craft67.git
cd craft67/packages/write-craft
```

只使用已打包的 `skills/write-craft/` 不需要加载上游仓库。

## 源码结构

- `skills/write-craft/`：唯一可安装产品。
- `upstreams/`：固定提交的原始参考仓库，不进入安装包。
- `docs/upstream-absorption.md`：吸收、拒绝和延期矩阵。
- `evals/cases.json`：行为验收案例，不包含模型生成结果。
- `scripts/` 与 `tests/`：源码、上游和打包验证。

## 本地验证

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/package_check.py
```

这些命令验证源码结构、静态合同、测试和打包边界。开发中的 Skill 或用例可以
在没有新模型基线时通过源码检查，因此源码检查不代表候选已经达到发布门槛。
准备版本候选时还必须运行：

```bash
python3 scripts/release_check.py
```

发布检查会把当前 Skill 摘要、当前用例合同和同版本真实行为基线绑定起来。
修改 Skill 或用例后，在完成新的真实评测并保存对应基线之前，它应当失败；
不得复制旧 PASS 或手工编造新基线来消除失败。

`evals/release-policy.json` 还要求回归用例全部通过、探索结果或 `NOT_RUN`
明确披露、当前评审器正反校准通过，并绑定至少三份真实脱敏文档的真人阅读
摘要、独立性记录和比较限制。三份只是本候选的最低探索门槛，不代表普遍有效。
发布检查最后会实际运行包边界检查；通过模型阶段并不替代安装内容检查。

`python3 scripts/upstream_status.py --remote --json` 可只读比较固定提交与远端 HEAD；它不会更新 submodule。

## 真实行为评测

真实评测通过 Pi 显式加载仓库里的 Skill。生成阶段只开放 `read`，用于读取
`SKILL.md` 引用的运行时参考；评审阶段不加载 Skill，也没有文件或命令工具，
事实和理解阶段只开放对应的终止式结构化提交工具。Pi 先按 schema 校验工具参数，
评测器再核对 case id、逐项覆盖、顺序和汇总状态；结构合法不代表内容通过。
事实评审先核对来源与交付合同；只有声明 `reader_test` 的用例，才会把候选稿
单独交给看不到来源和答案要点的盲读者，再由另一个上下文核对读者实际理解。
模型调用不会在 CI 中自动运行，也不会自动重试。

关键用例可以声明 `semantic_contract`，分别记录来源事实、允许与禁止的推断、
未知信息及读者应理解或不应误解的内容。未知信息必须区分来源“未说明”
（`not_stated`）与来源明确说明“尚未确定”（`explicitly_unknown`）。该账本只
提供给事实评审和理解核对，不提供给生成阶段或盲读者，避免把答案写进候选稿。

```bash
python3 scripts/eval_behavior.py \
  --suite smoke \
  --model deepseek/deepseek-flash \
  --judge-model deepseek/deepseek-flash \
  --reader-model deepseek/deepseek-flash \
  --reader-judge-model deepseek/deepseek-flash \
  --thinking medium \
  --judge-thinking medium
```

在依赖评审器结果前，可以单独运行正反校准集；该模式不生成候选稿：

```bash
python3 scripts/eval_behavior.py \
  --calibrate-judge \
  --judge-model deepseek/deepseek-flash \
  --judge-thinking medium
```

`--suite smoke` 运行四个核心案例；`--suite full` 运行全部案例；重复
`--case <id>` 可以只选择特定案例；`--track regression` 与
`--track exploration` 可以分开运行已承诺能力和探索能力。盲读者与理解核对
默认复用 judge model，也可以用 `--reader-model` 和 `--reader-judge-model`
明确指定。结果默认写入被 Git 忽略的
`.artifacts/write-craft-evals/<timestamp>/`，其中包含输入摘要、候选稿、逐项
判分、模型与 Pi 版本、Skill 摘要、结构化提交扩展摘要和退出状态。原始 Pi
JSONL 默认不落盘；仅在排障需要时显式增加 `--keep-raw-jsonl`，每个阶段仍受
`--raw-jsonl-max-bytes` 限制（默认 1 MiB），不能用它替代紧凑结果文件。当前执行器
按 Pi `0.80.6` 的 JSONL 工具调用事件格式验证；2026-10-09 另在 Pi `1.0.0` 上跑通 smoke 与 README 用例；这表示已验证版本，不声明为
最低兼容版本。已保存的
v0.2.1 基线使用同一个 Sonnet 4.6 模型的两个独立上下文完成生成与评审，因此
可证明那一版本的上下文隔离，但不能宣称跨模型复核，也不能作为当前未验收
改动的发布证据。

重要用例可以显式设置 `max_revisions: 1`。首轮评审正常完成，且事实合同返回
`FAIL` / `UNCERTAIN`，或编辑检查返回有具体定位、且不只是排版类（`presentation`）
的问题时，执行器把
来源、初稿和对应反馈交给生成模型做一次完整纠正，再由新的调用核对事实与编辑
问题；评审超时或协议错误不会触发盲目重试。事实、编辑和读者反馈共享这一次
预算，编辑问题不能因事实通过而被忽略，也不被伪装成事实失败。
初稿、初审、修订稿和复审分别留档，最终候选仍写入 `candidate.md`。未声明该
字段的普通短文和路由用例保持单次生成，第二次纠正永远不会自动发生。

实验性写作检查可增加 `--focused-editorial`（默认关闭，误报校准尚未通过）：在独立上下文中只提供请求与成稿，
检查结构、信息贡献和语言，先提出候选问题，再由掌握来源和任务合同的评审
确认或驳回；只有确认的问题进入修订，编辑建议不能直接当作缺陷。来源评审不得新增编辑问题，
确认项须保留候选的类型与原文引句；越界返回 `ERROR`，不静默丢弃，也不触发修订。
候选为空不影响新的事实错误通过事实合同或阻断项报告。独立编辑步骤使用
judge model，不加载 Skill 或工具；JSON 与原文引句仍需通过校验。修订后重做
独立编辑检查与来源核对。它与原有反馈共享一次修订预算，不自动增加修订次数。
启用该选项后，仍有 `NEEDS_EDIT` 时命令返回非零，即使事实合同为 PASS；
结果中的事实状态与 `editorial_status` 分开保留。该选项不适用于校准或 `--rejudge`。
这是模型编辑检查，不替代真人验收，也不能保证发现所有问题。

生成与修订回执中的 `skill_read_trace` 记录 Pi 的 read 调用、Skill 内相对路径、
读取范围（如有）和成功／失败／未确认状态；外部路径脱敏，不保存工具正文或
思考内容。它用于区分路径已传入与实际读取，不证明读取完整或规则已经执行。

如果生成已经完成、只有评审协议或评审服务失败，可显式使用
`--rejudge <case-artifact-dir>` 重新评审现有候选稿。重新评审写入新的
`rejudge-N/` 目录并保留原失败记录；评测器不会自动重试或覆盖历史。

`evals/baselines/` 中的旧版本证据只追加、不改写。源码验证检查这些历史文件
的内部完整性；只有 `release_check.py` 会要求当前版本存在与当前 Skill、用例
逐项匹配的 PASS 证据。v3 用例由程序冻结多来源文本摘要和行号；阶段执行成功、
事实通过与读者理解通过分别记录，最终状态由程序汇总。


## 写作质量对照

事实通过不等于语言精炼。`docs/pyramid-writing-change.md` 记录金字塔分组、信息贡献编辑与匿名成稿比较方法。开发时可对冻结 Skill 运行一次首稿样本：

```bash
python3 scripts/eval_writing_sample.py \
  --skill skills/write-craft \
  --cases evals/pyramid-heldout.json \
  --output-dir .artifacts/write-craft-evals/writing-sample \
  --model deepseek/deepseek-flash \
  --judge-model deepseek/deepseek-flash
```

修改前后的 Skill 分别使用同一批材料、同一模型与参数，并写入不同新目录。脚本禁止修订和覆盖样本，事实检查与写作比较、真人验收分别记录。六份合成材料在首次使用后即为已见集；后续调优不能继续把它们当作未见验收材料，也不能用合成稿替代真实脱敏文档的真人阅读。

`python3 scripts/style_metrics.py 稿件.md ...` 统计“不是、不代表、不能证明”等对照否定句的数量与密度，并列出跨段重复出现的长片段。它只帮助定位防御式写法和重复边界，供人工阅读核对，不作为通过或失败的判据。
