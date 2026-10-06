# Design 认证证据核验与执行清单

核验日期：2026-10-06。源码快照：`6d0676a8bf683dca42b327e27f22cad690797516`。
本轮范围是性能核验、只读门禁检查和评测入口 dry-run；用户明确选择暂不启动真实模型评测。

## 已核验的状态

| 项目 | 结果 | 依据与边界 |
| --- | --- | --- |
| Codex / Pi 当前宿主证据 | FAIL | 三个任务的现有 score 合同摘要过期，旧 `skill_source_commit` 不在当前仓库祖先历史中；不能改写摘要或提交号使旧证据通过 |
| 四组 comparative 证据 | FAIL | 原始 run 的 comparative 合同摘要过期，旧 source commit 不在当前仓库祖先历史中 |
| 本机安装来源与一致性 | PASS | 原 `install_provenance` 门禁通过；只读验证，未重新安装，也不等于模型真实加载已验收 |
| 上游 live 审查门禁 | FAIL | 原 `upstream_remote_review` 返回 taste-skill、impeccable、emilkowalski-skills、jakubkrehel-skills 为 unreviewed；尚未完成逐范围审查，不将此结果直接解释为必须更新全部 pin |
| 宿主执行入口 | PASS / dry-run | 3 个任务 × Codex/Pi 共 6 个组合成功；工作树行为摘要及 Skill 投影与 HEAD 中的 Git 内容一致；未调用模型 |
| 对照执行入口 | PASS / dry-run | 4 个 case × 3 个 variant 的隔离装配成功；未调用模型、未产生新的 observed/PASS 记录 |
| native 最终认证输入 | 尚不具备 | 根 native 工作流仍只手动触发；既有 main 手动运行不满足 Design 标签 push 的事件合同 |
| certified_100 | 尚不具备 | 还需要 Cursor/Claude、物理设备证据与根 physical-device 工作流，不在本轮执行范围 |

## 性能结果

**PASS：20 项 full 指标均未触发原性能回归阈值。** [GitHub run 37488212072](https://github.com/bigKING67/craft67/actions/runs/37488212072) 成功；附件 `performance-full-37488212072` 下载后通过原 `result_errors` 校验，源码 SHA 为本页开头的 `6d0676a`，`source_dirty=false`。临时下载目录已自动清理，原附件按工作流保留 90 天。

使用原 `compare_results` 对比已提交的 `packages/design-craft/benchmarks/baselines/v0.7.0-linux-x86_64-python3.13.json`：`ok=true`，errors/warnings 均为空，20 个 comparison 的 `regressed` 均为 false。baseline 没有改动。

| 代表性指标 | baseline p95 | 本次 p95 |
| --- | --- | --- |
| portable_validation | 10008.263 ms | 8722.036 ms |
| release_bundle_build | 973.793 ms | 794.640 ms |
| tree_scan_100000 | 5252.545 ms | 3630.162 ms |

两次均为 Linux x86_64、Ubuntu 24.04 镜像系列和 Python 3.13.15，满足现有比较合同。baseline 的镜像版本为 `20260823.283.1`、Node 为 `24.19.0`；本次为 `20260927.320.1`、Node `24.21.0`。因此只认定通过现有回归合同，不把数值下降归因于代码优化或承诺稳定加速。

本次是 main 上的 capture 运行，不能替代 final 所需的 tag-bound operational-candidate benchmark observation。结果绑定 `6d0676a`，不是后续提交的当前 SHA 证明；在最终版本提交确定后仍需采集对应认证证据。

## 真实评测执行顺序

所有命令从 `packages/design-craft` 执行。模型、推理档位、费用预算尚未指定；下面是待执行清单，不是已经执行的记录。

1. **先处理上游审查。** 对四个 unreviewed 范围核对来源和差异，作出有依据的吸收、保留或暂缓结论。若修改 Skill、评测合同或行为域，先完成源码门禁和 scoped commit，再采集新证据；不自动推进 pin 或伪造已审查状态。
2. **确定干净的待验收源码提交。** 确认 `git status --short`、包版本、Git 中的行为域和 Skill 投影一致。现有旧评测文件需要按原 history 合同归档并独立验证；本轮未移动或覆盖它们。运行器默认拒绝覆盖已有输出，不直接加 `--force` 绕过归档。
3. **重采宿主证据。** 三个任务分别在 Codex、Pi 上执行，共 6 次调用。每个输出按对应 scorecard 逐条评审，使用原 recorder 绑定真实 run；完整验证成功后才能标记 observed。
4. **重采对照与盲评。** 四个 case 分别执行 no-skill、focused upstream、Design 三个变体，共 12 次 Pi 调用；每组随后生成盲包，由独立 Codex/Cursor/Claude judge 调用 1 次，共 4 次。judge 必须独立于 Pi 执行端。按原 record/validate 接纳结果，不能保证 Design 必然胜出；不通过应修复产品或缩小声明，不能改分数。
5. **合并并检查完整证据。** 当前 observed host、comparative、上游、安装、性能与 native 均需通过各自门禁。至少 22 次模型调用只计一次成功执行，不含失败重试、人工逐条评分或 certified_100 的额外宿主。
6. **最后处理标签与认证。** 在源码和证据可验收后，再确认 annotated `design-craft/v<版本>` 标签与 native push 流程的启用；同一标签目标上执行 native、operational candidate full benchmark，然后在指向同一提交的 main 上运行 certification。创建标签和正式 Release 不属于本轮授权，正式发布仍单独处理。

### 宿主任务与命令

任务：`same-prompt-dashboard-review`、`same-prompt-motion-review`、`same-prompt-native-adaptive-review`。

```sh
python3 scripts/design_craft_cross_agent_run.py \
  --task-dir "evals/cross-agent/<task>" \
  --host <codex-or-pi> \
  --model <confirmed-host-model> \
  --reasoning-profile <confirmed-profile> \
  --skill-root skills/design-craft
```

接着按 [原宿主证据说明](../packages/design-craft/evals/cross-agent/README.md) 准备 criteria 并调用 `design_craft_cross_agent_record.py`。不能把 dry-run 当成真实 output 或 score。

### 对照任务与命令

Case：`emil-motion-ablation`、`emil-motion-planning-ablation`、`taste-visual-critique-ablation`、`impeccable-production-ablation`。

```sh
python3 scripts/design_craft_comparative_run.py \
  --case-dir "evals/comparative/<case>" \
  --model <confirmed-pi-model> --thinking <confirmed-profile>
python3 scripts/design_craft_comparative_blind.py \
  --case-dir "evals/comparative/<case>" --seed <release-specific-seed>
python3 scripts/design_craft_comparative_judge.py \
  --case-dir "evals/comparative/<case>" \
  --host <codex-or-cursor-or-claude> \
  --model <confirmed-judge-model> --reasoning-profile <confirmed-profile>
python3 scripts/design_craft_comparative_record.py \
  --case-dir "evals/comparative/<case>"
make comparative-observed-check
```

完整验收以 [原对照评测合同](../packages/design-craft/evals/comparative/README.md) 和 [发布迁移说明](release-migration.md) 为准。这里没有放宽原门禁，也没有把旧版本证据转换成新仓库的认证结果。
