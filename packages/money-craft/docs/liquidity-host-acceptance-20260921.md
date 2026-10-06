# 流动性语义真实宿主验收

结论：PASS_BOUNDED_AFTER_ROUTING_CORRECTION。四类合成问题各有一份通过的真实 Codex 宿主回答；共运行六次，首轮只有两例同时满足回答与规则读取要求，不能写成一次全过。

宿主为 codex-cli 0.155.1；复用 scripts/run_skill_task.py，以 explicit-source 方式读取仓库 Skill。在临时工作目录、read-only sandbox、ephemeral 会话下运行，每例上限300秒；六次均正常退出且未超时。并行启动了隔离测试进程，没有使用 collaboration 子代理。未修改全局安装或配置。

| 案例 | 首轮 | 修复后/采用结果 |
|---|---|---|
| 合并与母公司口径 | 回答及规则读取通过 | 集团差额300不能当作母公司分红，未知资金不设零 |
| 流动可转债 | 算130正确，但未读research-semantic-review | 重跑读到新规则，纳入一次并区分账面额和到期合同现金 |
| 重复扣受限现金 | 回答及规则读取通过 | 现金等价物80不再扣已排除20，不能把60称保守值 |
| 产品到期与解押 | 答案有边界，但未读research-semantic-review | 重跑明确139—158只是分桶敏感性，不是可用资金上下限 |

修复仅在 financial-data-and-evidence.md 增加局部经济解释问题到语义复核的明确入口，并保留纯转录/单位换算无需额外加载的例外。没有修改模型答案、计算核心或原失败回执。其余既有dirty工作保持。

最终采用四例：12项人工标准通过、8项计算通过、四例路由READY；结构化机器审计均通过。语义判断由主代理审阅实际回答和工具轨迹完成，不是机器自动评分或独立审查。37项定向单元测试、Skill quick_validate和git diff --check通过。

prompt只含任务及合成事实，没有criteria或正反例答案；实际读取轨迹未发现读取验收答案。这里的隔离是prompt排除与轨迹复核，不是文件系统禁止读取仓库答案；样本是已知问题衍生的四个自设题，不代表留出集泛化能力。

首轮两例通过使用修复前源码，另外两例在增加入口后重跑；哈希分别保留，不宣称四例均在同一源码快照重跑。语义规则正文在六次运行期间未改变。

证据：acceptance/liquidity-semantics/host-20260921.json绑定每次answer.md、events.jsonl、host.json、machine-audit.json、prompt.txt及源码哈希。原始宿主证据保留在local/skill-evals/20260921-liquidity-host/。每个案例继续用独立output-dir；例如重放可转债案例：

```sh
local/validation/disclosure-candidate/bin/python scripts/run_skill_task.py \
  --case liquidity-current-convertible \
  --case-file local/skill-evals/20260921-liquidity-host/run-cases.json \
  --output-dir local/skill-evals/liquidity-new-run \
  --timeout 300 --invocation explicit-source
```

仓库原任务文件保留READY_SYNTHETIC_NOT_EXECUTED的历史状态，本轮本地副本仅将status规范化为既有runner接受的READY_SYNTHETIC，问题、事实和criteria未修改；当前执行状态以上述新回执为准。

下一边界是全局安装与implicit自然发现；本轮均未执行。真实美的研究中的信息缺口仍为PARTIAL，不能由合成宿主案例通过推定已解决。
