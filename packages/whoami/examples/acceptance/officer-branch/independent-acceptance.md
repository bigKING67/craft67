# whoami 局部规则追问：运行记录与验收边界

运行目录：`<repo-root>`

唯一写域：`/tmp/whoami-rule-reasoning-20260923`

## 实际命令与退出码

| 命令 | 退出码 | 输出 |
|---|---:|---|
| `node dist/cli.js --help` | 0 | stdout（已在会话读取） |
| `node dist/cli.js validate --input /tmp/whoami-rule-reasoning-20260923/input-0200.json` | 0 | `validate-0200.json` |
| `node dist/cli.js validate --input /tmp/whoami-rule-reasoning-20260923/input-0400.json` | 0 | `validate-0400.json` |
| `node dist/cli.js context --input /tmp/whoami-rule-reasoning-20260923/input-0200.json --years 2026` | 0 | `context-0200.json` |
| `node dist/cli.js rule-review --input /tmp/whoami-rule-reasoning-20260923/input-0200.json --years 2026` | 0 | `rule-review-0200.md` |
| `node dist/cli.js context --input /tmp/whoami-rule-reasoning-20260923/input-0400.json --years 2026` | 0 | `context-0400.json` |
| `node dist/cli.js rule-review --input /tmp/whoami-rule-reasoning-20260923/input-0400.json --years 2026` | 0 | `rule-review-0400.md` |

预检查中曾将 `years` 放进 JSON 输入；`validate` 返回 1，错误为 `UNKNOWN_FIELD`。已将年份移至 CLI 的 `--years 2026` 参数后重新验证，以上记录是最终实际输入与结果。

## 输入与计算事实

- 02:00 合成输入：`calendar=solar`、`date=2003-08-11`、`time=02:00`、`gender=female`、`place=合成东经120度`、`longitude=120`、`timeZone=Asia/Shanghai`、`timeBasis=civil`；候选 `C1-a6e42e2d`，四柱癸未、庚申、丙辰、己丑。
- 04:00 独立合成输入：同上，仅 `time=04:00`；候选 `C1-84740a29`，四柱癸未、庚申、丙辰、庚寅。
- 两份 `context` 均为 `status=ready`、候选数 1。02:00 的财旺生官分支是 `blocked`，显干伤官反例为时干己；04:00 的该分支是 `pending`，不是 `established` 或成格结论。

## 事实来源 ID

| 输入 | chartId | evidenceId | 事实 ID | 规则 ID |
|---|---|---|---|---|
| 02:00 | `4efb131e36009535f9c0fb44b8456cb57eb3fb96f9792fa02f1dcfb481cf4691` | `eabbceec91079110175714454fa75a6fc6273a98ef5d21ebc66b5d7710efcca0` | `C1-a6e42e2d.bazi.year`、`C1-a6e42e2d.bazi.month`、`C1-a6e42e2d.bazi.day`、`C1-a6e42e2d.bazi.hour`、`C1-a6e42e2d.bazi.monthExposure`、`C1-a6e42e2d.bazi.wealthReview`、`C1-a6e42e2d.bazi.rootDetails` | `C1-a6e42e2d.R-bazi-structure`、`C1-a6e42e2d.R-bazi-wealth-review`、`C1-a6e42e2d.R-bazi-month-exposure`、`C1-a6e42e2d.R-bazi-root-review` |
| 04:00 | `5eb73032b617393121bf1ab763ebdcb40566a5cc3ece3853f7f41553740f1f5e` | `f47a0687bdaeeb4560d82341e1e24285b85e19b9b570f2d7e894ce4b6ab49d5f` | `C1-84740a29.bazi.year`、`C1-84740a29.bazi.month`、`C1-84740a29.bazi.day`、`C1-84740a29.bazi.hour`、`C1-84740a29.bazi.monthExposure`、`C1-84740a29.bazi.wealthReview`、`C1-84740a29.bazi.rootDetails` | `C1-84740a29.R-bazi-structure`、`C1-84740a29.R-bazi-wealth-review`、`C1-84740a29.R-bazi-month-exposure`、`C1-84740a29.R-bazi-root-review` |

规则 ID 的来源是 `references/analysis.md`：财格候选复核、月令透干复核、通根复核和八字的分层论证。`rule-review` 另列传统条件原文转录来源，但本次按要求未联网核验。

## 未验证项与边界

- 未验证真实出生时间；两份资料均是合成输入，04:00 不是可按吉凶选择的真实候选。
- 未完成旺衰、月令司权、财官实际作用、合化、制化、救应有效性、藏干影响或整体成格判断；CLI 对这两盘的 `wealthReview.judgment` 都是 `unresolved`。
- 未联网，也未读取 `src`、`tests`、`examples`、`docs/quality` 或其他代理产物；未作完整人生报告、紫微结论、现实预测或传统来源的影印校勘。
- 未运行 `report-template`、`report-check` 或 `render`，因为交付是三项局部追问而不是报告产物。
