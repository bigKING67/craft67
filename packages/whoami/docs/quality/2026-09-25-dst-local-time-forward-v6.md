# v6 DST 当地时刻前向验收

日期：2026-09-25。结论：报告时间门禁在日期、钟点和 IANA 时区格式通过后，继续检查当地民用时刻是否真实存在且唯一。纽约 `2027-03-14 02:30` 被识别为春季跳时缺口，任何 `earlier/later` 都不能将它顺延；`2026-11-01 01:30` 被识别为秋季回拨重复小时，必须由现实记录选择 earlier 或 later，不能按命理解读结果倒选。

## 同一分类器

`inspectLocalDateTime` 用 Temporal 分别求同一 PlainDateTime 在地区时区中的 earlier 与 later 结果。两者都不能还原原钟表时间时，状态为 nonexistent；两者都能还原但对应绝对时刻不同，状态为 ambiguous；两者相同才是 unique。出生时间和报告文字共用这一分类器，避免一层把缺失时间写成歧义、另一层又把它自动顺延。

报告中的 `YYYY-MM-DD HH:mm[:ss] Area/Location` 会先走这一步：缺失时间返回 `NONEXISTENT_LOCAL_TIME`，重复时间没有分支时返回 `AMBIGUOUS_LOCAL_TIME`，无法识别的地区时区返回 `INVALID_TIMEZONE`。重复时间追加 `earlier` 或 `later` 后，只是完成绝对时刻绑定，仍会继续进入日级、小时级 evidence 门禁。出生资料原先在 `dstDisambiguation=reject` 时会把跳时缺口归入笼统歧义，本轮也修正为稳定的 `NONEXISTENT_LOCAL_TIME`。

## 三阶段产物

前两 case 使用[同一 input](../../examples/acceptance/semantic-forward-018/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-018/context.json)。[缺失小时答复](../../examples/acceptance/semantic-forward-018/response-gap.md)为 358 个非空白 Unicode 字符，拒绝顺延或 disambiguation；[重复小时答复](../../examples/acceptance/semantic-forward-018/response-fold.md)为 336 个非空白字符，区分 UTC−04:00 earlier 与 UTC−05:00 later，要求依据现实记录选择。两者都不绑定 report，也不判断行动或签约结果。

第三 case 假定用户撤回两个 DST 问题时点，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-018/report.json)绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-018/response-annual.md)为 390 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-018/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前两 case：responseSafety=pass，未提供 report 的三项检查均为 not-applicable。
- 第三 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=14；最终 status=partial。
- 报告 DST 边界与固定前向回归各新增 1 项；既有出生 DST 缺失回归加强为精确错误码；`npm run check` 为 159/159 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `0d6375f13c148bc1162f9bca100ca13f6237b6d52a748a3fe3b3d1a36cba842c`；任务 `b6e1e4d8551809ecf430dc1519566e181fc14dbd7e2756664dd39e3c91645c5b`；量表 `73a78312378e883ee191a81343cc8c2fd274c6be2e94091044bdc4d2585176d8`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；缺失小时答复 `60648c66181b3ed78043364b1c6686fd5602c011653d6cafc46654d642416793`；重复小时答复 `f865367313c9d0deef5cc0fbddaefe57b2b794c16c3cca5ba04a65b9ee08c878`；年度答复 `ee8856de6a49a31f9c8afeb354d9b1cae349c74cd80bc375c51826be77b4c244`；sidecar `0ad7ce004431650add337eed4f4b3a99c7cb5ad937990311cc2c5ab0ce62b0dc`；manifest `acb5a8b8e44011a534e124d1d9554ef8213142562484e6fa84da2086ac5435c7`。

这项 PASS 只说明固定样例遵守 IANA/DST 当地时刻分类、分支选择、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
