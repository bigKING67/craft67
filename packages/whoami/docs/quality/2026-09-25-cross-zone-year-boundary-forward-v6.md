# v6 跨年时区前向验收

日期：2026-09-25。结论：新增双 case 固定样例 `semantic-forward-010`，验证同一绝对时刻落入不同本地年份时，宿主必须先按用户指定的 IANA 时区冻结本地日期，再解析“明年”；出生资料时区、UTC 日期与运行机器日期都不能替代报告时区。

## 同一时刻的两个本地日期

任务与量表在 context、报告与答复之前固定。绝对时刻为 `2026-12-31T16:30:00Z`。锁定 Temporal 实现重算得到：

- `Asia/Shanghai`：`2027-01-01T00:30:00+08:00`，本地日期为 2027-01-01，明年=2028；
- `America/Los_Angeles`：`2026-12-31T08:30:00-08:00`，本地日期为 2026-12-31，明年=2027。

两份 context 使用[同一 input](../../examples/acceptance/semantic-forward-010/input.json) 重算。[上海 context](../../examples/acceptance/semantic-forward-010/context-shanghai-2027-2028.json) 的 years 为 `[2027, 2028]`、evidenceId 为 `f4e42e0ae312632d500c13c9ded77b7b1baa526c0e6141af17e94904e6cdd054`；[洛杉矶 context](../../examples/acceptance/semantic-forward-010/context-los-angeles-2026-2027.json) 的 years 为 `[2026, 2027]`、evidenceId 为 `2fca890776d377112b8dc47edddb526a4f9e1bd8afa687bfbf719362de949f28`。两者 chartId 均为 `a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789`。

## 报告与答复边界

[上海报告](../../examples/acceptance/semantic-forward-010/report-shanghai.json) 冻结 `2027-01-01 / Asia/Shanghai`，事业段明年=2028，timingChain.years 为 `[2027, 2028]`；[洛杉矶报告](../../examples/acceptance/semantic-forward-010/report-los-angeles.json) 冻结 `2026-12-31 / America/Los_Angeles`，事业段明年=2027，timingChain.years 为 `[2026, 2027]`。两份报告均只绑定对应 evidenceId，并由当前构建版 `report-check` 重算为 valid。

[上海答复](../../examples/acceptance/semantic-forward-010/response-shanghai.md) 为 452 个、[洛杉矶答复](../../examples/acceptance/semantic-forward-010/response-los-angeles.md) 为 450 个非空白 Unicode 字符。它们分别说明时区换算、明年含义、证据年份和事业边界；两份 [上海 sidecar](../../examples/acceptance/semantic-forward-010/response-claims-shanghai.json) 与[洛杉矶 sidecar](../../examples/acceptance/semantic-forward-010/response-claims-los-angeles.json)逐段绑定 timing、career 与 advice claim。报告 schema 不保存绝对时刻，因此答复明确说明 `report-check` 只校验已冻结日期及证据绑定，不独立认证宿主的时区换算。

## 复核结果

- 两个 case 的 responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=13；最终 status=partial。
- 固定回归已加入 `tests/acceptance.test.ts`，直接用 Temporal 重算两个本地日期，并核对 context、report、timingChain、相对年份和答复长度；`npm run check` 为 143/143 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `e6cd9299948e06f89a0c3bf5f918efe56aa4169c211e83ee813489a9edb620aa`；任务 `ab8453d2ba70eda5aa44e2a1eae8f7591a04f45dcc83af0d77be24c3d95c975d`；量表 `3c15600cf27f84299d009b37180c77a3623d0830dd196572e008387bba84b26f`；上海报告 `c32749a7554ea34ef3fe567d0dbfcdba17b3bad8b651b0fc8ad23fe640238135`；洛杉矶报告 `0ae3750dd73ee964c11cf33cdf281107d4e21e875e8b2968e3cac32563ae224c`；上海答复 `f863a759e5224adf180d39cce5fe25e19232ece1e95b97695bf2ec71e7b450de`；洛杉矶答复 `0744c08685f95989bf73ddc19cef27da4279e069e4f879707d9c91f1fe1f67c5`；manifest `340972fd313571e9c1c17b635b16e295de1ce26ba43add25bb12d23385f20205`。

这项 PASS 只说明固定样例遵守时区换算、相对年份、证据绑定和未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
