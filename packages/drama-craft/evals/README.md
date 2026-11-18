# 评估与证据

目的只有一个：把 SKILL 里已经写下的可验收条款变成**能跑的检查**，让"结构合规"和"投放有效"分开报告。

- 机器检查：`scripts/check_eval.py` 校验交付物的结构契约（列、时间码、字段、单变量矩阵、机制数字）。
- 证据计算：`scripts/evidence.py` 从台账算出每个原型的 A/B/C 等级，并拒绝手写的等级漂移。

两者都不评价创意、不评价可拍性、不证明投放效果。

## 目录

| 路径 | 职责 |
| --- | --- |
| `cases/*.md` | 固定 brief。frontmatter 声明该用例要求的交付形态，正文只写输入与要求 |
| `baselines/*.md` | 已通过门禁的样例输出，文件名与用例同名 |
| `rubric.md` | 机器项与人工项的完整清单 |
| `ledger.json` | 真实投放台账：单变量轮次与同结构样本数 |
| `levels.json` | 声明等级快照；必须与台账计算结果一致 |

## 运行

```sh
python3 scripts/check_eval.py --all          # 校验所有已有基线
python3 scripts/check_eval.py --case evals/cases/02-dropoff-diagnosis.md \
                              --output evals/baselines/02-dropoff-diagnosis.md
python3 scripts/evidence.py --check          # 台账、等级与 README 口径一致性
```

三个命令都在包检查门禁里，与 `scripts/check.py`、单元测试一起跑。

## 覆盖现状

- 用例 5 个：三个方向、掉点诊断、成片复盘、钩子候选、批量原型库。
- 已有基线 2 个（`02-dropoff-diagnosis`、`04-hook-candidates`），覆盖"改稿 + 分镜"和"只要候选"两种形态；其余 3 个用例目前没有基线，`--all` 会把它们列在 `uncovered` 里。
- 补基线是新增用例的最低要求：没有基线就等于没有验证过这门检查能不能真的拦住坏交付。

## 新增用例

在 `cases/` 加一个 md，frontmatter 支持：

| 字段 | 含义 |
| --- | --- |
| `case` | 用例 id，与文件名一致 |
| `title` | 一句话说明 |
| `min_directions` | 要求的最少方向数（按 H2 含"方向"计数） |
| `require_sections` | 必须出现的节或内容关键字，逗号分隔 |
| `require_shot_tables` | 是否必须有分镜表 |
| `forbid_shot_tables` | 是否禁止出现分镜表（例如只要钩子候选） |
| `require_frozen_invariants` | 是否必须写冻结不变量 |

再放一份 `baselines/<case>.md`，跑 `--all` 通过即可。

## 台账与等级升级

`ledger.json` 两张表：

- `rounds`：`prototype`、`round`、`variable`（只写一个）、`samples`、`metrics`、`conclusion`(keep/drop/more)、`attribution`(hypothesis_rejected / hypothesis_supported / execution_failed)。
- `library`：`prototype`、`samples`、`window`、`reviewed`（复核日期）。

计算规则：同一原型有 ≥3 轮、每轮 ≥3 条、归属非"样本不足"、且有指标，才算 A；同结构样本 ≥5 且 90 天内复核过，算 B；否则 C。

升级顺序固定：先补台账 → 跑 `evidence.py --check` 看计算等级 → 改 `levels.json` → 同步 README 与 CHANGELOG。反向也成立：声明高于台账能支撑的等级，门禁直接失败。

## 边界

- 基线是本地自测产物，不是模型行为认证，也不是投放结论。
- `worked-example.md` 是给人看的范例；`baselines/` 是给门禁看的产物，两者不要互相替代。
- 真实效果仍要按 `skills/drama-craft/references/iteration-loop.md` 的口径自己积累。
