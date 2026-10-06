# v6 多年范围闭区间前向验收

日期：2026-09-25。结论：新增两道核心失败封闭规则与三 case 固定样例 `semantic-forward-014`。“未来三年、三年内、接下来五年、这几年、长期会怎样”等表达必须先改写为升序的年度闭区间；明确区间后，任一年缺少 evidence 都会继续停下，不能用已有年份外推。

## 两道门禁

第一道门禁覆盖相对多年数量、未定数量和带提问语境的长期表达，返回 `AMBIGUOUS_YEAR_RANGE`。宿主须先写明类似 `2027—2029 年度`的闭区间，并说明是否包含当前年。普通的“长期观察验证”“长期专业积累”不表示用户选择的时间范围，窄模式不会误伤。

第二道门禁只检查带“年/年度”标签的明确四位年份区间。起年晚于止年时返回 `AMBIGUOUS_YEAR_RANGE`；区间任一年不在同一 input 的 `evidence.years` 时返回 `TIME_RANGE_OUT_OF_SCOPE`，错误会列出具体缺年。通过后，既有正文门禁继续要求同候选 `ziwei-timing` 和 `timingChain.years` 覆盖区间全部年份。大限 `2022—2031` 这类周期标签继续作为周期事实，不要求为整个大限补算逐年 evidence。

## 三阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-014/input.json) 与 [2026—2027 baseline context](../../examples/acceptance/semantic-forward-014/context-2026-2027.json)。[范围停机答复](../../examples/acceptance/semantic-forward-014/response-range-stop.md) 为 244 个非空白 Unicode 字符，说明首尾年份与当前年包含口径未定义，不绑定 report。

第二 case 假定用户选择 2027—2029 年度事业主题，但继续使用 baseline context。[缺年答复](../../examples/acceptance/semantic-forward-014/response-missing-years.md) 为 254 个非空白字符，精确指出缺少 2028、2029，继续停下并拒绝从 2027 外推。

第三 case 使用同一 input 补算的 [2026—2029 context](../../examples/acceptance/semantic-forward-014/context-2026-2029.json)。chartId 保持，evidenceId 更新；[v6 报告](../../examples/acceptance/semantic-forward-014/report.json) 使用 `2027—2029 年度`闭区间，timingChain.years 覆盖 `[2026, 2027, 2028, 2029]`。[补算答复](../../examples/acceptance/semantic-forward-014/response-expanded.md) 为 387 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-014/response-claims.json)逐段绑定 timing、career 与 advice claim。补齐年份只关闭 evidence 缺口，现实岗位、考核、权限、组织机会、逐年作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前两 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第三 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=14；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 151/151 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `1c877153d390af35ebc79a415edf7e42dbf654c5b206243f1200ddd516c4b834`；任务 `0d625a0e696dce21fbf45fa0c4d915ee3c11cfe011de2bfcdc64a8c8ee51a93c`；量表 `63e94027a13cded4ef1f8096ed3025a1a00334a2748ab19329a894ce69b58445`；baseline context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；expanded context `30c27abde76fdee8db183e12798f6b5aa31876ffe31f68a5f800509f24939222`；报告 `78279c4ceb9e4c527feab3a8eb6b1ecf5f4a653a7348d13f403e931db32031be`；范围停机答复 `d2a1fd4668dda2b6c1d453aeac752a31c054f6510c6f363b3b50db42a6debbcf`；缺年答复 `8ec952bd9fe1515ad8b8b6104ac62f3929f6366bf96159dc3d3b8fc58724fdb4`；补算答复 `18bb2516a1d63b1c42ece24b7024d66d476380971d7feae0bfa920c77d82e435`；sidecar `06d12587aef758df9e30cadbadb2d52c2a743ab47b1b2393a0af28df52cfc06f`；manifest `8f32774b4fce1ad490dbcd8c0824b4c61954dc18a36bcc2436937dd6a825489d`。

这项 PASS 只说明固定样例遵守多年范围澄清、缺年停机、同 input 补算、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
