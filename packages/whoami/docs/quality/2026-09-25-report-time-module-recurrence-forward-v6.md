# 报告时间模块与 v6 重复日程前向验收

日期：2026-09-25。结论：报告自由文本的时间解析与失败封闭已从 `report.ts` 抽离到独立 `report-time.ts`，报告 schema、渲染与事实绑定接口保持不变；重复日程现在依次要求双侧绝对范围、IANA 地区时区和逐次 occurrence evidence，不再让“每天 09:00”一类表达绕过年度 evidence 粒度。

## 模块边界与校验顺序

抽离前后的既有报告回归为 52/52 PASS；最终 `report.ts` 为 1146 行，`report-time.ts` 为 639 行。新模块公开报告校验实际需要的 `validateReportTemporalText`、`validIsoDate` 与 `referencedRelativeYears`，集中持有日期、钟点、时区、DST、绝对时刻、区间、声明时长及年度范围规则。新增直接模块测试，使错误优先级不再只能经完整报告对象间接验证。

事件判断中的重复日程先检查绝对端点、IANA/DST/offset、区间闭合与顺序。没有双侧绝对范围返回 `RECURRENCE_RANGE_REQUIRED`；区间已闭合但没有 IANA 地区时区返回 `RECURRENCE_TIME_ZONE_REQUIRED`，固定 `Z` 或 offset 只定义 instant，不能定义跨日期的当地日程规则。范围和地区时区都明确后，仍须按当地日期展开每次 occurrence，并绑定相应日级、小时级 evidence；当前年度 context 因而返回 `UNSUPPORTED_RECURRENCE_GRANULARITY`。不用于事件判断的系统运行或纯计划说明继续允许。

## 四阶段产物

四个 case 使用[同一 input](../../examples/acceptance/semantic-forward-023/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-023/context.json)。[无范围答复](../../examples/acceptance/semantic-forward-023/response-unbounded.md)为 265 个非空白 Unicode 字符，拒绝自行补日期或无限延伸；[UTC 边界答复](../../examples/acceptance/semantic-forward-023/response-offset.md)为 304 个非空白字符，区分闭合绝对区间与缺失的地区时区；[纽约日程答复](../../examples/acceptance/semantic-forward-023/response-iana.md)为 391 个非空白字符，确认范围跨秋季 DST，并要求逐次展开 occurrence。三者都不绑定 report，也不选择联系客户的日期或时刻。

第四 case 假定用户撤回全部重复日程，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-023/report.json)绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-023/response-annual.md)为 407 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-023/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前三 case：responseSafety=pass，未提供 report 的三项检查均为 not-applicable。
- 第四 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=17；最终 status=partial。
- 时间模块直接回归新增 3 项，报告与固定前向回归各新增 1 项；`npm run check` 为 172/172 PASS，TypeScript strict 与 build PASS。
- 二十三份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 78 个现行 Markdown、389 个本地链接无缺失；不读取 private，private 与 node_modules 之外 175 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `d47ec2c7bc2751f0f36623fd624c0a7617a67d98d2aae684af328a01fe8273bb`；任务 `84689410c042a9c93b4ce6fd6d28b4d852574a7a31b842ebc115bd4a71f69704`；量表 `805e0ce155d86404062844569054f4b35c15d6c1d9d595deb8ab544aea5f3fc2`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；无范围答复 `4541c12602763c47c16fda73b5241e2765e3fb3080b8379be070ec362e8091da`；UTC 边界答复 `f6e3996b02c878c9ecffd15d6f6f18f29243ec939afb0a63aac8150b53978a3b`；纽约日程答复 `4d3798993bddad14177a85babbf6fd2321ca300e2965b46be96001881d931b90`；年度答复 `997bef1d48292d8f88c2d3eae9221f8b17e7041ef84389198c48927aa5d78e6c`；sidecar `28c79382c2f7ef391ff2c9348619f14c580713009acce9f757a903df500e0991`；manifest `8bcbe9949ffebfb1bec82ca7b4a31dee53e71318cb8e50489251e9df80b9f67b`。

这项 PASS 只说明固定样例遵守重复日程的范围、IANA 时区、DST、occurrence 粒度、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
