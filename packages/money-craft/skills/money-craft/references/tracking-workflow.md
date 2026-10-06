# 投资论文跟踪工作流

公司跟踪层位于该公司所有日期研究目录的同级，而不是某一次研究日期内部：

```text
<money-root>/
└── <ticker>-<company>/
    ├── <YYYY-MM-DD>/revisions/rNNNN/  # 某次正式研究档案
    └── tracking/
        ├── current.json               # 可变指针
        ├── .working/<run-id>/         # 单次可编辑跟踪工作区
        └── revisions/tNNNN/           # 只读、哈希绑定的论文跟踪历史
```

## 创建工作区

第一次建立跟踪层时显式绑定一份已通过审计的旧论文：

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" track init \
  --tracking-root <company-dir>/tracking \
  --previous <audited-thesis.md> \
  --source-revision <formal-revision-dir-or-REVISION.json> \
  --as-of <YYYY-MM-DD> --json
```

后续更新可以省略 `--previous`；命令从 `tracking/current.json` 解析上一版论文。`--source-revision` 是可选的正式研究档案绑定，不会复制原始证据。

`track init` 离线且不调用模型。它生成不可改写的 `previous-thesis.md`、`update-plan.json`、`run-state.json`，以及需要研究者或 Agent 根据新证据完成的 `thesis.md`、`card.md`、`state.json`。未完成的 `{{...}}` 占位符会阻断准出。

## 完成与封存

在工作区内完成三份可编辑文件后运行：

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" track check \
  --workspace <track-init-returned-workspace> --json
```

`track check` 会验证：

1. 旧论文和更新计划仍与初始化回执一致。
2. 新论文同时通过 report 和 financial audit。
3. 证券身份、时间、数据截止时间和历史更新记录满足 append-only 合同。
4. `state.json` 的假设、红线和健康度与论文逐项一致。
5. `card.md`、`state.json` 不再有占位符。

全部通过后，命令在锁内原子创建下一版 `revisions/tNNNN/`，写入 `TRACKING.json` 和 `SHA256SUMS`，将 revision 文件与目录改为只读，再原子切换 `current.json`。只有成功切换指针后，才清理工具自己创建的 `.working/<run-id>/`。

封存锁内首先验证已有历史；已有版本或 current 存在且验证失败时，返回 `invalid_history`，保留工作区及历史，不分配新版本。封存锁内还会核对工作区绑定的旧论文是否仍与 current 论文相同。其他工作区已更新论文时，旧基线候选返回 `stale_previous`，保留工作区和已封存历史；应从最新 current 重新初始化、复核并迁移仍有效的研究内容，不能直接重复提交旧候选。

封存失败不一定表示 current 尚未更新：原子替换后的目录同步也可能报错。失败时保留工作区；若 current 已指向新版本（或无法安全判定指针），不删除该版本。先执行 `track verify` / `track status` 核对现场；已提交的旧工作区重试会受旧基线检查约束，应从 current 初始化后续更新。指针更新前失败且可确认未被引用的本次版本会清理，工作区可修复后重试。这是进程内异常处理，不是断电或强制终止后的自动恢复。


假设与红线已全部核实时，健康度沿用损伤扣分公式：

```text
max(1, 10 - BROKEN*3 - DAMAGED*2 - WEAKENED*1 - TRIGGERED_RED_LINE*5)
```

有任一 `UNVERIFIED` 时，`health.score` 为 `null`，不能填 10 或 0。已知 `BROKEN`/`TRIGGERED`、`DAMAGED`、`WEAKENED` 按严重度保留；没有已知损伤时才显示 `UNVERIFIED`。只有 `WATCH` 而无已知损伤时显示 `WATCH`，不能显示 `SUPPORTED`。分数只统计已定义的损伤扣分，不能脱离状态解释；WATCH 不新增主观惩罚权重。

新工作区、revision 和 current 指针使用 v2 合同；相应 schema 位于 `schemas/tracking-{state,revision,current}.v2.schema.json`。旧 v1 封存档案继续按历史算法校验，不改写历史字节；不符合新期限规则的历史元数据仅令当前时效为 UNKNOWN。旧工作区在准出前需要将 state 更新为 v2 并重算健康度。该分数与 diff signal 只表示研究复核优先级，不是买卖信号。

## 读取与离线验证

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" track status \
  --tracking-root <company-dir>/tracking --json
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" track verify \
  --tracking-root <company-dir>/tracking --json
```

`verify` 重算文件哈希、审计结果、状态映射和 current 指针，并默认要求所有 `tNNNN` 文件与目录不可写。历史编号必须从 `t0001` 连续递增；从第二版起，每版声明的前驱论文哈希必须等于前一版论文的实际哈希。缺版或断链判为无效，不自动补写或修复历史；首版允许使用外部初始论文。这些检查只证明内部一致性，不能识别整套历史及 current 一并重写后的自洽替代档案。`status` 在此基础上返回 v2 `assessment`；`current` 仍是历史指针，不是当前投资判断。两者都不联网、不读取账户、不执行交易。两者在同一 tracking 锁内读取目录、current、校验结果和状态，遇到正在封存的更新会等待，避免把提交中的中间状态误判为损坏。验证不改写研究档案，但需要能打开运行锁 `.tracking.lock`（缺失时会创建）；当前使用排他锁，多个读取也会串行。此约束只覆盖遵循同一锁协议的进程，不覆盖外部直接改写文件。

`assessment.integrity` 表示档案验证结果；`status` 和 `score` 表示按新规则计算的当前可用判断。验证失败时为 `INVALID`、`UNVERIFIED` 和 null，不信任指针上的分数。没有 revision 时为 `UNVERIFIED`，查询成功不代表论文有效。

可在 `state.json` 的 `next_mandatory_review` 中填写由研究计划确定的 `due_date: YYYY-MM-DD`，不得早于论文 `as_of`。`status` 按当前 UTC 日期评估：截止日当天仍在复核窗口内，之后为 `STALE`；没有期限为 `UNKNOWN`，论文日期尚未到达为 `NOT_YET_VALID`。这三种情况都不输出当前数值评分，历史 `SUPPORTED` 降为 `UNVERIFIED`，已知损伤和 WATCH 仍保留。复核窗口内也只证明未超过登记的期限，不证明正式来源仍然最新或论点正确；重大事件触发的提前复核仍须执行。

## 触发路由

- 价格越过已有估值边界，但没有新经营证据：只刷新估值，不自动改写核心论文。
- 新定期报告：先做 earnings review，再执行 `track init -> 填写 -> track check`。
- 任一红线变为 `TRIGGERED`、核心假设变为 `BROKEN`、关键来源冲突改变估值或结论，或发生重大并购、减值、融资、治理、资本配置事件：升级为完整公司研究。

Provider 原始响应、正式报告和浏览器抓取仍属于私有证据层，不进入 tracking revision；revision 只保存论文、跟踪卡、状态、差异、审计和哈希清单。

### 强制终止后的处理边界

进程被强制终止后，先运行 `track verify` 和 `track status`，不要根据上次命令是否返回成功来推断封存结果。版本已生成但 current 尚未更新时，档案可能无效；`track check` 会以 `invalid_history` 拒绝继续扩展。current 已更新且档案验证通过时，旧候选重试由 `stale_previous` 拒绝，应从 current 初始化后续更新。

遇到无效档案，保留工作区、版本和残留临时文件，先核对验证错误及最后一个可信状态；不要直接编辑 current 或重算校验和来消除错误。当前没有自动修复或自动提升孤立版本的命令，修改档案需明确恢复目标、保留原始副本后单独处理。现有验收覆盖 current 替换前后两个 SIGKILL 窗口，不覆盖全部崩溃时点、隐藏 staging 的自动清理或真实断电耐久性。

### 论文变更识别

论文的合同章节必须唯一，包括结论、事实与证据、核心假设、估值与假设、风险与反方证据、证伪条件、更新记录和来源索引；重复章节会被拒绝，避免只解析首段而遗漏后续假设或证据。事实与证据正文变化、来源定义的新增/删除/替换均会进入 `CHANGED` 判断；已知受损假设或触发红线仍优先给出更强的复核提示。该信号仅指结构化变更，不判断文字变更是否具有投资重要性，也不自动重写旧封存档案。
